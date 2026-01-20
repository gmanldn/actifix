"""Tests for module metadata validation and failure paths."""

import json
import sys

import pytest

import actifix.api as api
from actifix.state_paths import get_actifix_paths, init_actifix_files


def test_validate_module_metadata():
    valid = {
        "name": "modules.sample",
        "version": "1.0.0",
        "description": "Sample module",
        "capabilities": {"gui": True},
        "data_access": {"state_dir": True},
        "network": {"external_requests": False},
        "permissions": ["logging"],
    }
    assert api._validate_module_metadata("sample", valid) == []

    invalid = {"name": "", "permissions": ["unknown_perm"]}
    errors = api._validate_module_metadata("sample", invalid)
    assert errors


def test_register_module_blueprint_rejects_invalid_metadata(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    def create_blueprint(project_root, host, port):
        return Blueprint("badmeta", __name__)

    module = sys.modules[__name__]
    monkeypatch.setattr(
        module,
        "MODULE_METADATA",
        {"name": "", "permissions": ["bad"]},
        raising=False,
    )

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    status_file = tmp_path / ".actifix" / "module_statuses.json"

    app = Flask(__name__)
    ok = api._register_module_blueprint(
        app,
        "badmeta",
        create_blueprint,
        project_root=tmp_path,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
    )

    assert not ok
    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert "modules.badmeta" in data["statuses"]["error"]
