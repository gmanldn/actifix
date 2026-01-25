"""Tests for AgentVoice persistence and pruning."""

from __future__ import annotations

import os

import pytest

from actifix.persistence.database import reset_database_pool
from actifix.persistence.agent_voice_repo import AgentVoiceRepository


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    reset_database_pool()
    yield db_path
    reset_database_pool()
    monkeypatch.delenv("ACTIFIX_DB_PATH", raising=False)


def test_agent_voice_table_exists(isolated_db):
    repo = AgentVoiceRepository(max_rows=10)
    row_id = repo.append(agent_id="test", thought="hello", run_label="unit")
    assert row_id > 0
    assert repo.count() == 1


def test_agent_voice_prunes_to_max_rows(isolated_db):
    repo = AgentVoiceRepository(max_rows=5)
    for idx in range(10):
        repo.append(agent_id="test", thought=f"t{idx}", run_label="unit")

    assert repo.count() == 5
    recent = repo.list_recent(limit=10)
    assert [e.thought for e in recent] == ["t9", "t8", "t7", "t6", "t5"]

