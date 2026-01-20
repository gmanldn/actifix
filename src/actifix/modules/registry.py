"""Module registry with lifecycle hook support."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Optional

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error


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
    """Track registered modules and invoke lifecycle hooks.

    Supported module-level hooks (optional):
    - module_register(context=..., app=..., blueprint=...)
    - module_unregister(context=...)
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._registered: dict[str, tuple[object, ModuleRuntimeContext]] = {}
        self._shutdown = False

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

