"""Plugin isolation helpers."""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any

from .protocol import Plugin
from .registry import PluginRegistry
from .validation import validate_plugin
from ..raise_af import record_error, TicketPriority

logger = logging.getLogger(__name__)


class PluginSandbox:
    """Gracefully handle plugin errors during lifecycle transitions."""

    def __init__(self, name: str) -> None:
        self.name = name

    def safe_register(self, plugin: Plugin, app: Any, registry: PluginRegistry) -> None:
        try:
            registry.register(plugin, app, name=self.name)
            logger.info("Plugin '%s' registered", self.name)
        except Exception as exc:
            self.record_error(f"Failed to register plugin '{self.name}'", exc)
            raise

    def record_error(self, message: str, exc: BaseException) -> None:
        logger.error("%s: %s", message, exc)
        record_error(
            message=message,
            source="PluginSandbox",
            error_type="PluginLoadError",
            run_label="plugin-architecture",
            priority=TicketPriority.P1,
            skip_duplicate_check=True,
            skip_ai_notes=True,
            capture_context=False
        )
