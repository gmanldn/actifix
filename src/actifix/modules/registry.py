"""Module registry with lifecycle hook support."""

from __future__ import annotations

import importlib
import json
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

    def import_module(self, module_label: str) -> tuple[str, object, Optional[dict[str, Any]]]:
        return _lazy_import_module(module_label)

    def on_registered(self, module: object, context: ModuleRuntimeContext, *, app: Any, blueprint: Any) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._registered[context.module_id] = (module, context)

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
