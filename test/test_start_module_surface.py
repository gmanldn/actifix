"""Tests for start.py surfacing API-hosted modules."""

from __future__ import annotations


def test_start_surfaces_expected_api_module_paths():
    from scripts import start

    assert start.API_MODULE_HEALTH_PATHS["Hollogram"] == "/modules/hollogram/health"
    assert start.API_MODULE_HEALTH_PATHS["Dev_Assistant"] == "/modules/dev_assistant/health"


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


def test_start_module_probe_retries_only_on_connection_refused(monkeypatch):
    from scripts import start
    import actifix.agent_voice as agent_voice

    calls = {"n": 0}

    def fake_probe(_url: str, timeout: float = 0.75):
        calls["n"] += 1
        # First call is a timeout (non-retryable), which should stop retries.
        return False, 0, "timed out"

    monkeypatch.setattr(start, "_probe_http_status", fake_probe)
    monkeypatch.setattr(start, "SLOW_MODULE_PROBE_NAMES", set())
    # Trigger the probe loop by calling announce_api_modules with API ready bypassed.
    monkeypatch.setattr(start, "_wait_for_api_ready", lambda *_args, **_kwargs: True)
    # Replace side-effectful logging/agent voice with no-ops.
    monkeypatch.setattr(start, "log_info", lambda *_: None)
    monkeypatch.setattr(start, "log_warning", lambda *_: None)
    monkeypatch.setattr(start, "log_success", lambda *_: None)
    monkeypatch.setattr(agent_voice, "record_agent_voice", lambda *_args, **_kwargs: 0)
    start.announce_api_modules("127.0.0.1", 5001)
    assert calls["n"] == len(start.API_MODULE_HEALTH_PATHS)
