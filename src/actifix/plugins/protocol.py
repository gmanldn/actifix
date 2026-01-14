"""Plugin protocol definitions and metadata contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class PluginMetadata:
    """Static metadata every plugin must expose."""

    name: str
    version: str
    description: str
    author: Optional[str] = None
    capabilities: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class PluginHealthStatus:
    """Health signal produced by plugins."""

    plugin_name: str
    healthy: bool
    checked_at: datetime
    details: Optional[str] = None


@runtime_checkable
class Plugin(Protocol):
    """Minimal plugin contract for Actifix extension points."""

    metadata: PluginMetadata

    def register(self, app: Any, registry: "PluginRegistry") -> None:
        """Hook called when the plugin is registered to the host app."""
        ...

    def unregister(self) -> None:
        """Hook called when the plugin is removed from the host app."""
        ...

    def health(self) -> Optional[PluginHealthStatus]:
        """Optional health signal to describe current plugin state."""
        ...


class PluginRegistry(Protocol):  # pragma: no cover - used for typing hints
    def register(self, plugin: Plugin, app: Any, **metadata: Any) -> None:
        ...

    def unregister(self, plugin_name: str) -> None:
        ...
