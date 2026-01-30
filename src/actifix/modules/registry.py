"""Module registry with lifecycle hook support."""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Optional

from actifix import log_utils
from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error
from actifix.state_paths import get_actifix_paths

MODULE_STATUS_SCHEMA_VERSION = "module-statuses.v1"
MODULE_STATUS_KEYS = {"active", "disabled", "error"}
MODULE_METADATA_REQUIRED_FIELDS = {
    "name",
    "version",
    "description",
    "capabilities",
    "data_access",
    "network",
    "permissions",
}
MODULE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
MODULE_ACCESS_RULES = {"public", "local-only", "auth-required"}


def _default_module_status_payload() -> dict[str, Any]:
    return {
        "schema_version": MODULE_STATUS_SCHEMA_VERSION,
        "statuses": {
            "active": [],
            "disabled": [],
            "error": [],
        },
    }


def _coerce_status_list(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    cleaned: list[str] = []
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


def _normalize_module_statuses(payload: object) -> dict[str, list[str]]:
    statuses = {key: [] for key in MODULE_STATUS_KEYS}
    if isinstance(payload, Mapping):
        for key in statuses:
            statuses[key] = _coerce_status_list(payload.get(key))
    return statuses


def _backup_corrupt_module_statuses(status_file: Path, raw_content: str) -> None:
    corrupt_path = status_file.with_suffix(".corrupt.json")
    log_utils.atomic_write(corrupt_path, raw_content)


def _read_module_status_payload(status_file: Path) -> dict[str, Any]:
    default_payload = _default_module_status_payload()
    if not status_file.exists():
        return default_payload

    try:
        raw_content = status_file.read_text(encoding="utf-8")
    except Exception as exc:
        record_error(
            message=f"Failed to read module status file: {exc}",
            source="modules.registry._read_module_status_payload",
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
            source="modules.registry._read_module_status_payload",
            priority=TicketPriority.P2,
        )
        _backup_corrupt_module_statuses(status_file, raw_content)
        try:
            _write_module_status_payload(status_file, default_payload)
        except Exception as write_exc:
            record_error(
                message=f"Failed to recover module status file: {write_exc}",
                source="modules.registry._read_module_status_payload",
                priority=TicketPriority.P2,
            )
        return default_payload

    if isinstance(data, dict):
        statuses = _normalize_module_statuses(data.get("statuses", data))
        schema_version = str(data.get("schema_version") or MODULE_STATUS_SCHEMA_VERSION)
        return {"schema_version": schema_version, "statuses": statuses}

    return default_payload


def _write_module_status_payload(status_file: Path, payload: dict[str, Any]) -> None:
    log_utils.atomic_write(status_file, json.dumps(payload, indent=2))


def _mark_module_status(status_file: Path, module_id: str, status: str) -> None:
    payload = _read_module_status_payload(status_file)
    statuses = payload["statuses"]

    for key in statuses:
        if module_id in statuses[key]:
            statuses[key].remove(module_id)

    if status in statuses:
        statuses[status].append(module_id)

    normalized = _normalize_module_statuses(statuses)
    updated = {
        **payload,
        "schema_version": MODULE_STATUS_SCHEMA_VERSION,
        "statuses": normalized,
    }
    _write_module_status_payload(status_file, updated)


def _discover_module_nodes(project_root: Path) -> list[dict[str, Any]]:
    depgraph_path = project_root / "docs" / "architecture" / "DEPGRAPH.json"
    if not depgraph_path.exists():
        return []

    try:
        data = json.loads(depgraph_path.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        return [
            node for node in nodes
            if isinstance(node, dict) and node.get("domain") == "modules"
        ]
    except Exception as exc:
        record_error(
            message=f"Failed to load DEPGRAPH.json: {exc}",
            source="modules.registry._discover_module_nodes",
            priority=TicketPriority.P2,
        )
        return []


def _lazy_import_module(module_label: str) -> tuple[str, object, Optional[dict[str, Any]]]:
    module_path = f"actifix.modules.{module_label}"
    module = importlib.import_module(module_path)
    metadata = getattr(module, "MODULE_METADATA", None)
    return module_path, module, metadata


def validate_module_metadata(module_label: str, metadata: Optional[dict[str, Any]]) -> list[str]:
    """Validate a module's metadata payload for release readiness."""
    errors: list[str] = []
    if not isinstance(metadata, dict):
        return ["metadata_missing"]

    missing = MODULE_METADATA_REQUIRED_FIELDS - set(metadata.keys())
    if missing:
        errors.append(f"missing_fields: {sorted(missing)}")

    name = metadata.get("name")
    expected_names = {f"modules.{module_label}", module_label}
    if not isinstance(name, str) or not name.strip():
        errors.append("name_invalid")
    elif name.strip() not in expected_names:
        errors.append("name_mismatch")

    version = metadata.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append("version_invalid")
    elif not MODULE_VERSION_PATTERN.match(version.strip()):
        errors.append("version_not_semver")

    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("description_invalid")

    for key in ("capabilities", "data_access", "network"):
        if not isinstance(metadata.get(key), dict):
            errors.append(f"{key}_invalid")

    permissions = metadata.get("permissions")
    if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
        errors.append("permissions_invalid")

    return errors


def validate_module_package(module_label: str, module: object, metadata: Optional[dict[str, Any]]) -> list[str]:
    """Validate module package exports and metadata."""
    errors = validate_module_metadata(module_label, metadata)

    defaults = getattr(module, "MODULE_DEFAULTS", None)
    if not isinstance(defaults, dict):
        errors.append("defaults_missing")
    else:
        if "host" not in defaults:
            errors.append("default_host_missing")
        if "port" not in defaults:
            errors.append("default_port_missing")

    access_rule = getattr(module, "ACCESS_RULE", None)
    if access_rule and access_rule not in MODULE_ACCESS_RULES:
        errors.append("access_rule_invalid")

    create_blueprint = getattr(module, "create_blueprint", None)
    if not callable(create_blueprint):
        errors.append("create_blueprint_missing")

    return errors


@dataclass(frozen=True)
class ModuleRuntimeContext:
    module_name: str
    module_id: str
    module_path: Optional[str]
    project_root: str
    host: str
    port: int


def _call_module_hook(module: object, hook_name: str, **kwargs: Any) -> None:
    hook = getattr(module, hook_name, None)
    if not callable(hook):
        return
    hook(**kwargs)


class ModuleRegistry:
    """Track registered modules, lifecycle hooks, and module metadata."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        status_file: Path | None = None,
    ) -> None:
        self._lock = RLock()
        self._registered: dict[str, tuple[object, ModuleRuntimeContext]] = {}
        self._shutdown = False
        paths = get_actifix_paths(project_root=project_root)
        self._project_root = project_root or paths.project_root
        self._status_file = status_file or (paths.state_dir / "module_statuses.json")
        self._status_payload = _read_module_status_payload(self._status_file)

    @property
    def status_file(self) -> Path:
        return self._status_file

    def statuses(self) -> dict[str, list[str]]:
        return self._status_payload["statuses"]

    def get_status(self, module_id: str) -> str:
        statuses = self.statuses()
        if module_id in statuses.get("disabled", []):
            return "disabled"
        if module_id in statuses.get("error", []):
            return "error"
        return "active"

    def mark_status(self, module_id: str, status: str) -> None:
        _mark_module_status(self._status_file, module_id, status)
        self._status_payload = _read_module_status_payload(self._status_file)

    def is_disabled(self, module_id: str) -> bool:
        return module_id in self.statuses().get("disabled", [])

    def discover_modules(self) -> list[dict[str, Any]]:
        return _discover_module_nodes(self._project_root)

    def registered_contexts(self) -> dict[str, "ModuleRuntimeContext"]:
        with self._lock:
            return {
                module_id: context
                for module_id, (_, context) in self._registered.items()
            }

    def registered_metadata(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            metadata_map: dict[str, dict[str, Any]] = {}
            for module_id, (module, _) in self._registered.items():
                metadata = getattr(module, "MODULE_METADATA", None)
                if isinstance(metadata, dict):
                    metadata_map[module_id] = metadata
            return metadata_map

    def import_module(self, module_label: str) -> tuple[str, object, Optional[dict[str, Any]]]:
        return _lazy_import_module(module_label)

    def on_registered(self, module: object, context: ModuleRuntimeContext, *, app: Any, blueprint: Any) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._registered[context.module_id] = (module, context)

        # Clear error status after successful registration
        current_status = self.get_status(context.module_id)
        if current_status == "error":
            self.mark_status(context.module_id, "active")
            log_event(
                "MODULE_STATUS_CLEARED",
                f"Module error status cleared after successful registration: {context.module_id}",
                extra={"module_id": context.module_id, "previous_status": "error", "new_status": "active"},
                source="modules.registry.ModuleRegistry.on_registered",
            )

        log_event(
            "MODULE_LIFECYCLE_REGISTERED",
            f"Module registered: {context.module_id}",
            extra={
                "module_id": context.module_id,
                "module_path": context.module_path,
                "host": context.host,
                "port": context.port,
            },
            source="modules.registry.ModuleRegistry.on_registered",
        )

        _call_module_hook(module, "module_register", context=context, app=app, blueprint=blueprint)

    def shutdown(self) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            items = list(self._registered.items())
            self._registered.clear()

        for module_id, (module, context) in reversed(items):
            try:
                _call_module_hook(module, "module_unregister", context=context)
                log_event(
                    "MODULE_LIFECYCLE_UNREGISTERED",
                    f"Module unregistered: {module_id}",
                    extra={"module_id": module_id, "module_path": context.module_path},
                    source="modules.registry.ModuleRegistry.shutdown",
                )
            except Exception as exc:
                record_error(
                    message=f"Module unregister hook failed for {module_id}: {exc}",
                    source="modules.registry.ModuleRegistry.shutdown",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                    capture_context=False,
                )
                raise
