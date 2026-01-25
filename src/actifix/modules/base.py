#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared module utilities (config, paths, logging, error capture, health helpers)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error, redact_secrets_from_text
from actifix.state_paths import get_actifix_paths

from .config import get_module_config


@dataclass
class ModuleAnchor:
    module_key: str
    defaults: Mapping[str, object]
    metadata: Mapping[str, object]
    project_root: Optional[Path]


class ModuleBase:
    """Minimal helper for modules that share config, logging, and error capture."""

    def __init__(
        self,
        module_key: str,
        defaults: Mapping[str, object],
        metadata: Mapping[str, object],
        *,
        project_root: Optional[str | Path] = None,
    ) -> None:
        self.anchor = ModuleAnchor(
            module_key=module_key,
            defaults=defaults,
            metadata=metadata,
            project_root=Path(project_root).resolve() if project_root else None,
        )

    @property
    def module_key(self) -> str:
        return self.anchor.module_key

    @property
    def module_id(self) -> str:
        name = str(self.anchor.metadata.get("name") or "").strip()
        if name:
            return name
        return f"modules.{self.module_key}"

    @property
    def module_defaults(self) -> Mapping[str, object]:
        return self.anchor.defaults

    @property
    def project_root(self) -> Optional[Path]:
        return self.anchor.project_root

    def resolve_host_port(
        self,
        host: str | None,
        port: int | None,
    ) -> Tuple[str, int]:
        config = get_module_config(
            self.module_key,
            self.module_defaults,
            project_root=self.project_root,
        )
        resolved_host = host or str(config.get("host", self.module_defaults.get("host", "127.0.0.1")))
        resolved_port_value = port or config.get("port", self.module_defaults.get("port", 0))
        try:
            resolved_port = int(resolved_port_value or 0)
        except (TypeError, ValueError):
            resolved_port = int(self.module_defaults.get("port") or 0)
        return resolved_host, resolved_port

    def get_paths(self):
        """Return Actifix paths for the configured project root."""
        return get_actifix_paths(project_root=self.project_root)

    def health_response(self) -> dict[str, object]:
        """Default health route helper."""
        if os.environ.get("ACTIFIX_MODULE_HEALTH_MINIMAL") == "1":
            return {"status": "ok"}
        return {
            "status": "ok",
            "module": self.module_key,
            "module_id": self.module_id,
        }

    def log_gui_init(
        self,
        host: str,
        port: int,
        *,
        event_name: str | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        """Log the module GUI configuration event."""
        paths = self.get_paths()
        payload = {
            "module": self.module_key,
            "module_id": self.module_id,
            "host": host,
            "port": port,
            "state_dir": str(paths.state_dir),
        }
        if extra:
            payload.update(extra)
        log_event(
            event_name or f"{self.module_key.upper()}_GUI_INIT",
            f"{self.module_key} GUI configured",
            extra=payload,
            source=f"modules.{self.module_key}:ModuleBase.log_gui_init",
        )

    def _run_label(self, override: str | None = None) -> str:
        if override:
            return override
        return f"{self.module_key}-gui"

    def record_module_error(
        self,
        message: str,
        *,
        source: str,
        run_label: str | None = None,
        error_type: str = "ModuleError",
        priority: TicketPriority | str = TicketPriority.P2,
    ) -> None:
        """Record a sanitized module error with a default run label."""
        safe_message = redact_secrets_from_text(message)
        record_error(
            message=safe_message,
            source=source,
            run_label=self._run_label(run_label),
            error_type=error_type,
            priority=priority,
        )
