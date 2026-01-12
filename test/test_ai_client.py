#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Actifix AI client fallback ordering and provider handling.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.ai_client import (
    AIClient,
    AIProvider,
    AIResponse,
    reset_ai_client,
)


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the global AI client before and after each test."""
    reset_ai_client()
    yield
    reset_ai_client()


def test_provider_order_prefers_available_providers(monkeypatch):
    """The order should respect preference, availability, and always end with the free alternative."""
    client = AIClient()
    monkeypatch.setattr(client, "_is_claude_local_available", lambda: True)
    monkeypatch.setattr(client, "_has_claude_api_key", lambda: True)
    monkeypatch.setattr(client, "_has_openai_api_key", lambda: True)
    monkeypatch.setattr(client, "_is_ollama_available", lambda: False)

    order = client._get_provider_order(preferred=AIProvider.FREE_ALTERNATIVE)

    assert order[0] == AIProvider.FREE_ALTERNATIVE
    assert AIProvider.CLAUDE_LOCAL in order
    assert AIProvider.CLAUDE_API in order
    assert AIProvider.OPENAI in order
    assert AIProvider.FREE_ALTERNATIVE in order


def test_generate_fix_iterates_providers(monkeypatch):
    """generate_fix should try each provider until one succeeds."""
    client = AIClient()

    monkeypatch.setattr(client, "_get_provider_order", lambda preferred=None: [
        AIProvider.CLAUDE_API,
        AIProvider.OPENAI,
        AIProvider.FREE_ALTERNATIVE,
    ])

    call_sequence = []

    def fake_call(provider, prompt, ticket_info):
        call_sequence.append(provider)
        success = provider == AIProvider.FREE_ALTERNATIVE
        return AIResponse(
            content="done" if success else "",
            provider=provider,
            model="test",
            success=success,
            error=None if success else "fail"
        )

    monkeypatch.setattr(client, "_call_provider", fake_call)

    ticket = {"id": "ACT-20260114-API", "message": "Fallback test", "priority": "P2"}
    response = client.generate_fix(ticket)

    assert response.success
    assert response.provider == AIProvider.FREE_ALTERNATIVE
    assert call_sequence[0] == AIProvider.CLAUDE_API
    assert call_sequence[-1] == AIProvider.FREE_ALTERNATIVE
