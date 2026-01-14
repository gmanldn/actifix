"""Plugin registry implementation."""

from __future__ import annotations

from collections import OrderedDict
from types import TracebackType
from threading import RLock
from typing import Any, Dict, Iterator, Optional

from .protocol import Plugin, PluginMetadata


class PluginState:
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"


class PluginRegistry:
    """Thread-safe registry responsible for tracking plugin lifecycle."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._plugins: Dict[str, Plugin] = OrderedDict()
        self._state: Dict[str, str] = {}

    def register(self, plugin: Plugin, app: Any, **metadata: Any) -> None:
        """Register the plugin and trigger its lifecycle hooks."""
        with self._lock:
            name = metadata.get("name", plugin.metadata.name)
            if name in self._plugins:
                raise RuntimeError(f"Plugin '{name}' already registered")

            plugin.register(app, self)
            self._plugins[name] = plugin
            self._state[name] = PluginState.ENABLED

    def unregister(self, plugin_name: str) -> None:
        """Unregister the plugin and call its cleanup hook."""
        with self._lock:
            plugin = self._plugins.pop(plugin_name, None)
            if plugin is None:
                raise KeyError(f"Plugin '{plugin_name}' is not registered")

            plugin.unregister()
            self._state.pop(plugin_name, None)

    def get(self, plugin_name: str) -> Plugin:
        with self._lock:
            return self._plugins[plugin_name]

    def __iter__(self) -> Iterator[Plugin]:
        with self._lock:
            yield from list(self._plugins.values())


class PluginContextManager:
    """Context manager helper for temporary plugin deloyments."""

    def __init__(self, registry: PluginRegistry, plugin_name: str, plugin: Plugin):
        self.registry = registry
        self.plugin_name = plugin_name
        self.plugin = plugin

    def __enter__(self) -> Plugin:
        self.registry.register(self.plugin, app=None, name=self.plugin_name)
        return self.plugin

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.registry.unregister(self.plugin_name)
