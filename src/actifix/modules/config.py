#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module configuration helpers.

Provides shared parsing and override logic so modules can resolve
configuration without duplicating JSON parsing or logging code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from actifix.config import load_config
from actifix.raise_af import TicketPriority, record_error


def _parse_module_config_overrides(raw: str) -> dict[str, dict[str, object]]:
    """Parse the ACTIFIX_MODULE_CONFIG_OVERRIDES payload."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        record_error(
            message=f"Invalid module config overrides JSON: {exc}",
            source="modules.config:_parse_module_config_overrides",
            error_type="ConfigurationError",
            priority=TicketPriority.P2,
        )
        return {}
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            normalized[str(key)] = value
    return normalized


def get_module_config(
    module_name: str,
    defaults: Mapping[str, object],
    *,
    project_root: str | Path | None = None,
) -> dict[str, object]:
    """Return module config merged with defaults and overrides."""
    config = load_config(project_root=Path(project_root) if project_root else None, fail_fast=False)
    overrides = _parse_module_config_overrides(config.module_config_overrides_json)
    normalized = module_name.strip()
    full_name = normalized if "." in normalized else f"modules.{normalized}"
    short_name = normalized.split(".", 1)[1] if normalized.startswith("modules.") else normalized

    module_overrides = overrides.get(full_name) or overrides.get(short_name) or {}
    merged = dict(defaults)
    if isinstance(module_overrides, dict):
        merged.update(module_overrides)
    return merged
