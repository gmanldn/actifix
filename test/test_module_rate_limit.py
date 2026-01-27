"""Integration tests for module rate limiting."""

import json

import pytest

import actifix.api as api
from actifix.security.rate_limiter import reset_rate_limiter
from actifix.state_paths import get_actifix_paths, init_actifix_files


def test_module_rate_limit_throttles(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv(
        "ACTIFIX_MODULE_RATE_LIMIT_OVERRIDES",
        json.dumps({"yahtzee": {"calls_per_minute": 1, "calls_per_hour": 1, "calls_per_day": 1}}),
    )

    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    reset_rate_limiter()

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()

    first = client.get("/modules/yahtzee/health", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert first.status_code == 200

    second = client.get("/modules/yahtzee/health", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert second.status_code == 429
