"""Plugin registry implementation."""

from __future__ import annotations

import os
import re
from collections import OrderedDict
from types import TracebackType
from threading import RLock
from typing import Any, Dict, Iterator, Optional

from .protocol import Plugin, PluginMetadata
from ..log_utils import log_event


def _sanitize_identifier(value: str) -> str:
    """Sanitize identifier values (like usernames) to prevent injection."""
    if not value:
        return "unknown"
    value = value.strip()
    # Keep only alphanumeric and underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', value)
    return sanitized or "unknown"


def _get_user_context() -> str:
    """Get sanitized user context from environment."""
    user = os.environ.get("ACTIFIX_USER") or os.environ.get("USER")
    if user:
        return _sanitize_identifier(user)
    return "unknown"


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

    def register(self, plugin: Plugin, app: Any, user_context: Optional[str] = None, **metadata: Any) -> None:
        """Register the plugin and trigger its lifecycle hooks.

        Args:
            plugin: Plugin to register.
            app: Application instance.
            user_context: Optional user context (defaults to current system user).
            **metadata: Additional metadata (including 'name' for plugin name).
        """
        with self._lock:
            name = metadata.get("name", plugin.metadata.name)
            if name in self._plugins:
                raise RuntimeError(f"Plugin '{name}' already registered")

            # Get user context for audit logging (sanitized)
            if user_context is None:
                user_context = _get_user_context()
            else:
                user_context = _sanitize_identifier(user_context)

            try:
                plugin.register(app, self)
                self._plugins[name] = plugin
                self._state[name] = PluginState.ENABLED

                # Log plugin load with user context
                log_event(
                    "PLUGIN_LOADED",
                    f"Plugin loaded: {name}",
                    extra={
                        "plugin_name": name,
                        "user": user_context,
                        "plugin_version": getattr(plugin.metadata, "version", "unknown"),
                    }
                )
            except Exception as e:
                # Log plugin load failure with user context
                log_event(
                    "PLUGIN_LOAD_FAILED",
                    f"Plugin load failed: {name}",
                    level="ERROR",
                    extra={
                        "plugin_name": name,
                        "user": user_context,
                        "error": str(e),
                    }
                )
                raise

    def unregister(self, plugin_name: str, user_context: Optional[str] = None) -> None:
        """Unregister the plugin and call its cleanup hook.

        Args:
            plugin_name: Name of plugin to unregister.
            user_context: Optional user context (defaults to current system user).
        """
        with self._lock:
            plugin = self._plugins.pop(plugin_name, None)
            if plugin is None:
                raise KeyError(f"Plugin '{plugin_name}' is not registered")

            # Get user context for audit logging (sanitized)
            if user_context is None:
                user_context = _get_user_context()
            else:
                user_context = _sanitize_identifier(user_context)

            try:
                plugin.unregister()
                self._state.pop(plugin_name, None)

                # Log plugin unload with user context
                log_event(
                    "PLUGIN_UNLOADED",
                    f"Plugin unloaded: {plugin_name}",
                    extra={
                        "plugin_name": plugin_name,
                        "user": user_context,
                        "plugin_version": getattr(plugin.metadata, "version", "unknown"),
                    }
                )
            except Exception as e:
                # Log plugin unload failure with user context
                log_event(
                    "PLUGIN_UNLOAD_FAILED",
                    f"Plugin unload failed: {plugin_name}",
                    level="ERROR",
                    extra={
                        "plugin_name": plugin_name,
                        "user": user_context,
                        "error": str(e),
                    }
                )
                raise

    def get(self, plugin_name: str) -> Plugin:
        with self._lock:
            return self._plugins[plugin_name]

    def __iter__(self) -> Iterator[Plugin]:
        with self._lock:
            yield from list(self._plugins.values())


class PluginContextManager:
    """Context manager helper for temporary plugin deployments."""

    def __init__(self, registry: PluginRegistry, plugin_name: str, plugin: Plugin, user_context: Optional[str] = None):
        self.registry = registry
        self.plugin_name = plugin_name
        self.plugin = plugin
        self.user_context = _sanitize_identifier(user_context) if user_context else _get_user_context()

    def __enter__(self) -> Plugin:
        self.registry.register(self.plugin, app=None, name=self.plugin_name, user_context=self.user_context)
        return self.plugin

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.registry.unregister(self.plugin_name, user_context=self.user_context)