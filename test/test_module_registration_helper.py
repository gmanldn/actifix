"""Tests for standardized module blueprint registration."""

import json

import pytest

import actifix.api as api
from actifix.modules.registry import ModuleRegistry, _read_module_status_payload, _write_module_status_payload
from actifix.state_paths import get_actifix_paths, init_actifix_files


def test_register_module_blueprint_sets_prefix(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    app = Flask(__name__)

    def create_blueprint(project_root, host, port):
        blueprint = Blueprint("dummy", __name__)

        @blueprint.route("/ping")
        def ping():
            return "ok"

        return blueprint

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    status_file = tmp_path / ".actifix" / "module_statuses.json"

    ok = api._register_module_blueprint(
        app,
        "dummy",
        create_blueprint,
        project_root=tmp_path,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
        depgraph_edges=set(),
    )

    assert ok
    client = app.test_client()
    response = client.get("/modules/dummy/ping")
    assert response.status_code == 200


def test_register_module_blueprint_rejects_mismatch(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    app = Flask(__name__)

    def create_blueprint(project_root, host, port):
        return Blueprint("dummy", __name__, url_prefix="/wrong")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    status_file = tmp_path / ".actifix" / "module_statuses.json"

    ok = api._register_module_blueprint(
        app,
        "dummy",
        create_blueprint,
        project_root=tmp_path,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
        depgraph_edges=set(),
    )

    assert not ok
    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert "modules.dummy" in data["statuses"]["error"]


def test_create_app_registers_module_blueprint(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    init_actifix_files(get_actifix_paths(project_root=tmp_path))

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()
    response = client.get("/modules/yahtzee/health", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200


def test_disabled_module_is_skipped(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    app = Flask(__name__)

    def create_blueprint(project_root, host, port):
        blueprint = Blueprint("dummy", __name__)

        @blueprint.route("/ping")
        def ping():
            return "ok"

        return blueprint

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    status_file = tmp_path / ".actifix" / "module_statuses.json"
    payload = _read_module_status_payload(status_file)
    payload["statuses"]["disabled"].append("modules.dummy")
    _write_module_status_payload(status_file, payload)

    registry = ModuleRegistry(project_root=tmp_path, status_file=status_file)

    ok = api._register_module_blueprint(
        app,
        "dummy",
        create_blueprint,
        project_root=tmp_path,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
        depgraph_edges=set(),
        registry=registry,
    )

    assert not ok
