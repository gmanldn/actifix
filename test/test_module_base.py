"""Tests for the ModuleBase shared helper."""

from __future__ import annotations

import json
from actifix.modules.base import ModuleBase
from actifix.raise_af import TicketPriority


def test_module_base_uses_config_overrides(tmp_path, monkeypatch):
    """ModuleBase should respect ACTIFIX_MODULE_CONFIG_OVERRIDES entries."""
    monkeypatch.setenv(
        "ACTIFIX_MODULE_CONFIG_OVERRIDES",
        json.dumps({"test": {"host": "192.0.2.5", "port": 49152}}),
    )
    helper = ModuleBase(
        module_key="test",
        defaults={"host": "127.0.0.1", "port": 8000},
        metadata={"name": "modules.test"},
        project_root=tmp_path,
    )

    host, port = helper.resolve_host_port(host=None, port=None)
    assert host == "192.0.2.5"
    assert port == 49152


def test_module_base_health_response_includes_module_id(tmp_path):
    helper = ModuleBase(
        module_key="test",
        defaults={"host": "127.0.0.1", "port": 8000},
        metadata={"name": "modules.test"},
        project_root=tmp_path,
    )

    health = helper.health_response()
    assert health["status"] == "ok"
    assert health["module"] == "test"
    assert health["module_id"] == "modules.test"


def test_module_base_records_error_with_default_run_label(tmp_path, monkeypatch):
    helper = ModuleBase(
        module_key="test",
        defaults={"host": "127.0.0.1", "port": 8000},
        metadata={"name": "modules.test"},
        project_root=tmp_path,
    )

    captured: dict[str, object] = {}

    def fake_record_error(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setattr("actifix.modules.base.record_error", fake_record_error)

    helper.record_module_error(
        message="failure occurred",
        source="modules.test",
        error_type="TestError",
        priority=TicketPriority.P1,
    )

    assert captured["run_label"] == "test-gui"
    assert captured["error_type"] == "TestError"
    assert captured["priority"] == TicketPriority.P1
