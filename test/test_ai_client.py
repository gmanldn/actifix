#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Actifix AI client fallback ordering and provider handling.
"""

import builtins
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import actifix.ai_client as ai_module
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


def _mock_import_error(monkeypatch, missing_name: str):
    """Patch __import__ to raise ImportError for a given module name."""
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == missing_name:
            raise ImportError(f"mock missing {missing_name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)


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


def test_build_fix_prompt_includes_ticket_context():
    """The generated prompt embeds the ticket metadata for the AI."""
    client = AIClient()
    prompt = client._build_fix_prompt({
        "id": "ACT-20260115-TEST",
        "message": "boom",
        "source": "module.py:45",
    })
    assert "ACT-20260115-TEST" in prompt
    assert "boom" in prompt
    assert "module.py:45" in prompt


def test_estimate_costs_match_pricing_tiers():
    """Cost helpers use the published pricing tables."""
    client = AIClient()
    claude_cost = client._estimate_claude_cost(1000, 2000)
    openai_cost = client._estimate_openai_cost(1000, 2000)
    assert claude_cost == pytest.approx(1000 * 0.000003 + 2000 * 0.000015)
    assert openai_cost == pytest.approx(1000 * 0.00001 + 2000 * 0.00003)


def test_call_provider_dispatches_to_helpers(monkeypatch):
    """Each provider routes to the expected helper method."""
    client = AIClient()
    called = []

    def make_stub(provider):
        def stub(prompt, ticket_info):
            called.append(provider)
            return AIResponse(
                content="ok",
                provider=provider,
                model="model",
                success=True,
            )
        return stub

    monkeypatch.setattr(client, "_call_claude_local", make_stub(AIProvider.CLAUDE_LOCAL))
    monkeypatch.setattr(client, "_call_claude_api", make_stub(AIProvider.CLAUDE_API))
    monkeypatch.setattr(client, "_call_openai", make_stub(AIProvider.OPENAI))
    monkeypatch.setattr(client, "_call_ollama", make_stub(AIProvider.OLLAMA))
    monkeypatch.setattr(client, "_call_free_alternative", make_stub(AIProvider.FREE_ALTERNATIVE))

    for provider in (
        AIProvider.CLAUDE_LOCAL,
        AIProvider.CLAUDE_API,
        AIProvider.OPENAI,
        AIProvider.OLLAMA,
        AIProvider.FREE_ALTERNATIVE,
    ):
        called.clear()
        response = client._call_provider(provider, "prompt", {})
        assert response.provider == provider
        assert called == [provider]


def test_call_provider_handles_unknown_provider():
    """An unrecognized provider returns a helpful error."""
    client = AIClient()
    response = client._call_provider(object(), "prompt", {})
    assert not response.success
    assert "Unknown provider" in response.error


def test_get_provider_order_handles_ollama_availability(monkeypatch):
    """OLLAMA is inserted when the helper reports availability."""
    client = AIClient()
    monkeypatch.setattr(client, "_is_claude_local_available", lambda: False)
    monkeypatch.setattr(client, "_has_claude_api_key", lambda: False)
    monkeypatch.setattr(client, "_has_openai_api_key", lambda: False)
    monkeypatch.setattr(client, "_is_ollama_available", lambda: True)

    order = client._get_provider_order()
    assert AIProvider.OLLAMA in order
    assert order[-1] == AIProvider.FREE_ALTERNATIVE


def test_call_claude_local_handles_timeout_and_errors(monkeypatch):
    client = AIClient()

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(subprocess, "run", raise_timeout)
    timeout_response = client._call_claude_local("prompt", {})
    assert not timeout_response.success
    assert timeout_response.error == "Claude CLI timeout"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("failed")),
    )
    error_response = client._call_claude_local("prompt", {})
    assert not error_response.success
    assert "Claude CLI error" in error_response.error


def test_is_claude_local_available_respects_subprocess(monkeypatch):
    """Claude CLI availability is cached and handles missing executables."""
    client = AIClient()

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: types.SimpleNamespace(returncode=0))
    assert client._is_claude_local_available()

    client2 = AIClient()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError),
    )
    assert not client2._is_claude_local_available()


def test_is_ollama_available_checks_http(monkeypatch):
    """Ollama availability queries the local HTTP port."""
    def requests_module(status_code=200, raise_exc=False):
        class DummyResponse:
            def __init__(self, status):
                self.status_code = status

        def get(*args, **kwargs):
            if raise_exc:
                raise RuntimeError("ouch")
            return DummyResponse(status_code)

        return types.SimpleNamespace(get=get)

    monkeypatch.setitem(sys.modules, "requests", requests_module(status_code=200))
    assert AIClient()._is_ollama_available()

    monkeypatch.setitem(sys.modules, "requests", requests_module(status_code=500))
    assert not AIClient()._is_ollama_available()

    monkeypatch.setitem(sys.modules, "requests", requests_module(raise_exc=True))
    assert not AIClient()._is_ollama_available()


def test_call_claude_local_returns_success_and_missing(monkeypatch):
    """Claude CLI reports success when available and handles missing binary."""
    client = AIClient()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(returncode=0, stdout="ready\n", stderr=""),
    )
    success = client._call_claude_local("prompt", {})
    assert success.success
    assert success.content == "ready"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError),
    )
    failure = client._call_claude_local("prompt", {})
    assert not failure.success
    assert "not found" in failure.error.lower()


def test_call_claude_api_success(monkeypatch):
    """Claude API uses the anthropic client structure to gather tokens."""
    class DummyUsage:
        input_tokens = 5
        output_tokens = 10

    class DummyChoice:
        def __init__(self, text):
            self.text = text

    class DummyResponse:
        def __init__(self):
            self.content = [DummyChoice("fixed")]
            self.usage = DummyUsage()

    class DummyMessages:
        def create(self, **kwargs):
            return DummyResponse()

    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = DummyMessages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=DummyAnthropic))
    client = AIClient()
    client.config.ai_api_key = "secret"
    response = client._call_claude_api("prompt", {})
    assert response.success
    assert response.provider == AIProvider.CLAUDE_API
    assert response.tokens_used == DummyUsage.input_tokens + DummyUsage.output_tokens


def test_call_claude_api_reports_missing_key(monkeypatch):
    """Missing API key returns a clear error."""
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=lambda api_key: None))
    client = AIClient()
    client.config.ai_api_key = ""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client._call_claude_api("prompt", {})
    assert not response.success
    assert response.error == "No Anthropic API key found"


def test_call_claude_api_handles_import_error(monkeypatch):
    """ImportError is translated into a descriptive failure."""
    client = AIClient()
    client.config.ai_api_key = "key"
    _mock_import_error(monkeypatch, "anthropic")
    response = client._call_claude_api("prompt", {})
    assert not response.success
    assert "anthropic package not installed" in response.error


def test_call_claude_api_handles_runtime_error(monkeypatch):
    """Runtime errors from the Anthropic client are reported."""
    class ExplodingAnthropic:
        def __init__(self, api_key):
            self.messages = self.Messages()

        class Messages:
            def create(self, **kwargs):
                raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=ExplodingAnthropic))
    client = AIClient()
    client.config.ai_api_key = "secret"
    response = client._call_claude_api("prompt", {})
    assert not response.success
    assert "Anthropic API error" in response.error


def test_call_openai_success(monkeypatch):
    """OpenAI integration builds a chat completion and reports usage."""
    class DummyUsage:
        prompt_tokens = 3
        completion_tokens = 2
        total_tokens = 5

    class DummyChoice:
        def __init__(self, content):
            self.message = types.SimpleNamespace(content=content)

    class DummyCompletions:
        def __init__(self):
            self.choices = [DummyChoice("answer")]
            self.usage = DummyUsage()

    class DummyOpenAI:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=lambda **kwargs: DummyCompletions())
            )

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    client = AIClient()
    client.config.ai_api_key = "openai-key"
    response = client._call_openai("prompt", {})
    assert response.success
    assert response.provider == AIProvider.OPENAI
    assert response.tokens_used == DummyUsage.total_tokens


def test_call_openai_reports_missing_key(monkeypatch):
    """Missing OpenAI API key returns a clear failure."""
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=lambda api_key: None))
    client = AIClient()
    client.config.ai_api_key = ""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client._call_openai("prompt", {})
    assert not response.success
    assert response.error == "No OpenAI API key found"


def test_call_openai_handles_import_error(monkeypatch):
    client = AIClient()
    client.config.ai_api_key = "key"
    _mock_import_error(monkeypatch, "openai")
    response = client._call_openai("prompt", {})
    assert not response.success
    assert "openai package not installed" in response.error


def test_call_openai_handles_runtime_exception(monkeypatch):
    """Runtime errors from OpenAI are surfaced."""
    class ExplodingChat:
        def __init__(self, api_key):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
            )

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=ExplodingChat))
    client = AIClient()
    client.config.ai_api_key = "openai-key"
    response = client._call_openai("prompt", {})
    assert not response.success
    assert "OpenAI API error" in response.error


def test_call_ollama_respects_http(monkeypatch):
    """Ollama client depends on requests.post and propagates HTTP errors."""
    def make_requests(status_code=200):
        def post(*args, **kwargs):
            return types.SimpleNamespace(
                status_code=status_code,
                json=lambda: {"response": "ok"} if status_code == 200 else {},
            )

        return types.SimpleNamespace(post=post)

    monkeypatch.setitem(sys.modules, "requests", make_requests(200))
    client = AIClient()
    response = client._call_ollama("prompt", {})
    assert response.success
    assert response.content == "ok"

    monkeypatch.setitem(sys.modules, "requests", make_requests(500))
    failure = client._call_ollama("prompt", {})
    assert not failure.success
    assert "HTTP" in failure.error


def test_call_ollama_handles_import_error(monkeypatch):
    client = AIClient()
    _mock_import_error(monkeypatch, "requests")
    response = client._call_ollama("prompt", {})
    assert not response.success
    assert "requests package not installed" in response.error


def test_call_ollama_handles_runtime_exception(monkeypatch):
    class ExplodingRequests:
        def post(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "requests", ExplodingRequests())
    response = AIClient()._call_ollama("prompt", {})
    assert not response.success
    assert "Ollama error" in response.error


def _stub_inputs(responses):
    iterator = iter(responses)

    def fake_input(prompt=""):
        return next(iterator)

    return fake_input


def test_call_free_alternative_manual_and_skip(monkeypatch):
    """Manual prompt, invalid input, and skip choices flow through."""
    client = AIClient()
    monkeypatch.setattr(builtins, "input", _stub_inputs(["1", "manual reply"]))
    choice_one = client._call_free_alternative("prompt", {"id": "ACT-TEST"})
    assert choice_one.success
    assert choice_one.model == "claude-web"

    monkeypatch.setattr(builtins, "input", _stub_inputs(["9", "5"]))
    choice_skip = client._call_free_alternative("prompt", {"id": "ACT-TEST"})
    assert not choice_skip.success
    assert "skip" in choice_skip.error.lower()

    called = []

    def fake_ollama(prompt, ticket_info):
        called.append(True)
        return AIResponse(
            content="ollama",
            provider=AIProvider.OLLAMA,
            model="codellama",
            success=True,
        )

    client._call_ollama = fake_ollama
    monkeypatch.setattr(builtins, "input", _stub_inputs(["3"]))
    choice_three = client._call_free_alternative("prompt", {"id": "ACT-TEST"})
    assert choice_three.success
    assert called


def test_call_free_alternative_handles_chatgpt_and_manual(monkeypatch):
    """ChatGPT and manual fix choices return the expected models."""
    client = AIClient()
    monkeypatch.setattr(builtins, "input", _stub_inputs(["2", "chat repsonse"]))
    chatgpt_choice = client._call_free_alternative("prompt", {"id": "ACT-CHAT"})
    assert chatgpt_choice.model == "chatgpt-web"
    assert chatgpt_choice.success

    monkeypatch.setattr(builtins, "input", _stub_inputs(["4", "manual fix"]))
    manual_choice = client._call_free_alternative("prompt", {"id": "ACT-CHAT"})
    assert manual_choice.model == "manual"
    assert manual_choice.content == "manual fix"


def test_call_free_alternative_keyboard_interrupt(monkeypatch):
    """KeyboardInterrupt during free alternative returns interrupted status."""
    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt

    client = AIClient()
    monkeypatch.setattr(builtins, "input", raise_interrupt)
    response = client._call_free_alternative("prompt", {"id": "ACT-TEST"})
    assert not response.success
    assert response.model == "interrupted"


def test_generate_fix_returns_error_when_all_providers_fail(monkeypatch):
    """generate_fix should fall back to FREE_ALTERNATIVE after exhausting providers."""
    client = AIClient()
    monkeypatch.setattr(client, "_get_provider_order", lambda preferred=None: [
        AIProvider.CLAUDE_LOCAL,
        AIProvider.OPENAI,
    ])
    monkeypatch.setattr(
        client,
        "_call_provider",
        lambda provider, prompt, ticket_info: AIResponse(
            content="",
            provider=provider,
            model="model",
            success=False,
            error="boom"
        ),
    )
    monkeypatch.setattr(ai_module.time, "sleep", lambda *args, **kwargs: None)
    response = client.generate_fix({"id": "ACT-FAKE"})
    assert not response.success
    assert response.provider == AIProvider.FREE_ALTERNATIVE
    assert "All AI providers failed" in response.error
