"""Tests for module status persistence and recovery."""

import json

import actifix.api as api
import actifix.log_utils as log_utils


def test_module_status_write_uses_atomic_write(tmp_path, monkeypatch):
    status_file = tmp_path / "module_statuses.json"
    payload = api._default_module_status_payload()
    captured = {}

    def fake_atomic_write(path, content, encoding="utf-8"):
        captured["path"] = path
        captured["content"] = content
        path.write_text(content, encoding=encoding)

    monkeypatch.setattr(log_utils, "atomic_write", fake_atomic_write)

    api._write_module_status_payload(status_file, payload)

    assert captured["path"] == status_file
    data = json.loads(captured["content"])
    assert data["schema_version"] == api.MODULE_STATUS_SCHEMA_VERSION
    assert data["statuses"] == payload["statuses"]


def test_module_status_recovery_on_partial_file(tmp_path):
    status_file = tmp_path / "module_statuses.json"
    status_file.write_text("{", encoding="utf-8")

    payload = api._read_module_status_payload(status_file)

    assert payload["schema_version"] == api.MODULE_STATUS_SCHEMA_VERSION
    assert payload["statuses"] == {"active": [], "disabled": [], "error": []}

    backup_path = status_file.with_suffix(".corrupt.json")
    assert backup_path.exists()

    recovered = json.loads(status_file.read_text(encoding="utf-8"))
    assert recovered["schema_version"] == api.MODULE_STATUS_SCHEMA_VERSION
