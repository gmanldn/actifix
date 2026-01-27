#!/usr/bin/env python3
"""
Set API keys for Actifix providers using the secure credential manager.

Stores keys in the OS credential store (Keychain/Credential Manager) or
Actifix's encrypted file fallback. Keys are never printed back to stdout.
"""

from __future__ import annotations

import getpass
import sys
from dataclasses import dataclass
from typing import Iterable

from actifix.raise_af import TicketPriority, enforce_raise_af_only, record_error
from actifix.security.credentials import CredentialType, get_credential_manager
from actifix.state_paths import get_actifix_paths, init_actifix_files


@dataclass(frozen=True)
class KeySpec:
    name: str
    label: str
    env_var: str
    description: str
    credential_type: CredentialType = CredentialType.API_KEY


KEY_SPECS: tuple[KeySpec, ...] = (
    KeySpec(
        name="openrouter_api_key",
        label="OpenRouter",
        env_var="OPENROUTER_API_KEY",
        description="OpenRouter API key for free/fallback models",
    ),
    KeySpec(
        name="openai_api_key",
        label="OpenAI",
        env_var="OPENAI_API_KEY",
        description="OpenAI API key for GPT models",
    ),
    KeySpec(
        name="anthropic_api_key",
        label="Anthropic",
        env_var="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude models",
    ),
    KeySpec(
        name="github_token",
        label="GitHub",
        env_var="ACTIFIX_GITHUB_TOKEN",
        description="GitHub token for issue sync",
        credential_type=CredentialType.TOKEN,
    ),
)


def _prompt_for_key(spec: KeySpec) -> str:
    prompt = (
        f"{spec.label} key ({spec.env_var}) - {spec.description}\n"
        "Leave blank to skip: "
    )
    return getpass.getpass(prompt)


def _store_key(spec: KeySpec, value: str) -> None:
    manager = get_credential_manager()
    manager.store_credential(
        spec.name,
        value,
        cred_type=spec.credential_type,
        description=spec.description,
    )


def _configure_keys(specs: Iterable[KeySpec]) -> int:
    stored = []
    skipped = []

    for spec in specs:
        value = _prompt_for_key(spec).strip()
        if not value:
            skipped.append(spec.label)
            continue
        try:
            _store_key(spec, value)
            stored.append(spec.label)
        except Exception as exc:
            record_error(
                message=f"Failed to store {spec.label} credential: {exc}",
                source="scripts/set_api.py:_store_key",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            print(f"Error storing {spec.label} credential. See Actifix tickets.")

    print("\nAPI key setup summary")
    if stored:
        print(f"  Stored: {', '.join(stored)}")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")
    if not stored and not skipped:
        print("  No keys processed")

    return 0


def main() -> int:
    paths = get_actifix_paths()
    init_actifix_files(paths)
    enforce_raise_af_only(paths)

    if not sys.stdin.isatty():
        record_error(
            message="set_api.py requires an interactive terminal",
            source="scripts/set_api.py:main",
            error_type="NonInteractiveError",
            priority=TicketPriority.P2,
        )
        print("set_api.py requires an interactive terminal.")
        return 1

    return _configure_keys(KEY_SPECS)


if __name__ == "__main__":
    raise SystemExit(main())
