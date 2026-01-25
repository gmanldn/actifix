"""Tests for start.py surfacing API-hosted modules."""

from __future__ import annotations


def test_start_surfaces_expected_api_module_paths():
    from scripts import start

    assert start.API_MODULE_HEALTH_PATHS["Hollogram"] == "/modules/hollogram/health"
    assert start.API_MODULE_HEALTH_PATHS["Dev_Assistant"] == "/modules/dev-assistant/health"


def test_start_waits_for_api_ready(monkeypatch):
    from scripts import start

    calls = {"n": 0}

    def fake_probe(url: str, timeout: float = 1.5):
        calls["n"] += 1
        # First two calls fail, then succeed.
        if calls["n"] < 3:
            return False, 0, "conn refused"
        return True, 200, ""

    monkeypatch.setattr(start, "_probe_http_status", fake_probe)
    assert start._wait_for_api_ready("127.0.0.1", 5001, timeout=1.0) is True
