"""Entry point driven plugin discovery and loading."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Iterable, List

from .protocol import Plugin
from .registry import PluginRegistry
from .sandbox import PluginSandbox
from .validation import validate_plugin
from ..raise_af import record_error, TicketPriority

logger = logging.getLogger(__name__)

PLUGIN_ENTRY_POINT_GROUP = "actifix.plugins"


def _select_entrypoints(group: str) -> Iterable[metadata.EntryPoint]:
    eps = metadata.entry_points()
    if hasattr(eps, "select"):
        return eps.select(group=group)
    return (ep for ep in eps if ep.group == group)


@dataclass(frozen=True)
class PluginLoadResult:
    """Summary of plugins loaded in a discovery run."""

    loaded: List[str]
    errors: List[str]


def _instantiate(entry_point: metadata.EntryPoint) -> Plugin:
    plugin_target = entry_point.load()
    if isinstance(plugin_target, type):
        instance = plugin_target()
    elif callable(plugin_target):
        instance = plugin_target()
    else:
        instance = plugin_target

    if not isinstance(instance, Plugin):
        raise TypeError(f"Entry point {entry_point.name} did not return a Plugin")

    return instance


def discover_plugins(group: str = PLUGIN_ENTRY_POINT_GROUP) -> List[metadata.EntryPoint]:
    return list(_select_entrypoints(group))


def load_plugins(registry: PluginRegistry, app: Any = None, *, group: str = PLUGIN_ENTRY_POINT_GROUP) -> PluginLoadResult:
    """Discover and register plugins using entry points."""
    loaded: List[str] = []
    errors: List[str] = []
    entry_points = discover_plugins(group)

    for entry in entry_points:
        sandbox = PluginSandbox(entry.name)
        try:
            plugin = _instantiate(entry)
            validate_plugin(plugin)
            sandbox.safe_register(plugin, app, registry)
            loaded.append(entry.name)
        except Exception as exc:
            message = f"Failed to load plugin '{entry.name}': {exc}"
            errors.append(message)
            sandbox.record_error(message, exc)

    if errors:
        logger.warning("Plugin load completed with failures: %s", errors)
    else:
        logger.info("Plugin load completed successfully (%d plugins)", len(loaded))

    return PluginLoadResult(loaded=loaded, errors=errors)
