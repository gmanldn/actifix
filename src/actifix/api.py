"""
Actifix API Server - Flask-based REST API for frontend dashboard.

Provides endpoints for health, stats, tickets, logs, and system information.
"""

import importlib
import json
import logging
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

import yaml

try:
    from flask import Flask, jsonify, request, g
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None

try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    SocketIO = None
    emit = None


def _ensure_web_dependencies() -> bool:
    """
    Ensure Flask dependencies are installed. Auto-install if missing.

    Returns:
        True if dependencies are available, False otherwise.
    """
    global FLASK_AVAILABLE, SOCKETIO_AVAILABLE, Flask, CORS, SocketIO, emit

    if FLASK_AVAILABLE and SOCKETIO_AVAILABLE:
        return True

    print("Flask dependencies not found. Installing...")
    print("Running: pip install flask flask-cors flask-socketio")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask", "flask-cors", "flask-socketio"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Successfully installed Flask dependencies")
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        from flask_socketio import SocketIO, emit
        FLASK_AVAILABLE = True
        SOCKETIO_AVAILABLE = True
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Flask dependencies: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during installation: {e}")
        return False

from . import __version__
from .health import get_health, check_sla_breaches
from .do_af import (
    get_open_tickets,
    get_ticket_stats,
    get_completed_tickets,
    fix_highest_priority_ticket,
)
from .raise_af import (
    STRUCTURED_MESSAGE_ENFORCED,
    _ensure_structured_message,
    capture_stack_trace,
    enforce_raise_af_only,
    generate_duplicate_guard,
    record_error,
    TicketPriority,
)
from .state_paths import get_actifix_paths
from .persistence.event_repo import get_event_repository, EventFilter
from .persistence.ticket_cleanup import run_automatic_cleanup
from .persistence.cleanup_config import get_cleanup_config
from .metrics import export_prometheus_metrics
from .config import get_config, set_config, load_config
from .security.rate_limiter import RateLimitConfig, RateLimitError, get_rate_limiter
from .log_utils import log_event
from .plugins.permissions import PermissionRegistry
from .ai_client import get_ai_client, resolve_provider_selection
from .ai_context import get_ai_context_manager
from .modules.registry import (
    MODULE_STATUS_SCHEMA_VERSION,
    ModuleRegistry,
    ModuleRuntimeContext,
    _default_module_status_payload,
    _mark_module_status,
    _normalize_module_statuses,
    _read_module_status_payload,
    _write_module_status_payload,
)

# Server start time for uptime calculation
SERVER_START_TIME = time.time()
SYSTEM_OWNERS = {"runtime", "infra", "core", "persistence", "testing", "tooling"}

# Global SocketIO instance for real-time updates
_socketio_instance: Optional["SocketIO"] = None


def get_socketio() -> Optional["SocketIO"]:
    """Get the global SocketIO instance."""
    return _socketio_instance


def emit_ticket_event(event_type: str, ticket_data: dict) -> None:
    """
    Emit a ticket event to all connected WebSocket clients.

    Args:
        event_type: Type of event ('ticket_created', 'ticket_updated', 'ticket_completed', 'ticket_deleted')
        ticket_data: Ticket data to broadcast
    """
    socketio = get_socketio()
    if socketio is None:
        return
    try:
        socketio.emit(event_type, ticket_data, namespace="/tickets")
    except Exception as e:
        # WebSocket failures should be recorded but not block operations
        record_error(
            message=f"WebSocket emission failed: {e}",
            source="api.py:emit_ticket_event",
            error_type=type(e).__name__,
            priority=TicketPriority.P3,
        )
MODULE_STATUS_SCHEMA_VERSION = "module-statuses.v1"
MODULE_ACCESS_PUBLIC = "public"
MODULE_ACCESS_LOCAL_ONLY = "local-only"
MODULE_ACCESS_AUTH_REQUIRED = "auth-required"

_MODULE_METADATA_REQUIRED_FIELDS = {
    "name",
    "version",
    "description",
    "capabilities",
    "data_access",
    "network",
    "permissions",
}


def _parse_module_rate_limit_overrides(raw: str) -> dict[str, dict[str, int]]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        record_error(
            message=f"Invalid module rate limit overrides JSON: {exc}",
            source="api.py:_parse_module_rate_limit_overrides",
            priority=TicketPriority.P2,
        )
        return {}
    if not isinstance(data, dict):
        return {}
    overrides: dict[str, dict[str, int]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        overrides[str(key)] = {
            "calls_per_minute": int(value.get("calls_per_minute", 0) or 0),
            "calls_per_hour": int(value.get("calls_per_hour", 0) or 0),
            "calls_per_day": int(value.get("calls_per_day", 0) or 0),
        }
    return overrides


def _resolve_docs_root(project_root: Path) -> Path:
    docs_root = project_root / "docs" / "architecture"
    if docs_root.exists():
        return project_root
    fallback_root = Path(__file__).resolve().parents[2]
    fallback_docs = fallback_root / "docs" / "architecture"
    if fallback_docs.exists():
        return fallback_root
    return project_root


def _parse_map_dependencies(project_root: Path) -> set[tuple[str, str]]:
    """Parse MAP.yaml to build module dependency edges as a fallback."""
    map_path = project_root / "docs" / "architecture" / "MAP.yaml"
    if not map_path.exists():
        return set()
    try:
        data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
        modules = data.get("modules", []) if isinstance(data, dict) else []
        edges = set()
        for module in modules:
            module_id = module.get("id")
            if not module_id:
                continue
            for dep in module.get("depends_on", []):
                edges.add((module_id, dep))
        return edges
    except Exception as exc:
        record_error(
            message=f"Failed to parse MAP.yaml for dependencies: {exc}",
            source="api.py:_parse_map_dependencies",
            priority=TicketPriority.P2,
        )
        return set()


def _load_module_metadata(create_blueprint) -> tuple[Optional[str], Optional[dict], Optional[object]]:
    module_path = getattr(create_blueprint, "__module__", "")
    if not module_path:
        return None, None, None
    module = importlib.import_module(module_path)
    return module_path, getattr(module, "MODULE_METADATA", None), module


def _validate_module_metadata(module_name: str, metadata: Optional[dict]) -> list[str]:
    errors: list[str] = []
    if not isinstance(metadata, dict):
        return ["metadata_missing"]

    missing = _MODULE_METADATA_REQUIRED_FIELDS - set(metadata.keys())
    if missing:
        errors.append(f"missing_fields: {sorted(missing)}")

    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name_invalid")
    elif name.strip() not in {module_name, f"modules.{module_name}"}:
        errors.append("name_mismatch")

    version = metadata.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append("version_invalid")

    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("description_invalid")

    for key in ("capabilities", "data_access", "network"):
        if not isinstance(metadata.get(key), dict):
            errors.append(f"{key}_invalid")

    permissions = metadata.get("permissions")
    if not isinstance(permissions, list):
        errors.append("permissions_invalid")
    else:
        valid_names = {perm.name for perm in PermissionRegistry.ALL_PERMISSIONS}
        invalid = [name for name in permissions if name not in valid_names]
        if invalid:
            errors.append(f"permissions_unknown: {sorted(invalid)}")

    return errors


def _load_depgraph_edges(project_root: Path) -> set[tuple[str, str]]:
    docs_root = _resolve_docs_root(project_root)
    depgraph_path = docs_root / "docs" / "architecture" / "DEPGRAPH.json"
    if not depgraph_path.exists():
        record_error(
            message="DEPGRAPH.json missing for module dependency validation",
            source="api.py:_load_depgraph_edges",
            priority=TicketPriority.P2,
        )
        return _parse_map_dependencies(docs_root)
    try:
        data = json.loads(depgraph_path.read_text(encoding="utf-8"))
        edges = data.get("edges", []) if isinstance(data, dict) else []
        return {(edge.get("from"), edge.get("to")) for edge in edges if edge}
    except Exception as exc:
        record_error(
            message=f"Failed to read DEPGRAPH.json: {exc}",
            source="api.py:_load_depgraph_edges",
            priority=TicketPriority.P2,
        )
        return _parse_map_dependencies(docs_root)


def _validate_module_dependencies(
    module_name: str,
    dependencies: object,
    depgraph_edges: set[tuple[str, str]],
) -> list[str]:
    if not dependencies:
        return []
    if not isinstance(dependencies, list):
        return ["dependencies_invalid"]
    if not depgraph_edges:
        return ["depgraph_missing"]
    module_id = f"modules.{module_name}"
    missing = [dep for dep in dependencies if (module_id, dep) not in depgraph_edges]
    if missing:
        return [f"missing_edges: {sorted(missing)}"]
    return []



def _register_module_blueprint(
    app,
    module_name: str,
    create_blueprint,
    *,
    project_root: Path,
    host: str,
    port: int,
    status_file: Path,
    access_rule: str,
    register_access,
    register_rate_limit,
    depgraph_edges: set[tuple[str, str]],
    registry: ModuleRegistry | None = None,
) -> bool:
    """Register a module blueprint with consistent logging and guards."""
    expected_prefix = f"/modules/{module_name}"
    module_id = f"modules.{module_name}"

    def _agent_voice_best_effort(thought: str, *, level: str = "INFO", extra: dict | None = None) -> None:
        # Modules must feed info/errors into AgentVoice for review. This is best-effort:
        # failures are captured by raise_af inside record_agent_voice, but we don't block startup.
        try:
            from actifix.agent_voice import record_agent_voice

            record_agent_voice(
                thought,
                agent_id=module_id,
                run_label=f"{module_name}-gui",
                level=level,
                extra=extra,
            )
        except Exception:
            pass

    try:
        if registry and registry.is_disabled(module_id):
            log_event(
                "MODULE_SKIPPED_DISABLED",
                f"Skipped disabled module: {module_name}",
                extra={"module": module_name, "module_id": module_id},
                source="api.py:_register_module_blueprint",
            )
            _agent_voice_best_effort(
                f"Skipped disabled module: {module_name}",
                extra={"module": module_name, "module_id": module_id},
            )
            return False
        status_payload = _read_module_status_payload(status_file)
        if module_id in status_payload.get("statuses", {}).get("disabled", []):
            log_event(
                "MODULE_SKIPPED_DISABLED",
                f"Skipped disabled module: {module_name}",
                extra={"module": module_name, "module_id": module_id},
                source="api.py:_register_module_blueprint",
            )
            _agent_voice_best_effort(
                f"Skipped disabled module: {module_name}",
                extra={"module": module_name, "module_id": module_id},
            )
            return False

        module_path, metadata, module = _load_module_metadata(create_blueprint)
        should_validate_metadata = (module_path or "").startswith("actifix.modules.") or isinstance(metadata, dict)
        metadata_errors = _validate_module_metadata(module_name, metadata) if should_validate_metadata else []
        if should_validate_metadata and metadata_errors:
            record_error(
                message=(
                    f"Module metadata invalid for {module_name}: "
                    f"{', '.join(metadata_errors)}"
                ),
                source="api.py:_register_module_blueprint",
                run_label=f"{module_name}-gui",
                error_type="ModuleMetadataError",
                priority=TicketPriority.P2,
            )
            _agent_voice_best_effort(
                f"Module metadata invalid for {module_name}: {', '.join(metadata_errors)}",
                level="ERROR",
                extra={"module": module_name, "module_id": module_id, "errors": metadata_errors},
            )
            if registry:
                registry.mark_status(module_id, "error")
            else:
                _mark_module_status(status_file, module_id, "error")
            return False

        dependencies = getattr(module, "MODULE_DEPENDENCIES", [])
        dependency_errors = _validate_module_dependencies(
            module_name,
            dependencies,
            depgraph_edges,
        )
        if dependency_errors:
            record_error(
                message=(
                    f"Module dependency validation failed for {module_name}: "
                    f"{', '.join(dependency_errors)}"
                ),
                source="api.py:_register_module_blueprint",
                run_label=f"{module_name}-gui",
                error_type="ModuleDependencyError",
                priority=TicketPriority.P2,
            )
            _agent_voice_best_effort(
                f"Module dependency validation failed for {module_name}: {', '.join(dependency_errors)}",
                level="ERROR",
                extra={"module": module_name, "module_id": module_id, "errors": dependency_errors},
            )
            if registry:
                registry.mark_status(module_id, "error")
            else:
                _mark_module_status(status_file, module_id, "error")
            return False

        blueprint = create_blueprint(project_root=project_root, host=host, port=port)
        blueprint_prefix = getattr(blueprint, "url_prefix", None)

        # Normalize hyphen/underscore for robustness
        def normalize_prefix(p: str) -> str:
            return p.replace('-', '_')

        expected_norm = normalize_prefix(expected_prefix)
        blueprint_norm = normalize_prefix(blueprint_prefix) if blueprint_prefix else None

        if blueprint_norm is None or blueprint_norm == expected_norm:
            if blueprint_prefix is None:
                app.register_blueprint(blueprint, url_prefix=expected_prefix)
            else:
                app.register_blueprint(blueprint)
        else:
            raise ValueError(
                f"Module {module_name} url_prefix mismatch: {blueprint_prefix} != {expected_prefix} "
                f"(normalized: {blueprint_norm} != {expected_norm})"
            )
        register_access(module_name, access_rule)
        register_rate_limit(module_name)
        if registry is not None:
            registry.on_registered(
                module,
                ModuleRuntimeContext(
                    module_name=module_name,
                    module_id=module_id,
                    module_path=module_path,
                    project_root=str(project_root),
                    host=host,
                    port=port,
                ),
                app=app,
                blueprint=blueprint,
            )
            registry.mark_status(module_id, "active")
        else:
            _mark_module_status(status_file, module_id, "active")
        log_event(
            "MODULE_REGISTERED",
            f"Registered module blueprint: {module_name}",
            extra={
                "module": module_name,
                "url_prefix": expected_prefix,
                "module_path": module_path,
            },
            source="api.py:_register_module_blueprint",
        )
        _agent_voice_best_effort(
            f"Registered module blueprint: {module_name}",
            extra={"module": module_name, "module_id": module_id, "url_prefix": expected_prefix, "module_path": module_path},
        )
        return True
    except Exception as exc:
        record_error(
            message=f"Module registration failed for {module_name}: {exc}",
            source="api.py:_register_module_blueprint",
            run_label=f"{module_name}-gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        _agent_voice_best_effort(
            f"Module registration failed for {module_name}: {exc}",
            level="ERROR",
            extra={"module": module_name, "module_id": module_id, "error_type": type(exc).__name__},
        )
        if registry:
            registry.mark_status(module_id, "error")
        else:
            _mark_module_status(status_file, module_id, "error")
        return False


def _is_local_request(req) -> bool:
    address = req.remote_addr or ""
    if address.startswith("127.") or address == "::1":
        return True
    for addr in req.access_route or []:
        if addr.startswith("127.") or addr == "::1":
            return True
    return False


def _extract_bearer_token(req) -> Optional[str]:
    header = req.headers.get("Authorization", "")
    if not header:
        return None
    parts = header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return header.strip()


def _verify_auth_token(token: str) -> bool:
    try:
        from actifix.security.auth import get_token_manager, get_user_manager
        token_manager = get_token_manager()
        user_manager = get_user_manager()
        user_id = token_manager.verify_token(token)
        if not user_id:
            return False
        user = user_manager.get_user(user_id)
        return user is not None and user.is_active
    except Exception as exc:
        record_error(
            message=f"Auth token verification failed: {exc}",
            source="api.py:_verify_auth_token",
            priority=TicketPriority.P2,
        )
        return False


def _verify_admin_password(password: str) -> bool:
    """Verify X-Admin-Password header against admin user."""
    try:
        from actifix.security.auth import get_user_manager
        user_manager = get_user_manager()
        # Try to authenticate as admin user with the password
        user_id = user_manager.authenticate_user('admin', password)
        return user_id is not None
    except Exception:
        return False


def _auth_credentials_valid(req, allow_local: bool = True) -> bool:
    """Check if request has valid admin password or token (local option)."""
    admin_password = req.headers.get("X-Admin-Password", "")
    if admin_password and _verify_admin_password(admin_password):
        return True
    if allow_local and _is_local_request(req):
        return True
    token = _extract_bearer_token(req)
    if token and _verify_auth_token(token):
        return True
    return False


def _check_auth(req) -> bool:
    """Check if request is authenticated via Authorization header or X-Admin-Password."""
    return _auth_credentials_valid(req, allow_local=True)


def _require_auth(req) -> bool:
    """Require credentials (no local bypass)."""
    return _auth_credentials_valid(req, allow_local=False)


def _fetch_module_health(app, module_name: str, timeout_sec: float = 2.0) -> dict:
    import concurrent.futures
    start = time.monotonic()

    def _call_health():
        with app.test_client() as client:
            return client.get(
                f"/modules/{module_name}/health",
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_health)
            response = future.result(timeout=timeout_sec)
    except concurrent.futures.TimeoutError:
        record_error(
            message=f"Module health check timed out for {module_name}",
            source="api.py:_fetch_module_health",
            priority=TicketPriority.P2,
        )
        return {
            "module": module_name,
            "status": "timeout",
            "http_status": 504,
            "elapsed_ms": int((time.monotonic() - start) * 1000),
            "response": None,
        }
    except Exception as exc:
        record_error(
            message=f"Module health check failed for {module_name}: {exc}",
            source="api.py:_fetch_module_health",
            priority=TicketPriority.P2,
        )
        return {
            "module": module_name,
            "status": "error",
            "http_status": 500,
            "elapsed_ms": int((time.monotonic() - start) * 1000),
            "response": None,
        }

    status_code = response.status_code
    payload = response.get_json(silent=True)
    if status_code == 404:
        status = "missing"
    elif status_code >= 400:
        status = "error"
    else:
        status = "ok"

    return {
        "module": module_name,
        "status": status,
        "http_status": status_code,
        "elapsed_ms": int((time.monotonic() - start) * 1000),
        "response": payload,
    }


def _is_system_domain(domain: Optional[str]) -> bool:
    """Decide whether a module belongs to the system catalog."""
    normalized = (domain or "").strip().lower()
    return normalized in {
        "runtime",
        "infra",
        "core",
        "tooling",
        "security",
        "plugins",
        "persistence",
    }


def _parse_modules_markdown(markdown_path: Path) -> List[Dict[str, str]]:
    """Parse MODULES.md for module metadata fallback when DEPGRAPH is missing."""
    if not markdown_path.exists():
        return []

    lines = [line.rstrip("\n") for line in markdown_path.read_text(encoding="utf-8").splitlines()]
    current_domain = ""
    modules: List[Dict[str, str]] = []
    current_module: Dict[str, str] | None = None

    def _finalize_module():
        nonlocal current_module
        if current_module:
            modules.append(current_module)
            current_module = None

    def _start_module(name: str):
        nonlocal current_module
        if current_module:
            modules.append(current_module)
        current_module = {
            "name": name.strip(),
            "domain": current_domain,
            "owner": "",
            "summary": "",
        }

    def _peek_next_nonempty(start: int) -> str:
        for j in range(start + 1, len(lines)):
            if lines[j].strip():
                return lines[j].strip()
        return ""

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("## "):
            next_line = _peek_next_nonempty(idx)
            if next_line.startswith("**Domain:**"):
                _start_module(line[3:].strip())
            else:
                current_domain = line[3:].strip().lower()
        elif line.startswith("### "):
            _start_module(line[4:].strip())
        elif line.startswith("**Domain:**"):
            value = line.split(":", 1)[1].strip().lower()
            if current_module:
                current_module["domain"] = value
            else:
                current_domain = value
        elif line.startswith("**Owner:**"):
            value = line.split(":", 1)[1].strip()
            if current_module:
                current_module["owner"] = value
        elif line.startswith("**Summary:**") or line.startswith("- Summary:"):
            value = line.split(":", 1)[1].strip()
            if current_module:
                current_module["summary"] = value

    _finalize_module()
    return modules


def _load_architecture_details(project_root: Path) -> Dict[str, dict]:
    """Load detailed architecture information from MAP.yaml."""
    map_path = project_root / "docs" / "architecture" / "MAP.yaml"
    details = {}

    if map_path.exists():
        try:
            map_data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
            modules = map_data.get("modules", [])
            for module in modules:
                module_id = module.get("id")
                if module_id:
                    details[module_id] = {
                        "entrypoints": module.get("entrypoints", []),
                        "depends_on": module.get("depends_on", []),
                        "contracts": module.get("contracts", []),
                    }
        except Exception:
            pass

    return details


def _load_modules(project_root: Path) -> Dict[str, List[Dict[str, str]]]:
    """Load modules from canonical DEPGRAPH.json or MODULES.md fallback with detailed metadata."""
    from actifix.state_paths import get_actifix_paths
    paths = get_actifix_paths(project_root=project_root)
    status_file = paths.state_dir / "module_statuses.json"

    status_payload = _read_module_status_payload(status_file)
    statuses = status_payload["statuses"]

    # Load detailed architecture information
    arch_details = _load_architecture_details(project_root)

    def get_status(name: str) -> str:
        if name in statuses.get("disabled", []):
            return "disabled"
        if name in statuses.get("error", []):
            return "error"
        return "active"

    depgraph_path = project_root / "docs" / "architecture" / "DEPGRAPH.json"
    modules_data: List[Dict[str, str]] = []

    if depgraph_path.exists():
        try:
            data = json.loads(depgraph_path.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            for node in nodes:
                module_id = node["id"]
                module_entry = {
                    "name": module_id,
                    "domain": node.get("domain", ""),
                    "owner": node.get("owner", ""),
                    "summary": node.get("label", node["id"]),
                    "status": get_status(module_id),
                    "version": "unknown",
                }
                # Add detailed architecture information
                if module_id in arch_details:
                    details = arch_details[module_id]
                    module_entry["entrypoints"] = details.get("entrypoints", [])
                    module_entry["dependencies"] = details.get("depends_on", [])
                    module_entry["contracts"] = details.get("contracts", [])
                modules_data.append(module_entry)
        except Exception:
            modules_data = []

    if not modules_data:
        fallback_modules = _parse_modules_markdown(project_root / "docs" / "architecture" / "MODULES.md")
        for module in fallback_modules:
            module_id = module["name"]
            module_entry = {
                "name": module_id,
                "domain": module.get("domain", ""),
                "owner": module.get("owner", ""),
                "summary": module.get("summary", module_id),
                "status": get_status(module_id),
                "version": "unknown",
            }
            # Add detailed architecture information if available
            if module_id in arch_details:
                details = arch_details[module_id]
                module_entry["entrypoints"] = details.get("entrypoints", [])
                module_entry["dependencies"] = details.get("depends_on", [])
                module_entry["contracts"] = details.get("contracts", [])
            modules_data.append(module_entry)

    system_domains = {"runtime", "infra", "core", "tooling", "security", "plugins", "persistence"}
    system_modules = [m for m in modules_data if m["domain"].lower() in system_domains]
    user_modules = [m for m in modules_data if m["domain"].lower() not in system_domains]
    return {"system": system_modules, "user": user_modules}


def _annotate_modules_with_runtime_contexts(
    modules_payload: Dict[str, List[Dict[str, str]]],
    registry: Optional[ModuleRegistry],
) -> None:
    """Enrich module metadata with runtime context such as host/port."""
    if not registry or not modules_payload:
        return
    contexts = registry.registered_contexts()
    metadata_map = registry.registered_metadata()
    if not contexts:
        return
    for bucket in modules_payload.values():
        for module in bucket:
            module_id = module.get("name")
            if not module_id:
                continue
            context = contexts.get(module_id)
            if context:
                module["host"] = context.host
                module["port"] = context.port
            metadata = metadata_map.get(module_id)
            if metadata:
                version = metadata.get("version")
                if version:
                    module["version"] = str(version)


def _collect_ai_feedback(limit: int = 40) -> List[str]:
    """Collect recent AI-related feedback for the settings panel."""
    try:
        repo = get_event_repository()
        raw_events = repo.get_recent_events(limit=max(limit * 4, 100))
    except Exception as exc:
        record_error(
            message=f"Failed to read AI feedback events: {exc}",
            source="api.py:_collect_ai_feedback",
            priority=TicketPriority.P2,
        )
        return []

    feedback = []
    for event in reversed(raw_events):
        event_type = (event.get("event_type") or "").upper()
        message = event.get("message") or ""
        if event_type.startswith("AI_") or "AI " in message or "AI_" in message:
            timestamp = event.get("timestamp") or ""
            entry = f"[{timestamp}] {event_type}: {message}"
            feedback.append(entry)
            if len(feedback) >= limit:
                break

    return list(reversed(feedback))


def _run_git_command(cmd: list[str], project_root: Path) -> Optional[str]:
    """Run git command and return stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _gather_version_info(project_root: Path) -> Dict[str, Optional[str]]:
    """Gather version metadata and git status for the dashboard."""
    info_root = Path(project_root).resolve()
    status_output = _run_git_command(["git", "status", "--porcelain"], info_root)
    git_checked = status_output is not None
    clean = git_checked and status_output == ""
    branch = _run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], info_root) if git_checked else None
    commit = _run_git_command(["git", "rev-parse", "HEAD"], info_root) if git_checked else None
    tag = _run_git_command(["git", "describe", "--tags", "--abbrev=0"], info_root) if git_checked else None

    return {
        "version": __version__,
        "git_checked": git_checked,
        "clean": clean,
        "dirty": git_checked and not clean,
        "branch": branch,
        "commit": commit,
        "tag": tag,
        "status": status_output,
    }


def _map_event_type_to_level(event_type: str, message: str) -> str:
    """Map ACTIFIX event types to log levels used by the frontend."""
    normalized = (event_type or "").upper()
    if "✓" in message or "SUCCESS" in message.upper():
        return "SUCCESS"
    if "✗" in message:
        return "ERROR"
    if "⚠" in message:
        return "WARNING"
    if normalized in {"ERROR", "DISPATCH_FAILED"} or "ERROR" in message.upper():
        return "ERROR"
    if normalized in {"ASCII_BANNER"}:
        return "BANNER"
    if normalized in {"ACTION_DECIDED"}:
        return "ACTION"
    if normalized in {"THOUGHT_PROCESS"}:
        return "THOUGHT"
    if normalized in {"TESTING"}:
        return "TEST"
    if normalized in {"TICKET_CLOSED", "DISPATCH_SUCCESS", "TICKET_COMPLETED"}:
        return "SUCCESS"
    if normalized in {"WARNING", "TICKET_ALREADY_COMPLETED"} or "WARNING" in message.upper():
        return "WARNING"
    return "INFO"


def _parse_log_line(line: str) -> Optional[dict]:
    """Parse a single AFLog line into structured fields."""
    stripped = line.strip()
    if not stripped:
        return None

    # AFLog structured format: "timestamp | EVENT | ticket | message | extra"
    if " | " in stripped:
        parts = [part.strip() for part in stripped.split(" | ")]
        timestamp = parts[0] if len(parts) >= 1 else ""
        event_type = parts[1] if len(parts) >= 2 else "LOG"
        ticket_id = parts[2] if len(parts) >= 3 else "-"
        message = parts[3] if len(parts) >= 4 else stripped
        extra = parts[4] if len(parts) >= 5 else None
        level = _map_event_type_to_level(event_type, message)

        return {
            "timestamp": timestamp,
            "event": event_type,
            "ticket": ticket_id,
            "text": message,
            "extra": extra,
            "level": level,
        }

    # Simple text formats such as "LEVEL: message" or icon-prefixed lines
    icon_levels = {
        "✓": "SUCCESS",
        "✗": "ERROR",
        "⚠": "WARNING",
    }
    for icon, level in icon_levels.items():
        if stripped.startswith(icon):
            message = stripped[len(icon):].strip() or stripped
            return {
                "timestamp": "",
                "event": "LOG",
                "ticket": "-",
                "text": message,
                "extra": None,
                "level": level,
            }

    prefix, sep, remainder = stripped.partition(":")
    if sep:
        event_type = prefix.strip() or "LOG"
        message = remainder.strip() or stripped
        level = _map_event_type_to_level(event_type, message)
        return {
            "timestamp": "",
            "event": event_type,
            "ticket": "-",
            "text": message,
            "extra": None,
            "level": level,
        }

    level = _map_event_type_to_level("LOG", stripped)
    return {
        "timestamp": "",
        "event": "LOG",
        "ticket": "-",
        "text": stripped,
        "extra": None,
        "level": level,
    }


def create_app(
    project_root: Optional[Path] = None,
    host: str = "127.0.0.1",
    port: int = 5001,
) -> "Flask":
    """
    Create and configure the Flask API application.
    
    Args:
        project_root: Optional project root path.
    
    Returns:
        Configured Flask application.
    """
    if not _ensure_web_dependencies():
        raise ImportError(
            "Flask and flask-cors are required for the API server. "
            "Install with: pip install flask flask-cors"
        )
    
    # Import here after ensuring dependencies are available
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    
    # Configure Flask to serve static files from actifix-frontend
    root = project_root or Path.cwd()
    frontend_dir = root / 'actifix-frontend'
    
    app = Flask(
        __name__,
        static_folder=str(frontend_dir),
        static_url_path=''
    )
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    CORS(app)  # Enable CORS for frontend

    # Initialize SocketIO for real-time WebSocket updates
    global _socketio_instance
    socketio = None
    if SOCKETIO_AVAILABLE:
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
        _socketio_instance = socketio
        app.extensions["socketio"] = socketio

        @socketio.on("connect", namespace="/tickets")
        def handle_ticket_connect():
            """Handle client connection to tickets namespace."""
            pass

        @socketio.on("disconnect", namespace="/tickets")
        def handle_ticket_disconnect():
            """Handle client disconnection from tickets namespace."""
            pass

        @socketio.on("subscribe", namespace="/tickets")
        def handle_subscribe(data):
            """Handle subscription to specific ticket updates."""
            pass

    # Store project root and API binding info in app config
    app.config['PROJECT_ROOT'] = root
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in development
    app.config['API_HOST'] = host
    app.config['API_PORT'] = port
    module_registry = ModuleRegistry(project_root=root)
    app.extensions["actifix_module_registry"] = module_registry
    status_file = get_actifix_paths(project_root=root).state_dir / "module_statuses.json"
    depgraph_edges = _load_depgraph_edges(root)
    config = load_config(project_root=root, fail_fast=False)
    rate_limiter = get_rate_limiter()
    module_rate_overrides = _parse_module_rate_limit_overrides(
        config.module_rate_limit_overrides_json
    )
    module_rate_rules: dict[str, RateLimitConfig] = {}
    module_access_rules: dict[str, str] = {}

    def _register_module_access(module_name: str, access_rule: str) -> None:
        module_access_rules[module_name] = access_rule or MODULE_ACCESS_PUBLIC

    def _register_module_rate_limit(module_name: str) -> None:
        override = module_rate_overrides.get(module_name, {})
        calls_per_minute = override.get("calls_per_minute") or config.module_rate_limit_per_minute
        calls_per_hour = override.get("calls_per_hour") or config.module_rate_limit_per_hour
        calls_per_day = override.get("calls_per_day") or config.module_rate_limit_per_day
        provider_key = f"module:{module_name}"
        limit_config = RateLimitConfig(
            provider_name=provider_key,
            calls_per_minute=calls_per_minute,
            calls_per_hour=calls_per_hour,
            calls_per_day=calls_per_day,
            enabled=True,
        )
        rate_limiter.set_limit(provider_key, limit_config)
        module_rate_rules[module_name] = limit_config

    _create_yahtzee_blueprint = None
    _yahtzee_access_rule = MODULE_ACCESS_PUBLIC
    _yahtzee_host = host
    _yahtzee_port = port
    try:
        _, yahtzee_module, _ = module_registry.import_module("yahtzee")
        _create_yahtzee_blueprint = getattr(yahtzee_module, "create_blueprint", None)
        _yahtzee_access_rule = getattr(yahtzee_module, "ACCESS_RULE", MODULE_ACCESS_PUBLIC)
        yahtzee_defaults = getattr(yahtzee_module, "MODULE_DEFAULTS", {})
        _yahtzee_host = yahtzee_defaults.get("host", host)
        _yahtzee_port = yahtzee_defaults.get("port", port)
    except ImportError:
        pass
    except Exception as exc:
        record_error(
            message=f"Failed to import yahtzee module: {exc}",
            source="api.py:module_loader",
            priority=TicketPriority.P2,
        )

    _create_superquiz_blueprint = None
    _superquiz_access_rule = MODULE_ACCESS_PUBLIC
    _superquiz_host = host
    _superquiz_port = port
    try:
        _, superquiz_module, _ = module_registry.import_module("superquiz")
        _create_superquiz_blueprint = getattr(superquiz_module, "create_blueprint", None)
        _superquiz_access_rule = getattr(superquiz_module, "ACCESS_RULE", MODULE_ACCESS_PUBLIC)
        superquiz_defaults = getattr(superquiz_module, "MODULE_DEFAULTS", {})
        _superquiz_host = superquiz_defaults.get("host", host)
        _superquiz_port = superquiz_defaults.get("port", port)
    except ImportError:
        pass
    except Exception as exc:
        record_error(
            message=f"Failed to import superquiz module: {exc}",
            source="api.py:module_loader",
            priority=TicketPriority.P2,
        )

    _create_shootymcshoot_blueprint = None
    _shootymcshoot_access_rule = MODULE_ACCESS_PUBLIC
    _shootymcshoot_host = host
    _shootymcshoot_port = port
    try:
        _, shootymcshoot_module, _ = module_registry.import_module("shootymcshoot")
        _create_shootymcshoot_blueprint = getattr(shootymcshoot_module, "create_blueprint", None)
        _shootymcshoot_access_rule = getattr(shootymcshoot_module, "ACCESS_RULE", MODULE_ACCESS_PUBLIC)
        shootymcshoot_defaults = getattr(shootymcshoot_module, "MODULE_DEFAULTS", {})
        _shootymcshoot_host = shootymcshoot_defaults.get("host", host)
        _shootymcshoot_port = shootymcshoot_defaults.get("port", port)
    except ImportError:
        pass
    except Exception as exc:
        record_error(
            message=f"Failed to import shootymcshoot module: {exc}",
            source="api.py:module_loader",
            priority=TicketPriority.P2,
        )

    _create_dev_assistant_blueprint = None
    _dev_assistant_access_rule = MODULE_ACCESS_PUBLIC
    _dev_assistant_host = host
    _dev_assistant_port = port
    try:
        _, dev_assistant_module, _ = module_registry.import_module("dev_assistant")
        _create_dev_assistant_blueprint = getattr(dev_assistant_module, "create_blueprint", None)
        _dev_assistant_access_rule = getattr(dev_assistant_module, "ACCESS_RULE", MODULE_ACCESS_PUBLIC)
        dev_assistant_defaults = getattr(dev_assistant_module, "MODULE_DEFAULTS", {})
        _dev_assistant_host = dev_assistant_defaults.get("host", host)
        _dev_assistant_port = dev_assistant_defaults.get("port", port)
    except ImportError:
        pass
    except Exception as exc:
        record_error(
            message=f"Failed to import dev_assistant module: {exc}",
            source="api.py:module_loader",
            priority=TicketPriority.P2,
        )

    _create_hollogram_blueprint = None
    _hollogram_access_rule = MODULE_ACCESS_LOCAL_ONLY
    _hollogram_host = host
    _hollogram_port = port
    try:
        _, hollogram_module, _ = module_registry.import_module("hollogram")
        _create_hollogram_blueprint = getattr(hollogram_module, "create_blueprint", None)
        _hollogram_access_rule = getattr(hollogram_module, "ACCESS_RULE", MODULE_ACCESS_LOCAL_ONLY)
        hollogram_defaults = getattr(hollogram_module, "MODULE_DEFAULTS", {})
        _hollogram_host = hollogram_defaults.get("host", host)
        _hollogram_port = hollogram_defaults.get("port", port)
    except ImportError:
        pass
    except Exception as exc:
        record_error(
            message=f"Failed to import hollogram module: {exc}",
            source="api.py:module_loader",
            priority=TicketPriority.P2,
        )

    if _create_yahtzee_blueprint:
        _register_module_blueprint(
            app,
            "yahtzee",
            _create_yahtzee_blueprint,
            project_root=root,
            host=_yahtzee_host,
            port=_yahtzee_port,
            status_file=status_file,
            access_rule=_yahtzee_access_rule,
            register_access=_register_module_access,
            register_rate_limit=_register_module_rate_limit,
            depgraph_edges=depgraph_edges,
            registry=module_registry,
        )

    if _create_superquiz_blueprint:
        _register_module_blueprint(
            app,
            "superquiz",
            _create_superquiz_blueprint,
            project_root=root,
            host=_superquiz_host,
            port=_superquiz_port,
            status_file=status_file,
            access_rule=_superquiz_access_rule,
            register_access=_register_module_access,
            register_rate_limit=_register_module_rate_limit,
            depgraph_edges=depgraph_edges,
            registry=module_registry,
        )

    if _create_shootymcshoot_blueprint:
        _register_module_blueprint(
            app,
            "shootymcshoot",
            _create_shootymcshoot_blueprint,
            project_root=root,
            host=_shootymcshoot_host,
            port=_shootymcshoot_port,
            status_file=status_file,
            access_rule=_shootymcshoot_access_rule,
            register_access=_register_module_access,
            register_rate_limit=_register_module_rate_limit,
            depgraph_edges=depgraph_edges,
            registry=module_registry,
        )

    if _create_dev_assistant_blueprint:
        _register_module_blueprint(
            app,
            "dev_assistant",
            _create_dev_assistant_blueprint,
            project_root=root,
            host=_dev_assistant_host,
            port=_dev_assistant_port,
            status_file=status_file,
            access_rule=_dev_assistant_access_rule,
            register_access=_register_module_access,
            register_rate_limit=_register_module_rate_limit,
            depgraph_edges=depgraph_edges,
            registry=module_registry,
        )

    if _create_hollogram_blueprint:
        _register_module_blueprint(
            app,
            "hollogram",
            _create_hollogram_blueprint,
            project_root=root,
            host=_hollogram_host,
            port=_hollogram_port,
            status_file=status_file,
            access_rule=_hollogram_access_rule,
            register_access=_register_module_access,
            register_rate_limit=_register_module_rate_limit,
            depgraph_edges=depgraph_edges,
            registry=module_registry,
        )

    @app.before_request
    def _enforce_module_access():
        path = request.path or ""
        if not path.startswith("/modules/"):
            return None
        parts = path.split("/")
        if len(parts) < 3 or not parts[2]:
            return None
        module_name = parts[2]
        access_rule = module_access_rules.get(module_name, MODULE_ACCESS_PUBLIC)
        if access_rule == MODULE_ACCESS_PUBLIC:
            return None
        if access_rule == MODULE_ACCESS_LOCAL_ONLY:
            if _is_local_request(request):
                return None
            return jsonify({"error": "Module access restricted to local requests"}), 403
        if access_rule == MODULE_ACCESS_AUTH_REQUIRED:
            if not _auth_credentials_valid(request, allow_local=False):
                return jsonify({"error": "Authorization required"}), 401
            return None
        return jsonify({"error": "Unsupported module access rule"}), 403

    @app.before_request
    def _enforce_module_rate_limit():
        path = request.path or ""
        if not path.startswith("/modules/"):
            return None
        parts = path.split("/")
        if len(parts) < 3 or not parts[2]:
            return None
        module_name = parts[2]
        limit_config = module_rate_rules.get(module_name)
        if not limit_config:
            return None
        try:
            rate_limiter.check_rate_limit(limit_config.provider_name)
        except RateLimitError as exc:
            record_error(
                message=f"Module rate limit exceeded for {module_name}: {exc}",
                source="api.py:_enforce_module_rate_limit",
                priority=TicketPriority.P2,
            )
            return jsonify({"error": "Module rate limit exceeded"}), 429
        g.module_rate_limit_provider = limit_config.provider_name
        return None

    @app.after_request
    def _record_module_rate_limit(response):
        provider = getattr(g, "module_rate_limit_provider", None)
        if provider:
            success = response.status_code < 400
            rate_limiter.record_call(provider, success=success, error=None if success else response.status)
        return response

    @app.after_request
    def _add_security_headers(response):
        """Add security headers including Content Security Policy."""
        # Content Security Policy - restricts sources for scripts, styles, etc.
        # Allow self for API and frontend assets
        csp = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",  # Needed for inline scripts in frontend
            "style-src": "'self' 'unsafe-inline'",   # Needed for inline styles in frontend
            "img-src": "'self' data: https:",
            "connect-src": "'self' ws: wss:",  # Allow WebSocket connections
            "font-src": "'self'",
            "object-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        }
        
        # Convert CSP dict to header string
        csp_header = "; ".join([f"{k} {v}" for k, v in csp.items()])
        
        response.headers["Content-Security-Policy"] = csp_header
        
        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

    @app.route('/', methods=['GET'])
    def serve_index():
        """Serve the dashboard frontend."""
        response = app.send_static_file('index.html')
        # Disable caching for development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Get comprehensive health check data."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        
        # Health summary
        health = get_health(paths)
        
        # Git info
        git_info = _gather_version_info(app.config['PROJECT_ROOT'])
        
        # Disk usage
        disk_info = None
        try:
            import psutil
            disk = psutil.disk_usage(str(paths.data_dir.parent))
            disk_gb = lambda b: round(b / (1024**3), 1)
            disk_info = {
                'total_gb': disk_gb(disk.total),
                'used_gb': disk_gb(disk.used),
                'free_gb': disk_gb(disk.free),
                'percent': round((disk.used / disk.total) * 100, 1)
            }
        except Exception:
            disk_info = None
        
        # Recent events snippet
        recent_events = []
        try:
            repo = get_event_repository()
            raw_events = repo.get_recent_events(limit=5)
            recent_events = [{
                "timestamp": e.get("timestamp", ""),
                "event": e.get("event_type", "LOG"),
                "text": (e.get("message", "")[:50] + "...") if len(e.get("message", "")) > 50 else e.get("message", "")
            } for e in raw_events[-5:][::-1]]
        except Exception:
            recent_events = []
        
        # Paths summary
        paths_dict = {
            "base_dir": str(paths.base_dir),
            "data_dir": str(paths.data_dir),
            "logs_dir": str(paths.logs_dir),
            "state_dir": str(paths.state_dir),
        }
        health = get_health(paths)
        
        return jsonify({
            'healthy': health.healthy,
            'status': health.status,
            'timestamp': health.timestamp.isoformat(),
            'metrics': {
                'open_tickets': health.open_tickets,
                'completed_tickets': health.completed_tickets,
                'sla_breaches': health.sla_breaches,
                'oldest_ticket_age_hours': health.oldest_ticket_age_hours,
            },
            'filesystem': {
                'files_exist': health.files_exist,
                'files_writable': health.files_writable,
            },
            'warnings': health.warnings,
            'errors': health.errors,
            'details': health.details,
    })
    
    @app.route('/api/version', methods=['GET'])
    def api_version():
        """Return version metadata and git status for the dashboard."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        root = Path(app.config['PROJECT_ROOT'])
        info = _gather_version_info(root)
        return jsonify(info)

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        """Get ticket statistics."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        stats = get_ticket_stats(paths)
        breaches = check_sla_breaches(paths)
        
        return jsonify({
            'total': stats.get('total', 0),
            'open': stats.get('open', 0),
            'completed': stats.get('completed', 0),
            'by_priority': stats.get('by_priority', {}),
            'sla_breaches': breaches,
        })

    @app.route('/api/metrics', methods=['GET'])
    def api_metrics():
        """Export Prometheus-compatible metrics."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        try:
            payload = export_prometheus_metrics(paths)
        except Exception as exc:
            record_error(
                message=f"Metrics export failed: {exc}",
                source="api.py:api_metrics",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return jsonify({'error': 'Failed to export metrics'}), 500

        response = app.response_class(payload, mimetype="text/plain")
        response.headers["Content-Type"] = "text/plain; version=0.0.4"
        return response

    @app.route('/api/metrics/json', methods=['GET'])
    def api_metrics_json():
        """Export metrics as JSON for tool integration."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        try:
            paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
            health = get_health(paths)

            # Extract stats from health details
            stats = health.details.get("stats", {})
            by_priority = stats.get("by_priority", {})

            # Build comprehensive metrics object
            metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": __version__,
                "health_status": health.status,
                "healthy": health.healthy,
                "tickets": {
                    "total": stats.get("total", 0),
                    "open": stats.get("open", 0),
                    "in_progress": stats.get("in_progress", 0),
                    "completed": stats.get("completed", 0),
                    "by_priority": {
                        "P0": by_priority.get("P0", 0),
                        "P1": by_priority.get("P1", 0),
                        "P2": by_priority.get("P2", 0),
                        "P3": by_priority.get("P3", 0),
                        "P4": by_priority.get("P4", 0),
                    },
                    "sla_breaches": health.sla_breaches,
                },
                "system": {
                    "platform": platform.system(),
                    "python_version": platform.python_version(),
                    "warnings": health.warnings,
                    "errors": health.errors,
                },
            }

            return jsonify(metrics)

        except Exception as exc:
            record_error(
                message=f"JSON metrics export failed: {exc}",
                source="api.py:api_metrics_json",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return jsonify({'error': 'Failed to export metrics'}), 500

    @app.route('/api/status/export', methods=['GET'])
    def api_status_export():
        """Export a status snapshot for sharing."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        root = Path(app.config['PROJECT_ROOT'])
        paths = get_actifix_paths(project_root=root)
        try:
            health = get_health(paths)
            stats = get_ticket_stats(paths)
            modules = _load_modules(root)
            registry = app.extensions.get("actifix_module_registry")
            _annotate_modules_with_runtime_contexts(modules, registry)
            version_info = _gather_version_info(root)
        except Exception as exc:
            record_error(
                message=f"Status export failed: {exc}",
                source="api.py:api_status_export",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return jsonify({'error': 'Failed to export status'}), 500

        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health': {
                'healthy': health.healthy,
                'status': health.status,
                'warnings': health.warnings,
                'errors': health.errors,
            },
            'tickets': {
                'total': stats.get('total', 0),
                'open': stats.get('open', 0),
                'completed': stats.get('completed', 0),
                'by_priority': stats.get('by_priority', {}),
            },
            'modules': modules,
            'version': version_info,
        })
    
    @app.route('/api/tickets', methods=['GET'])
    def api_tickets():
        """Get recent tickets list."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        limit = request.args.get('limit', 20, type=int)

        open_tickets = get_open_tickets(paths)
        completed_tickets = get_completed_tickets(paths)

        # Get stats using same method as /health endpoint for consistency
        stats = get_ticket_stats(paths)

        # Format tickets for API response
        def format_ticket(ticket, status='open'):
            return {
                'ticket_id': ticket.ticket_id,
                'error_type': ticket.error_type,
                'message': ticket.message[:100] + '...' if len(ticket.message) > 100 else ticket.message,
                'source': ticket.source,
                'priority': ticket.priority,
                'created': ticket.created,
                'status': status,
            }

        all_tickets = [
            format_ticket(t, 'open') for t in open_tickets
        ] + [
            format_ticket(t, 'completed') for t in completed_tickets
        ]

        # Sort by created date (newest first)
        all_tickets.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'tickets': all_tickets[:limit],
            'total_open': stats.get('open', 0),
            'total_completed': stats.get('completed', 0),
        })

    @app.route('/api/ticket/<ticket_id>', methods=['GET'])
    def api_ticket(ticket_id):
        """Get full ticket details by ID."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        from .persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        ticket = repo.get_ticket(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket)

    @app.route('/api/raise-ticket', methods=['POST'])
    def api_raise_ticket():
        """
        Create a new ticket via API.

        Request body (JSON):
            {
                "message": "Error description (required)",
                "source": "file.py:line or module name (required)",
                "error_type": "ErrorType (optional, default: APITicket)",
                "priority": "P0|P1|P2|P3|P4 (optional, default: P2)",
                "run_label": "Label for this ticket (optional, default: api-created)",
                "capture_context": false (optional, whether to capture stack/file context)
            }

        Returns:
            {
                "success": true,
                "ticket_id": "ACT-YYYYMMDD-XXXXX",
                "message": "Ticket created successfully",
                "priority": "P2"
            }
        """
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        data = request.get_json() if request.is_json else {}

        # Validate required fields
        if not data.get('message'):
            return jsonify({
                'error': 'Missing required field: message',
                'required_fields': ['message', 'source'],
                'optional_fields': ['error_type', 'priority', 'run_label', 'capture_context']
            }), 400

        if not data.get('source'):
            return jsonify({
                'error': 'Missing required field: source',
                'hint': 'Provide source as "file.py:line" or module name'
            }), 400

        # Parse priority
        priority_str = data.get('priority', 'P2')
        try:
            if isinstance(priority_str, str):
                priority = TicketPriority[priority_str] if priority_str.startswith('P') else TicketPriority[f'P{priority_str}']
            else:
                priority = TicketPriority.P2
        except (KeyError, ValueError):
            return jsonify({
                'error': f'Invalid priority: {priority_str}',
                'valid_priorities': ['P0', 'P1', 'P2', 'P3', 'P4']
            }), 400

        # Create the ticket
        try:
            ticket_id = record_error(
                message=data['message'],
                source=data['source'],
                error_type=data.get('error_type', 'APITicket'),
                priority=priority,
                run_label=data.get('run_label', 'api-created'),
                capture_context=data.get('capture_context', False),
                paths=paths,
            )

            # Emit WebSocket event for new ticket
            emit_ticket_event('ticket_created', {
                'ticket_id': ticket_id,
                'error_type': data.get('error_type', 'APITicket'),
                'priority': priority_str,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })

            return jsonify({
                'success': True,
                'ticket_id': ticket_id,
                'message': 'Ticket created successfully',
                'priority': priority_str,
            }), 201

        except Exception as e:
            return jsonify({
                'error': f'Failed to create ticket: {str(e)}',
                'details': str(e)
            }), 500

    @app.route('/api/complete-ticket', methods=['POST'])
    def api_complete_ticket():
        """
        Mark a ticket as complete.

        Request body (JSON):
            {
                "ticket_id": "ACT-YYYYMMDD-XXXXX (required)",
                "completion_notes": "Detailed completion notes with Implementation and Files sections (required)",
                "test_steps": "Steps taken to test the fix (required)",
                "test_results": "Test results and verification (required)",
                "summary": "Brief summary (optional)",
                "test_documentation_url": "URL to test documentation (optional)"
            }

        Returns:
            {
                "success": true,
                "ticket_id": "ACT-YYYYMMDD-XXXXX",
                "message": "Ticket marked complete"
            }
        """
        # Require authentication for mutations
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401

        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])

        # Enforce Raise_AF-only policy
        enforce_raise_af_only(paths)

        data = request.get_json() if request.is_json else {}

        # Validate required fields
        if not data.get('ticket_id'):
            return jsonify({'error': 'Missing required field: ticket_id'}), 400

        completion_notes = data.get('completion_notes')
        test_steps = data.get('test_steps')
        test_results = data.get('test_results')

        if not completion_notes or not test_steps or not test_results:
            return jsonify({
                'error': 'completion_notes, test_steps, and test_results are required',
                'hint': 'Include Implementation and Files sections in completion_notes.'
            }), 400

        # Import mark_ticket_complete
        from .do_af import mark_ticket_complete

        try:
            success = mark_ticket_complete(
                ticket_id=data['ticket_id'],
                completion_notes=completion_notes,
                test_steps=test_steps,
                test_results=test_results,
                summary=data.get('summary', ''),
                test_documentation_url=data.get('test_documentation_url'),
                paths=paths,
            )

            if success:
                # Emit WebSocket event
                emit_ticket_event('ticket_completed', {
                    'ticket_id': data['ticket_id'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                })

                return jsonify({
                    'success': True,
                    'ticket_id': data['ticket_id'],
                    'message': 'Ticket marked complete'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to mark ticket complete',
                    'ticket_id': data['ticket_id']
                }), 500

        except Exception as e:
            return jsonify({
                'error': f'Failed to complete ticket: {str(e)}',
                'details': str(e)
            }), 500

    @app.route('/api/fix-ticket', methods=['POST'])
    def api_fix_ticket():
        """Fix the highest priority open ticket with detailed logging."""
        # Require authentication (no local bypass for mutations)
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])

        # Enforce Raise_AF-only policy before modifying tickets
        # (Defense in depth - also enforced in fix_highest_priority_ticket)
        enforce_raise_af_only(paths)

        # Require explicit completion evidence from request body
        data = request.get_json() if request.is_json else {}
        completion_notes = data.get('completion_notes')
        test_steps = data.get('test_steps')
        test_results = data.get('test_results')
        summary = data.get('summary', 'Resolved via dashboard fix')
        test_documentation_url = data.get('test_documentation_url')

        if not completion_notes or not test_steps or not test_results:
            return jsonify({
                'error': 'completion_notes, test_steps, and test_results are required',
                'hint': 'Include Implementation and Files sections in completion_notes.'
            }), 400

        result = fix_highest_priority_ticket(
            paths,
            completion_notes=completion_notes,
            test_steps=test_steps,
            test_results=test_results,
            summary=summary,
            test_documentation_url=test_documentation_url
        )

        # Emit WebSocket event for ticket completion
        if result.get('processed') and result.get('ticket_id'):
            emit_ticket_event('ticket_completed', {
                'ticket_id': result.get('ticket_id'),
                'priority': result.get('priority'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })

        return jsonify({
            'processed': result.get('processed', False),
            'ticket_id': result.get('ticket_id'),
            'priority': result.get('priority'),
            'reason': result.get('reason'),
            'thought': result.get('thought'),
            'action': result.get('action'),
            'testing': result.get('testing'),
        })
    
    @app.route('/api/logs', methods=['GET'])
    def api_logs():
        """Get log entries (database-backed, with optional setup log file)."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        log_type = request.args.get('type', 'audit')
        max_lines = request.args.get('lines', 100, type=int)
        if log_type == "setup":
            setup_log = app.config['PROJECT_ROOT'] / 'logs' / 'setup.log'
            if not setup_log.exists():
                return jsonify({
                    'content': [],
                    'file': 'logs/setup.log',
                    'error': 'Log file not found',
                })
            try:
                content = setup_log.read_text(encoding='utf-8', errors='replace').strip()
                file_lines = content.split('\n') if content else []
                recent_lines = file_lines[-max_lines:] if len(file_lines) > max_lines else file_lines
                parsed_lines = []
                for line in recent_lines:
                    parsed = _parse_log_line(line)
                    if parsed:
                        parsed_lines.append(parsed)
                return jsonify({
                    'content': parsed_lines,
                    'file': str(setup_log),
                    'total_lines': len(file_lines),
                })
            except Exception as e:
                return jsonify({
                    'content': [],
                    'file': str(setup_log),
                    'error': str(e),
                })

        try:
            repo = get_event_repository()
            limit = max_lines if max_lines > 0 else 100
            if log_type == "errors":
                raw_events = repo.get_events(EventFilter(limit=max(limit * 5, 100)))
                events = [
                    event for event in raw_events
                    if (event.get("level") or "").upper() in {"ERROR", "CRITICAL"}
                ]
            else:
                events = repo.get_recent_events(limit=limit)

            events = list(reversed(events))
            if len(events) > max_lines:
                events = events[-max_lines:]

            parsed_lines = []
            for event in events:
                event_type = event.get("event_type") or "LOG"
                message = event.get("message") or ""
                level = (event.get("level") or "").upper()
                if not level:
                    level = _map_event_type_to_level(event_type, message)
                parsed_lines.append({
                    "timestamp": event.get("timestamp") or "",
                    "event": event_type,
                    "ticket": event.get("ticket_id") or "-",
                    "text": message,
                    "extra": event.get("extra_json"),
                    "level": level,
                })

            return jsonify({
                'content': parsed_lines,
                'file': 'data/actifix.db:event_log',
                'total_lines': len(events),
            })
        except Exception as e:
            return jsonify({
                'content': [],
                'file': 'data/actifix.db:event_log',
                'error': str(e),
            })

    def _collect_recent_events(limit: int = 5) -> List[Dict[str, str]]:
        """Helper to fetch recent events for dashboard summary sections."""
        try:
            repo = get_event_repository()
            raw_events = repo.get_recent_events(limit=max(limit, 1))
            recent = raw_events[-limit:][::-1]
            entries = []
            for event in recent:
                message = event.get("message", "") or ""
                entries.append({
                    "timestamp": event.get("timestamp", ""),
                    "event": event.get("event_type", "LOG"),
                    "text": (message[:50] + "...") if len(message) > 50 else message,
                })
            return entries
        except Exception:
            return []

    @app.route('/api/system', methods=['GET'])
    def api_system():
        """Get system information."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        uptime_seconds = time.time() - SERVER_START_TIME
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        disk_info = None
        memory_info = {
            'total_gb': 0.0,
            'used_gb': 0.0,
            'percent': 0.0,
        }
        cpu_percent = 0.0

        try:
            import psutil
            mem = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(mem.total / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'percent': round(mem.percent, 1),
            }
            cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)

            disk = psutil.disk_usage(str(paths.data_dir.parent))
            disk_gb = lambda b: round(b / (1024**3), 1)
            disk_info = {
                'total_gb': disk_gb(disk.total),
                'used_gb': disk_gb(disk.used),
                'free_gb': disk_gb(disk.free),
                'percent': round((disk.used / disk.total) * 100, 1),
            }
        except ImportError:
            pass
        except Exception:
            cpu_percent = 0.0

        paths_dict = {
            "base_dir": str(paths.base_dir),
            "data_dir": str(paths.data_dir),
            "logs_dir": str(paths.logs_dir),
            "state_dir": str(paths.state_dir),
        }
        health = get_health(paths)
        git_info = _gather_version_info(app.config['PROJECT_ROOT'])
        recent_events = _collect_recent_events(limit=5)

        return jsonify({
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'python_version': platform.python_version(),
            },
            'project': {
                'root': str(app.config['PROJECT_ROOT']),
                'actifix_dir': str(paths.base_dir),
            },
            'server': {
                'uptime': uptime_str,
                'uptime_seconds': int(uptime_seconds),
                'start_time': datetime.fromtimestamp(
                    SERVER_START_TIME, tz=timezone.utc
                ).isoformat(),
            },
            'resources': {
                'memory': memory_info if memory_info else None,
                'cpu_percent': cpu_percent,
                'disk': disk_info,
            },
            'health': {
                'healthy': health.healthy,
                'status': health.status,
                'open_tickets': getattr(health, 'open_tickets', 0),
                'warnings': len(getattr(health, 'warnings', [])),
                'errors': len(getattr(health, 'errors', [])),
            },
            'git': git_info,
            'paths': paths_dict,
            'recent_events': recent_events,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/modules', methods=['GET'])
    def api_modules():
        """List system/user modules from architecture catalog."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        modules = _load_modules(app.config['PROJECT_ROOT'])
        registry = app.extensions.get("actifix_module_registry")
        _annotate_modules_with_runtime_contexts(modules, registry)
        return jsonify(modules)

    @app.route('/api/modules/<module_id>/health', methods=['GET'])
    def api_module_health(module_id):
        """Aggregate module health and status."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        module_name = module_id.split(".", 1)[1] if module_id.startswith("modules.") else module_id
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        status_payload = _read_module_status_payload(paths.state_dir / "module_statuses.json")
        statuses = status_payload.get("statuses", {})
        module_status = "active"
        if f"modules.{module_name}" in statuses.get("disabled", []):
            module_status = "disabled"
        elif f"modules.{module_name}" in statuses.get("error", []):
            module_status = "error"

        result = _fetch_module_health(app, module_name)
        result["module_id"] = module_id
        result["module_status"] = module_status

        return jsonify(result), result.get("http_status", 200)

    @app.route('/api/modules/<module_id>', methods=['POST'])
    def api_toggle_module(module_id):
        """Toggle module status (enable/disable)."""
        # Require authentication (no local bypass for mutations)
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401
        
        from actifix.state_paths import get_actifix_paths

        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        status_file = paths.state_dir / "module_statuses.json"

        try:
            status_payload = _read_module_status_payload(status_file)
            statuses = status_payload["statuses"]

            if module_id in statuses.get("disabled", []):
                statuses["disabled"].remove(module_id)
                if module_id not in statuses.get("active", []):
                    statuses["active"].append(module_id)
                if module_id in statuses.get("error", []):
                    statuses["error"].remove(module_id)
                action = "enabled"
            else:
                if module_id in statuses.get("active", []):
                    statuses["active"].remove(module_id)
                if module_id not in statuses.get("disabled", []):
                    statuses["disabled"].append(module_id)
                action = "disabled"

            status_payload["statuses"] = _normalize_module_statuses(statuses)
            status_payload["schema_version"] = MODULE_STATUS_SCHEMA_VERSION
            _write_module_status_payload(status_file, status_payload)
            return jsonify({"success": True, "module_id": module_id, "action": action})
        except Exception as e:
            record_error(
                message=f"Failed to toggle module status for {module_id}: {e}",
                source="api.py:api_toggle_module",
                priority=TicketPriority.P2,
            )
            return jsonify({"error": str(e)}), 500

    @app.route('/api/ping', methods=['GET'])
    def api_ping():
        """Simple ping endpoint for connectivity check."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/websocket/status', methods=['GET'])
    def api_websocket_status():
        """Return WebSocket availability and connection info."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        ws_available = socketio is not None
        return jsonify({
            'available': ws_available,
            'namespace': '/tickets' if ws_available else None,
            'events': {
                'ticket_created': 'Emitted when a new ticket is created',
                'ticket_updated': 'Emitted when a ticket is updated',
                'ticket_completed': 'Emitted when a ticket is marked complete',
                'ticket_deleted': 'Emitted when a ticket is deleted',
            } if ws_available else {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/ai-status', methods=['GET'])
    def api_ai_status():
        """Return AI provider status, defaults, and recent feedback."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        try:
            config = load_config(fail_fast=False)
            selection = resolve_provider_selection(config.ai_provider, config.ai_model)
            ai_client = get_ai_client()
            status = ai_client.get_status(selection)
            context_manager = get_ai_context_manager()
            status.update({
                "memory_available": context_manager.memory_available(),
                "vector_available": context_manager.vector_available(),
                "memory_provider": config.ai_memory_provider,
                "vector_provider": config.ai_vector_store_provider,
                "vector_store_path": config.ai_vector_store_path,
                "memory_enabled": config.ai_memory_enabled,
                "vector_enabled": config.ai_vector_store_enabled,
            })
            status.update({
                "ai_enabled": config.ai_enabled,
                "feedback_log": _collect_ai_feedback(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return jsonify(status)
        except Exception as exc:
            record_error(
                message=f"AI status endpoint failed: {exc}",
                source="api.py:api_ai_status",
                priority=TicketPriority.P2,
            )
            return jsonify({
                "error": "Failed to load AI status",
                "details": str(exc),
            }), 500

    @app.route('/api/settings', methods=['GET'])
    def api_get_settings():
        """Get current AI settings (API key is masked for security)."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        config = load_config(fail_fast=False)

        api_key = config.ai_api_key
        if api_key and len(api_key) > 8:
            masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        elif api_key:
            masked_key = '*' * len(api_key)
        else:
            masked_key = ''

        return jsonify({
            'ai_provider': config.ai_provider,
            'ai_api_key': masked_key,
            'ai_model': config.ai_model,
            'ai_enabled': config.ai_enabled,
        })

    @app.route('/api/settings', methods=['POST'])
    def api_update_settings():
        """Update AI settings."""
        # Require authentication (no local bypass for mutations)
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401
        
        try:
            data = request.get_json()

            if not data:
                return jsonify({'error': 'No data provided'}), 400

            config = get_config()

            if 'ai_provider' in data:
                config.ai_provider = data['ai_provider']
            if 'ai_api_key' in data:
                config.ai_api_key = data['ai_api_key']
            if 'ai_model' in data:
                config.ai_model = data['ai_model']
            if 'ai_enabled' in data:
                config.ai_enabled = bool(data['ai_enabled'])

            set_config(config)

            os.environ['ACTIFIX_AI_PROVIDER'] = config.ai_provider
            os.environ['ACTIFIX_AI_API_KEY'] = config.ai_api_key
            os.environ['ACTIFIX_AI_MODEL'] = config.ai_model
            os.environ['ACTIFIX_AI_ENABLED'] = '1' if config.ai_enabled else '0'

            return jsonify({
                'success': True,
                'message': 'Settings updated successfully',
            })
        except Exception as e:
            record_error(
                message=f"Settings update failed: {e}",
                source="api.py:api_update_settings",
                priority=TicketPriority.P2,
            )
            return jsonify({
                'error': str(e)
            }), 500

    @app.route('/api/ideas', methods=['POST'])
    def api_ideas():
        """Process user idea into AI-enriched ticket."""
        # Require authentication (no local bypass for mutations)
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401
        
        try:
            data = request.get_json()
            idea = data.get('idea', '').strip()
            if not idea:
                return jsonify({'error': 'Idea text required'}), 400

            paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])

            # Dummy ticket info for AI analysis
            dummy_ticket = {
                'id': 'IDEA-GUI',
                'priority': 'P3',
                'error_type': 'feature_request',
                'message': idea,
                'source': 'gui_ideas',
                'stack_trace': '',
            }

            # Use AI to generate detailed analysis/remediation notes
            ai_client = get_ai_client()
            ai_response = ai_client.generate_fix(dummy_ticket)

            ai_notes = ai_response.content if ai_response.success else f"AI analysis unavailable: {ai_response.error}"

            # Create enriched ticket
            from .raise_af import record_error, TicketPriority
            stack_trace = capture_stack_trace()
            base_message = f"User Feature Request: {idea}"
            clean_message = _ensure_structured_message(base_message) if STRUCTURED_MESSAGE_ENFORCED else base_message
            duplicate_guard = generate_duplicate_guard(
                "gui_ideas",
                clean_message,
                "feature_request",
                stack_trace,
            )

            from .persistence.ticket_repo import get_ticket_repository
            repo = get_ticket_repository()
            existing = repo.check_duplicate_guard(duplicate_guard)
            if existing:
                preview = ai_notes[:150] + '...' if len(ai_notes) > 150 else ai_notes
                return jsonify({
                    'success': True,
                    'ticket_id': existing.get('id'),
                    'priority': existing.get('priority', 'P3'),
                    'preview': preview,
                    'duplicate': True,
                    'ai_provider': ai_response.provider.value if ai_response.provider else 'none',
                })

            entry = record_error(
                message=clean_message,
                source="gui_ideas",
                run_label="dashboard",
                error_type="feature_request",
                priority=TicketPriority.P3,
                paths=paths,
                skip_ai_notes=True,  # Use our custom notes
                skip_duplicate_check=True,
                stack_trace=stack_trace,
            )

            if not entry:
                return jsonify({'error': 'Failed to create ticket (possible duplicate)'}), 500

            # Update with AI notes
            repo.update_ticket(entry.entry_id, {
                'ai_remediation_notes': ai_notes[:4000],  # Truncate if needed
                'message': f"User Idea → AI Expanded\n\nOriginal: {idea}\n\nAI Analysis:\n{ai_notes[:500]}...",
            })

            preview = ai_notes[:150] + '...' if len(ai_notes) > 150 else ai_notes

            # Emit WebSocket event for ticket creation
            emit_ticket_event('ticket_created', {
                'ticket_id': entry.entry_id,
                'priority': entry.priority.value,
                'message': idea[:100],
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })

            return jsonify({
                'success': True,
                'ticket_id': entry.entry_id,
                'priority': entry.priority.value,
                'preview': preview,
                'ai_provider': ai_response.provider.value if ai_response.provider else 'none',
            })
        except Exception as e:
            record_error(
                message=f"Ideas endpoint failed: {e}",
                source="api.py:api_ideas",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ingest/sentry', methods=['POST'])
    def api_ingest_sentry():
        """
        Sentry-style error ingestion endpoint.

        Accepts Sentry event format and creates Actifix tickets.
        Compatible with Sentry SDK error reporting.
        """
        # Check authentication (local-only default)
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        try:
            # Parse Sentry event from request
            event = request.get_json()

            if not event:
                return jsonify({'error': 'No event data provided'}), 400

            # Ingest event and create ticket
            from .ingestion import ingest_sentry_event

            ticket_id = ingest_sentry_event(event)

            if ticket_id:
                return jsonify({
                    'success': True,
                    'ticket_id': ticket_id,
                    'event_id': event.get('event_id', 'unknown'),
                }), 201
            else:
                # Duplicate or ingestion failed
                return jsonify({
                    'success': False,
                    'reason': 'duplicate_or_failed',
                    'event_id': event.get('event_id', 'unknown'),
                }), 200

        except Exception as e:
            record_error(
                message=f"Sentry ingestion endpoint failed: {e}",
                source="api.py:api_ingest_sentry",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cleanup', methods=['POST'])
    def api_cleanup():
        """Run ticket cleanup with retention policies."""
        # Require authentication (no local bypass for mutations)
        if not _require_auth(request):
            return jsonify({'error': 'Authorization required (admin password)'}), 401
        
        try:
            data = request.get_json() or {}

            config = get_cleanup_config()
            retention_days = data.get('retention_days', config.retention_days)
            test_retention_days = data.get('test_retention_days', config.test_ticket_retention_days)
            auto_complete = data.get('auto_complete_test_tickets', config.auto_complete_test_tickets)
            dry_run = data.get('dry_run', True)

            results = run_automatic_cleanup(
                retention_days=retention_days,
                test_ticket_retention_days=test_retention_days,
                auto_complete_test_tickets=auto_complete,
                dry_run=dry_run
            )

            return jsonify({
                'success': True,
                'results': results,
            })
        except Exception as e:
            record_error(
                message=f"Cleanup failed: {e}",
                source="api.py:api_cleanup",
                priority=TicketPriority.P2,
            )
            return jsonify({
                'error': str(e)
            }), 500

    @app.route('/api/cleanup/config', methods=['GET'])
    def api_cleanup_config():
        """Get cleanup configuration."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401
        
        try:
            config = get_cleanup_config()
            return jsonify({
                'success': True,
                'config': config.to_dict(),
            })
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500

    @app.route('/api/auth/login', methods=['POST'])
    def api_auth_login():
        """Authenticate user and return token."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            from actifix.security.auth import get_user_manager
            user_manager = get_user_manager()
            
            try:
                user, token = user_manager.authenticate_user(username, password)
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'user_id': user.user_id,
                        'username': user.username,
                        'roles': [r.value for r in user.roles],
                        'is_active': user.is_active
                    }
                })
            except Exception as auth_error:
                return jsonify({'error': str(auth_error)}), 401
        except Exception as e:
            record_error(
                message=f"Login failed: {e}",
                source="api.py:api_auth_login",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': str(e)}), 500

    @app.route('/api/auth/create-first-user', methods=['POST'])
    def api_auth_create_first_user():
        """Create first admin user if no users exist."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            from actifix.security.auth import get_user_manager, AuthRole
            user_manager = get_user_manager()
            
            # Check if any users exist
            try:
                # Try to get any user to check if database exists
                # This is a simplified check - in production you'd query the database
                test_user = user_manager.get_user('admin')
                if test_user:
                    return jsonify({'error': 'Admin user already exists'}), 409
            except Exception:
                pass  # No users exist yet
            
            # Create first admin user
            try:
                user = user_manager.create_user(
                    user_id='admin',
                    username=username,
                    password=password,
                    roles={AuthRole.ADMIN}
                )
                
                # Generate token
                from actifix.security.auth import get_token_manager
                token_manager = get_token_manager()
                _, token = token_manager.create_token(user.user_id)
                
                return jsonify({
                    'success': True,
                    'message': 'First admin user created successfully',
                    'token': token,
                    'user': {
                        'user_id': user.user_id,
                        'username': user.username,
                        'roles': [r.value for r in user.roles],
                        'is_active': user.is_active
                    }
                })
            except Exception as create_error:
                return jsonify({'error': f'Failed to create user: {create_error}'}), 500
        except Exception as e:
            record_error(
                message=f"Create first user failed: {e}",
                source="api.py:api_auth_create_first_user",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': str(e)}), 500


    @app.route('/api/auth/verify-password', methods=['POST'])
    def api_auth_verify_password():
        """Test admin password validity."""
        data = request.get_json() or {}
        password = data.get('password', '')
        if not password:
            return jsonify({'valid': False, 'error': 'Password required'}), 400

        if _verify_admin_password(password):
            return jsonify({'valid': True})
        else:
            return jsonify({'valid': False, 'error': 'Invalid password'}), 401

    @app.route('/api/schema/tickets', methods=['GET'])
    def api_schema_tickets():
        """Export JSON Schema for ticket data structure."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        try:
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Actifix Ticket",
                "description": "Ticket data structure for Actifix error management system",
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique ticket identifier (e.g., ACT-20260125-ABC12)"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["P0", "P1", "P2", "P3", "P4"],
                        "description": "Priority level (P0=critical/1hr, P1=high/4hr, P2=medium/24hr, P3=low/72hr, P4=minimal/1wk)"
                    },
                    "error_type": {
                        "type": "string",
                        "description": "Type of issue (Feature, BugFix, Refactor, etc.)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable ticket message/description"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source location (file:line or module:function)"
                    },
                    "run_label": {
                        "type": ["string", "null"],
                        "description": "Runtime environment label (e.g., production-api, test)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Open", "In Progress", "Completed"],
                        "description": "Current ticket status"
                    },
                    "priority_level": {
                        "type": "integer",
                        "description": "Numeric priority (0=P0, 1=P1, etc.) for sorting"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 creation timestamp"
                    },
                    "updated_at": {
                        "type": ["string", "null"],
                        "format": "date-time",
                        "description": "ISO 8601 last update timestamp"
                    },
                    "stack_trace": {
                        "type": ["string", "null"],
                        "description": "Full stack trace if applicable"
                    },
                    "ai_remediation_notes": {
                        "type": ["string", "null"],
                        "description": "AI-generated analysis and remediation suggestions"
                    },
                    "completion_summary": {
                        "type": ["string", "null"],
                        "description": "Summary of how ticket was resolved"
                    },
                    "documented": {
                        "type": "boolean",
                        "description": "Whether the issue is documented"
                    },
                    "functioning": {
                        "type": "boolean",
                        "description": "Whether the fix is functioning correctly"
                    },
                    "tested": {
                        "type": "boolean",
                        "description": "Whether the fix has been tested"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Whether the ticket is complete"
                    }
                },
                "required": ["id", "priority", "error_type", "message", "source", "status"]
            }
            return jsonify(schema)
        except Exception as e:
            record_error(
                message=f"Failed to export ticket schema: {e}",
                source="api.py:api_schema_tickets",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': 'Failed to export schema'}), 500

    @app.route('/api/schema/events', methods=['GET'])
    def api_schema_events():
        """Export JSON Schema for event data structure."""
        # Check authentication
        if not _check_auth(request):
            return jsonify({'error': 'Authorization required'}), 401

        try:
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Actifix Event",
                "description": "Event log entry in Actifix system",
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Unique event identifier"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["audit", "setup", "error"],
                        "description": "Event type classification"
                    },
                    "message": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 event timestamp"
                    },
                    "details": {
                        "type": ["object", "null"],
                        "description": "Additional structured event metadata"
                    }
                },
                "required": ["id", "type", "message", "timestamp"]
            }
            return jsonify(schema)
        except Exception as e:
            record_error(
                message=f"Failed to export event schema: {e}",
                source="api.py:api_schema_events",
                priority=TicketPriority.P2,
            )
            return jsonify({'error': 'Failed to export schema'}), 500

    return app


def run_api_server(
    host: str = '127.0.0.1',
    port: int = 5001,
    project_root: Optional[Path] = None,
    debug: bool = False,
) -> None:
    """
    Run the API server.

    Args:
        host: Host to bind to.
        port: Port to bind to.
        project_root: Optional project root path.
        debug: Enable debug mode.
    """
    app = create_app(project_root, host=host, port=port)
    registry = app.extensions.get("actifix_module_registry")
    socketio = app.extensions.get("socketio")
    try:
        if socketio is not None:
            socketio.run(app, host=host, port=port, debug=debug)
        else:
            app.run(host=host, port=port, debug=debug, threaded=True)
    finally:
        if isinstance(registry, ModuleRegistry):
            registry.shutdown()


if __name__ == '__main__':
    run_api_server(debug=True)
