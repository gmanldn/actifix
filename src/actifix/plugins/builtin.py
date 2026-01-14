"""A built-in plugin used to validate the entry-point loader."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from .protocol import Plugin, PluginHealthStatus, PluginMetadata
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class CorePlugin(Plugin):
    """A self-testing plugin shipped with Actifix."""

    metadata = PluginMetadata(
        name="actifix-core-plugin",
        version="1.0.0",
        description="Built-in plugin that exercises the plugin loader and lifecycle hooks.",
        author="Actifix System",
        capabilities={"self_test": True},
    )

    def __init__(self) -> None:
        self._registry: PluginRegistry | None = None
        self._registered_at: datetime | None = None

    def register(self, app: Any, registry: PluginRegistry) -> None:
        self._registry = registry
        self._registered_at = datetime.now(timezone.utc)
        logger.info("%s registered at %s", self.metadata.name, self._registered_at.isoformat())

    def unregister(self) -> None:
        logger.info("Unregistering %s", self.metadata.name)
        self._registry = None
        self._registered_at = None

    def health(self) -> PluginHealthStatus:
        healthy = self._registry is not None
        details = "active" if healthy else "disabled"
        return PluginHealthStatus(
            plugin_name=self.metadata.name,
            healthy=healthy,
            checked_at=datetime.now(timezone.utc),
            details=details,
        )


__all__ = ["CorePlugin"]
