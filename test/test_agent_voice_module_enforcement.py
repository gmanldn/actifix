"""Enforcement tests: modules must emit AgentVoice rows for info and errors."""

from __future__ import annotations

import sys

import pytest

import actifix.api as api
from actifix.persistence.agent_voice_repo import AgentVoiceRepository
from actifix.persistence.database import get_database_pool, reset_database_pool
from actifix.state_paths import get_actifix_paths, init_actifix_files


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    reset_database_pool()
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    yield db_path
    reset_database_pool()


def _count_agent_voice() -> int:
    return AgentVoiceRepository(max_rows=1000).count()


def test_modulebase_records_agent_voice_on_error(isolated_db):
    from actifix.modules.base import ModuleBase

    helper = ModuleBase(module_key="unit", defaults={}, metadata={"name": "modules.unit"})
    before = _count_agent_voice()
    helper.record_module_error(
        "boom",
        source="unit:test",
        error_type="UnitError",
    )
    after = _count_agent_voice()
    assert after == before + 1


def test_api_register_module_writes_agent_voice_on_success(isolated_db, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    # Provide valid metadata in the create_blueprint module context.
    module = sys.modules[__name__]
    monkeypatch.setattr(
        module,
        "MODULE_METADATA",
        {
            "name": "modules.goodmeta",
            "version": "1.0.0",
            "description": "Good module",
            "capabilities": {"gui": True},
            "data_access": {"state_dir": True},
            "network": {"external_requests": False},
            "permissions": ["logging"],
        },
        raising=False,
    )
    monkeypatch.setattr(module, "MODULE_DEPENDENCIES", [], raising=False)

    def create_blueprint(project_root, host, port):
        return Blueprint("goodmeta", __name__, url_prefix="/modules/goodmeta")

    app = Flask(__name__)
    status_file = isolated_db.parent / ".actifix" / "module_statuses.json"
    depgraph_edges = {("modules.goodmeta", "runtime.state")}  # not used if MODULE_DEPENDENCIES is empty

    before = _count_agent_voice()
    ok = api._register_module_blueprint(
        app,
        "goodmeta",
        create_blueprint,
        project_root=isolated_db.parent,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
        depgraph_edges=depgraph_edges,
    )
    assert ok is True
    assert _count_agent_voice() == before + 1


def test_api_register_module_writes_agent_voice_on_metadata_error(isolated_db, monkeypatch):
    pytest.importorskip("flask")
    from flask import Blueprint, Flask

    module = sys.modules[__name__]
    monkeypatch.setattr(
        module,
        "MODULE_METADATA",
        {"name": "", "permissions": ["bad"]},
        raising=False,
    )

    def create_blueprint(project_root, host, port):
        return Blueprint("badmeta", __name__, url_prefix="/modules/badmeta")

    app = Flask(__name__)
    status_file = isolated_db.parent / ".actifix" / "module_statuses.json"

    before = _count_agent_voice()
    ok = api._register_module_blueprint(
        app,
        "badmeta",
        create_blueprint,
        project_root=isolated_db.parent,
        host="127.0.0.1",
        port=5001,
        status_file=status_file,
        access_rule=api.MODULE_ACCESS_PUBLIC,
        register_access=lambda *_: None,
        register_rate_limit=lambda *_: None,
        depgraph_edges=set(),
    )
    assert ok is False
    assert _count_agent_voice() == before + 1
