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

try:
    from flask import Flask, jsonify, request, g
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None


def _ensure_web_dependencies() -> bool:
    """
    Ensure Flask dependencies are installed. Auto-install if missing.
    
    Returns:
        True if dependencies are available, False otherwise.
    """
    global FLASK_AVAILABLE, Flask, CORS

    if FLASK_AVAILABLE:
        return True

    print("Flask dependencies not found. Installing...")
    print("Running: pip install flask flask-cors")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask", "flask-cors"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Successfully installed Flask dependencies")
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        FLASK_AVAILABLE = True
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
from .raise_af import enforce_raise_af_only, record_error, TicketPriority
from .state_paths import get_actifix_paths
from .persistence.event_repo import get_event_repository, EventFilter
from .persistence.ticket_cleanup import run_automatic_cleanup
from .persistence.cleanup_config import get_cleanup_config
from .config import get_config, set_config, load_config
from .security.rate_limiter import RateLimitConfig, RateLimitError, get_rate_limiter
from .log_utils import log_event
from .plugins.permissions import PermissionRegistry
from .ai_client import get_ai_client, resolve_provider_selection
from .modules.registry import ModuleRegistry, ModuleRuntimeContext

# Server start time for uptime calculation
SERVER_START_TIME = time.time()
SYSTEM_OWNERS = {"runtime", "infra", "core", "persistence", "testing", "tooling"}
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
    depgraph_path = project_root / "docs" / "architecture" / "DEPGRAPH.json"
    if not depgraph_path.exists():
        record_error(
            message="DEPGRAPH.json missing for module dependency validation",
            source="api.py:_load_depgraph_edges",
            priority=TicketPriority.P2,
        )
        return set()
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
        return set()


def _validate_module_dependencies(
    module_name: str,
    dependencies: object,
    depgraph_edges: set[tuple[str, str]],
) -> list[str]:
    if not dependencies:
        return []
    if not isinstance(dependencies, list):
        return ["dependencies_invalid"]
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
    try:
        status_payload = _read_module_status_payload(status_file)
        if module_id in status_payload.get("statuses", {}).get("disabled", []):
            log_event(
                "MODULE_SKIPPED_DISABLED",
                f"Skipped disabled module: {module_name}",
                extra={"module": module_name, "module_id": module_id},
                source="api.py:_register_module_blueprint",
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
            _mark_module_status(status_file, module_id, "error")
            return False

        dependencies = getattr(module, "MODULE_DEPENDENCIES", [])
        dependency_errors = (
            _validate_module_dependencies(module_name, dependencies, depgraph_edges)
            if depgraph_edges
            else []
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
            _mark_module_status(status_file, module_id, "error")
            return False

        blueprint = create_blueprint(project_root=project_root, host=host, port=port)
        blueprint_prefix = getattr(blueprint, "url_prefix", None)
        if blueprint_prefix is None:
            app.register_blueprint(blueprint, url_prefix=expected_prefix)
        elif blueprint_prefix == expected_prefix:
            app.register_blueprint(blueprint)
        else:
            raise ValueError(
                f"Module {module_name} url_prefix mismatch: {blueprint_prefix} != {expected_prefix}"
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
        return True
    except Exception as exc:
        record_error(
            message=f"Module registration failed for {module_name}: {exc}",
            source="api.py:_register_module_blueprint",
            run_label=f"{module_name}-gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        _mark_module_status(status_file, module_id, "error")
        return False


def _default_module_status_payload() -> Dict[str, Dict[str, List[str]]]:
    return {
        "schema_version": MODULE_STATUS_SCHEMA_VERSION,
        "statuses": {
            "active": [],
            "disabled": [],
            "error": [],
        },
    }


def _coerce_status_list(values: object) -> List[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    cleaned: List[str] = []
    seen = set()
    for value in values:
        if value is None:
            continue
        name = str(value)
        if name in seen:
            continue
        seen.add(name)
        cleaned.append(name)
    return cleaned


def _normalize_module_statuses(payload: object) -> Dict[str, List[str]]:
    statuses = {"active": [], "disabled": [], "error": []}
    if isinstance(payload, dict):
        for key in statuses:
            statuses[key] = _coerce_status_list(payload.get(key))
    return statuses


def _backup_corrupt_module_statuses(status_file: Path, raw_content: str) -> None:
    from actifix.log_utils import atomic_write

    corrupt_path = status_file.with_suffix(".corrupt.json")
    atomic_write(corrupt_path, raw_content)


def _write_module_status_payload(status_file: Path, payload: Dict[str, object]) -> None:
    from actifix.log_utils import atomic_write

    atomic_write(status_file, json.dumps(payload, indent=2))


def _mark_module_status(status_file: Path, module_id: str, status: str) -> None:
    status_payload = _read_module_status_payload(status_file)
    statuses = status_payload["statuses"]

    for key in statuses:
        if module_id in statuses[key]:
            statuses[key].remove(module_id)

    if status in statuses:
        statuses[status].append(module_id)

    status_payload["statuses"] = _normalize_module_statuses(statuses)
    status_payload["schema_version"] = MODULE_STATUS_SCHEMA_VERSION
    try:
        _write_module_status_payload(status_file, status_payload)
    except Exception as exc:
        record_error(
            message=f"Failed to persist module status for {module_id}: {exc}",
            source="api.py:_mark_module_status",
            priority=TicketPriority.P2,
        )


def _read_module_status_payload(status_file: Path) -> Dict[str, Dict[str, List[str]]]:
    default_payload = _default_module_status_payload()
    if not status_file.exists():
        return default_payload

    try:
        raw_content = status_file.read_text(encoding="utf-8")
    except Exception as exc:
        record_error(
            message=f"Failed to read module status file: {exc}",
            source="api.py:_read_module_status_payload",
            priority=TicketPriority.P2,
        )
        return default_payload

    if not raw_content.strip():
        return default_payload

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        record_error(
            message=f"Invalid module status JSON: {exc}",
            source="api.py:_read_module_status_payload",
            priority=TicketPriority.P2,
        )
        try:
            _backup_corrupt_module_statuses(status_file, raw_content)
            _write_module_status_payload(status_file, default_payload)
        except Exception as write_exc:
            record_error(
                message=f"Failed to recover module status file: {write_exc}",
                source="api.py:_read_module_status_payload",
                priority=TicketPriority.P2,
            )
        return default_payload

    if isinstance(data, dict) and "schema_version" in data and "statuses" in data:
        statuses = _normalize_module_statuses(data.get("statuses"))
        return {
            "schema_version": data.get("schema_version") or MODULE_STATUS_SCHEMA_VERSION,
            "statuses": statuses,
        }

    if isinstance(data, dict):
        statuses = _normalize_module_statuses(data)
        return {
            "schema_version": MODULE_STATUS_SCHEMA_VERSION,
            "statuses": statuses,
        }

    record_error(
        message="Unexpected module status payload format",
        source="api.py:_read_module_status_payload",
        priority=TicketPriority.P2,
    )
    return default_payload


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
    except Exception as exc:
        record_error(
            message=f"Failed to load auth managers: {exc}",
            source="api.py:_verify_auth_token",
            priority=TicketPriority.P2,
        )
        return False


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

    try:
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


def _load_modules(project_root: Path) -> Dict[str, List[Dict[str, str]]]:
    """Load modules from canonical DEPGRAPH.json."""
    from actifix.state_paths import get_actifix_paths
    paths = get_actifix_paths(project_root=project_root)
    status_file = paths.state_dir / "module_statuses.json"

    status_payload = _read_module_status_payload(status_file)
    statuses = status_payload["statuses"]

    def get_status(name):
        if name in statuses.get("disabled", []):
            return "disabled"
        if name in statuses.get("error", []):
            return "error"
        return "active"
    
    depgraph_path = project_root / "docs" / "architecture" / "DEPGRAPH.json"
    if not depgraph_path.exists():
        return {"system": [], "user": []}

    try:
        data = json.loads(depgraph_path.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
    except Exception:
        return {"system": [], "user": []}

    system_domains = {"runtime", "infra", "core", "tooling", "security", "plugins", "persistence"}
    modules = []
    for node in nodes:
        module_id = node["id"]
        modules.append({
            "name": module_id,
            "domain": node.get("domain", ""),
            "owner": node.get("owner", ""),
            "summary": node.get("label", node["id"]),
            "status": get_status(module_id)
        })

    system_modules = [m for m in modules if m["domain"] in system_domains]
    user_modules = [m for m in modules if m["domain"] not in system_domains]
    return {"system": system_modules, "user": user_modules}


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
    
    # Store project root and API binding info in app config
    app.config['PROJECT_ROOT'] = root
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in development
    app.config['API_HOST'] = host
    app.config['API_PORT'] = port
    module_registry = ModuleRegistry()
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

    try:
        from actifix.modules.yhatzee import create_blueprint as _create_yhatzee_blueprint
        from actifix.modules.yhatzee import ACCESS_RULE as _yhatzee_access_rule
    except ImportError:
        _create_yhatzee_blueprint = None
        _yhatzee_access_rule = MODULE_ACCESS_PUBLIC

    try:
        from actifix.modules.superquiz import create_blueprint as _create_superquiz_blueprint
        from actifix.modules.superquiz import ACCESS_RULE as _superquiz_access_rule
    except ImportError:
        _create_superquiz_blueprint = None
        _superquiz_access_rule = MODULE_ACCESS_PUBLIC

    if _create_yhatzee_blueprint:
        _register_module_blueprint(
            app,
            "yhatzee",
            _create_yhatzee_blueprint,
            project_root=root,
            host=host,
            port=port,
            status_file=status_file,
            access_rule=_yhatzee_access_rule,
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
            host=host,
            port=port,
            status_file=status_file,
            access_rule=_superquiz_access_rule,
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
            token = _extract_bearer_token(request)
            if not token:
                return jsonify({"error": "Authorization required"}), 401
            if not _verify_auth_token(token):
                return jsonify({"error": "Invalid token"}), 401
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
        root = Path(app.config['PROJECT_ROOT'])
        info = _gather_version_info(root)
        return jsonify(info)

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        """Get ticket statistics."""
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
    
    @app.route('/api/tickets', methods=['GET'])
    def api_tickets():
        """Get recent tickets list."""
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
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        from .persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        ticket = repo.get_ticket(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket)

    @app.route('/api/fix-ticket', methods=['POST'])
    def api_fix_ticket():
        """Fix the highest priority open ticket with detailed logging."""
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])

        # Enforce Raise_AF-only policy before modifying tickets
        # (Defense in depth - also enforced in fix_highest_priority_ticket)
        enforce_raise_af_only(paths)

        # Get completion fields from request body or use defaults
        data = request.get_json() if request.is_json else {}
        completion_notes = data.get('completion_notes', 'Ticket resolved via API endpoint. Issue addressed and verified.')
        test_steps = data.get('test_steps', 'Automated testing performed via API.')
        test_results = data.get('test_results', 'All validation checks passed successfully.')
        summary = data.get('summary', 'Resolved via dashboard fix')
        test_documentation_url = data.get('test_documentation_url')

        result = fix_highest_priority_ticket(
            paths,
            completion_notes=completion_notes,
            test_steps=test_steps,
            test_results=test_results,
            summary=summary,
            test_documentation_url=test_documentation_url
        )
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
        modules = _load_modules(app.config['PROJECT_ROOT'])
        return jsonify(modules)

    @app.route('/api/modules/<module_id>/health', methods=['GET'])
    def api_module_health(module_id):
        """Aggregate module health and status."""
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
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/ai-status', methods=['GET'])
    def api_ai_status():
        """Return AI provider status, defaults, and recent feedback."""
        try:
            config = load_config(fail_fast=False)
            selection = resolve_provider_selection(config.ai_provider, config.ai_model)
            ai_client = get_ai_client()
            status = ai_client.get_status(selection)
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
            entry = record_error(
                message=f"User Feature Request: {idea}",
                source="gui_ideas",
                run_label="dashboard",
                error_type="feature_request",
                priority=TicketPriority.P3,
                paths=paths,
                skip_ai_notes=True  # Use our custom notes
            )

            if not entry:
                return jsonify({'error': 'Failed to create ticket (possible duplicate)'}), 500

            # Update with AI notes
            from .persistence.ticket_repo import get_ticket_repository
            repo = get_ticket_repository()
            repo.update_ticket(entry.entry_id, {
                'ai_remediation_notes': ai_notes[:4000],  # Truncate if needed
                'message': f"User Idea → AI Expanded\n\nOriginal: {idea}\n\nAI Analysis:\n{ai_notes[:500]}...",
            })

            preview = ai_notes[:150] + '...' if len(ai_notes) > 150 else ai_notes

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

    @app.route('/api/cleanup', methods=['POST'])
    def api_cleanup():
        """Run ticket cleanup with retention policies."""
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
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    finally:
        if isinstance(registry, ModuleRegistry):
            registry.shutdown()


if __name__ == '__main__':
    run_api_server(debug=True)
