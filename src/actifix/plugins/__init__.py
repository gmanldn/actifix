"""Plugin subsystem exports."""

from .protocol import Plugin, PluginHealthStatus, PluginMetadata
from .registry import PluginContextManager, PluginRegistry
from .sandbox import PluginSandbox
from .loader import PluginLoadResult, PLUGIN_ENTRY_POINT_GROUP, discover_plugins, load_plugins
from .validation import validate_plugin
from .builtin import CorePlugin

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginHealthStatus",
    "PluginRegistry",
    "PluginContextManager",
    "PluginSandbox",
    "discover_plugins",
    "load_plugins",
    "PluginLoadResult",
    "PLUGIN_ENTRY_POINT_GROUP",
    "validate_plugin",
    "CorePlugin",
]
