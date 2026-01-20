"""Actifix modules package."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Mapping

from actifix.raise_af import redact_secrets_from_text

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
