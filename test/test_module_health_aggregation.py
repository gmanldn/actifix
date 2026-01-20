"""Tests for module health aggregation endpoint."""

import pytest

import actifix.api as api
from actifix.state_paths import get_actifix_paths, init_actifix_files


def test_module_health_missing(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    init_actifix_files(get_actifix_paths(project_root=tmp_path))

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()
    response = client.get("/api/modules/missing/health")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["status"] == "missing"


def test_module_health_timeout(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    init_actifix_files(get_actifix_paths(project_root=tmp_path))

    def fake_fetch(app, module_name, timeout_sec=2.0):
        return {
            "module": module_name,
            "status": "timeout",
            "http_status": 504,
            "elapsed_ms": 2000,
            "response": None,
        }

    monkeypatch.setattr(api, "_fetch_module_health", fake_fetch)

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()
    response = client.get("/api/modules/yhatzee/health")

    assert response.status_code == 504
    payload = response.get_json()
    assert payload["status"] == "timeout"
