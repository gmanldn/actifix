"""Actifix modules package."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from actifix.raise_af import redact_secrets_from_text
from actifix.raise_af import record_error, TicketPriority
from actifix.config import load_config

__all__ = [
    "ModuleContext",
    "build_module_env",
    "get_module_context",
    "yhatzee",
]


_SAFE_ENV_KEYS = {
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "LC_MESSAGES",
    "LOGNAME",
    "PATH",
    "PWD",
    "SHELL",
    "TERM",
    "TERM_PROGRAM",
    "TERM_PROGRAM_VERSION",
    "TMPDIR",
    "TZ",
    "USER",
}

_SAFE_ENV_PREFIXES = ("LC_", "XDG_")

_SENSITIVE_ENV_MARKERS = (
    "SECRET",
    "TOKEN",
    "PASS",
    "PASSWORD",
    "API_KEY",
    "AUTH",
    "AWS",
    "OPENAI",
    "CLAUDE",
    "GITHUB",
    "GITLAB",
    "SLACK",
    "DATABASE",
    "PRIVATE",
)


@dataclass(frozen=True)
class ModuleContext:
    env: dict[str, str]


def _is_sensitive_env_key(key: str) -> bool:
    upper_key = key.upper()
    return any(marker in upper_key for marker in _SENSITIVE_ENV_MARKERS)


def _is_safe_env_key(key: str, allowlist: set[str]) -> bool:
    if key in allowlist:
        return True
    return any(key.startswith(prefix) for prefix in _SAFE_ENV_PREFIXES)


def build_module_env(
    env: Mapping[str, str] | None = None,
    *,
    extra_safe_keys: Iterable[str] | None = None,
) -> dict[str, str]:
    """Return a sanitized environment mapping for module execution."""
    env = env or os.environ
    allowlist = set(_SAFE_ENV_KEYS)
    if extra_safe_keys:
        allowlist.update(str(key) for key in extra_safe_keys)

    safe_env: dict[str, str] = {}
    for key, value in env.items():
        if not _is_safe_env_key(key, allowlist):
            continue
        if _is_sensitive_env_key(key):
            continue
        safe_env[key] = redact_secrets_from_text(str(value))
    return safe_env


def get_module_context(
    env: Mapping[str, str] | None = None,
    *,
    extra_safe_keys: Iterable[str] | None = None,
) -> ModuleContext:
    """Build a module execution context with sanitized env."""
    return ModuleContext(env=build_module_env(env, extra_safe_keys=extra_safe_keys))


def _parse_module_config_overrides(raw: str) -> dict[str, dict[str, object]]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        record_error(
            message=f"Invalid module config overrides JSON: {exc}",
            source="modules.__init__:_parse_module_config_overrides",
            priority=TicketPriority.P2,
        )
        return {}
    if not isinstance(data, dict):
        return {}
    overrides: dict[str, dict[str, object]] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            overrides[str(key)] = value
    return overrides


def get_module_config(
    module_name: str,
    defaults: Mapping[str, object],
    *,
    project_root: str | None = None,
) -> dict[str, object]:
    """Return module config merged with overrides."""
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
