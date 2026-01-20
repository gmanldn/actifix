"""Tests for module registry lifecycle hooks."""

from __future__ import annotations

import types

import pytest


def test_module_registry_calls_hooks(tmp_path, monkeypatch):
    flask = pytest.importorskip("flask")
    from flask import Blueprint, Flask

    import actifix.api as api
    from actifix.modules.registry import ModuleRegistry

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    app = Flask(__name__)
    status_file = tmp_path / "module_statuses.json"

    called: dict[str, int] = {"register": 0, "unregister": 0}

    dummy_module = types.SimpleNamespace()
    dummy_module.MODULE_METADATA = {
        "name": "modules.dummy",
        "version": "1.0.0",
        "description": "Dummy module for lifecycle hook tests.",
        "capabilities": {"gui": True},
        "data_access": {"state_dir": False},
        "network": {"external_requests": False},
        "permissions": ["logging"],
    }
    dummy_module.MODULE_DEPENDENCIES = []

    def module_register(*, context, app, blueprint):
        assert context.module_id == "modules.dummy"
        assert app is not None
        assert blueprint is not None
        called["register"] += 1

    def module_unregister(*, context):
        assert context.module_id == "modules.dummy"
        called["unregister"] += 1

    dummy_module.module_register = module_register
    dummy_module.module_unregister = module_unregister

    def create_blueprint(project_root, host, port):
        blueprint = Blueprint("dummy", __name__)

        @blueprint.route("/health")
        def health():
            return {"status": "ok"}

        return blueprint

    create_blueprint.__module__ = "dummy_module_for_registry"

    import importlib

    real_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "dummy_module_for_registry":
            return dummy_module
        return real_import(name, package=package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    registry = ModuleRegistry()
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

    assert ok is True
    assert called["register"] == 1

    client = app.test_client()
    response = client.get("/modules/dummy/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

    registry.shutdown()
    assert called["unregister"] == 1

