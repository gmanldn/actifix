"""Plugin validation helpers."""

from __future__ import annotations

import logging
import re
from typing import Final

from .protocol import Plugin, PluginMetadata

logger = logging.getLogger(__name__)

VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d+\.\d+(?:\.\d+)?$")


def validate_plugin(plugin: Plugin) -> PluginMetadata:
    """Enforce sane metadata and capability declarations."""
    metadata = plugin.metadata
    errors: list[str] = []

    if not metadata.name.strip():
        errors.append("name")
    if not metadata.version.strip():
        errors.append("version")
    elif not VERSION_PATTERN.match(metadata.version):
        errors.append("version-format")
    if not metadata.description.strip():
        errors.append("description")

    if errors:
        message = f"Plugin '{metadata.name or '<unknown>'}' failed validation: {', '.join(errors)}"
        logger.error(message)
        raise ValueError(message)

    logger.debug("Plugin '%s' passed validation", metadata.name)
    return metadata
