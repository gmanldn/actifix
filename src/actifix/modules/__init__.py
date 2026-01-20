"""Actifix modules package."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from actifix.raise_af import redact_secrets_from_text
from .base import ModuleBase
from .config import get_module_config

__all__ = [
    "ModuleBase",
    "ModuleContext",
    "build_module_env",
    "get_module_context",
    "get_module_config",
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

_SAFE_ENV_PREFIXES = ("LC_", "XDG_", "ACTIFIX_")

_ALWAYS_ALLOW_SENSITIVE_NAMED_KEYS = {
    # This is a configuration toggle, not a secret value.
    "ACTIFIX_SECRET_REDACTION",
}

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
    if key in _ALWAYS_ALLOW_SENSITIVE_NAMED_KEYS:
        return False
    upper_key = key.upper()
    return any(marker in upper_key for marker in _SENSITIVE_ENV_MARKERS)


def _is_safe_env_key(key_upper: str, allowlist_upper: set[str]) -> bool:
    if key_upper in allowlist_upper:
        return True
    return any(key_upper.startswith(prefix) for prefix in _SAFE_ENV_PREFIXES)


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

    allowlist_upper = {key.upper() for key in allowlist}

    safe_env: dict[str, str] = {}
    for key, value in env.items():
        key_str = str(key)
        key_upper = key_str.upper()
        if not _is_safe_env_key(key_upper, allowlist_upper):
            continue
        if _is_sensitive_env_key(key_upper):
            continue
        safe_env[key_str] = redact_secrets_from_text(str(value))
    return safe_env


def get_module_context(
    env: Mapping[str, str] | None = None,
    *,
    extra_safe_keys: Iterable[str] | None = None,
) -> ModuleContext:
    """Build a module execution context with sanitized env."""
    return ModuleContext(env=build_module_env(env, extra_safe_keys=extra_safe_keys))

