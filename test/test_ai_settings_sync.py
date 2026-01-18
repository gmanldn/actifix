from pathlib import Path

import pytest

from actifix.ai_client import (
    AIProvider,
    DEFAULT_FREE_MODEL,
    resolve_provider_selection,
)
from actifix.api import create_app, FLASK_AVAILABLE


def test_resolve_provider_selection_defaults_to_mimo():
    selection = resolve_provider_selection("", "")
    assert selection.provider == AIProvider.FREE_ALTERNATIVE
    assert selection.model == DEFAULT_FREE_MODEL
    assert selection.strict_preferred is True


def test_ai_status_defaults_to_mimo(monkeypatch):
    if not FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.delenv("ACTIFIX_AI_PROVIDER", raising=False)
    monkeypatch.delenv("ACTIFIX_AI_MODEL", raising=False)

    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(project_root=repo_root)
    client = app.test_client()

    response = client.get("/api/ai-status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["active_provider"] == DEFAULT_FREE_MODEL
    assert data["preferred_provider"] == DEFAULT_FREE_MODEL


def test_ai_status_provider_options_include_do_af(monkeypatch):
    if not FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(project_root=repo_root)
    client = app.test_client()

    response = client.get("/api/ai-status")
    assert response.status_code == 200
    data = response.get_json()
    option_values = {opt["value"] for opt in data["provider_options"]}

    assert {
        "auto",
        "claude_local",
        "openai_cli",
        "claude_api",
        "openai",
        "ollama",
        DEFAULT_FREE_MODEL,
    }.issubset(option_values)
