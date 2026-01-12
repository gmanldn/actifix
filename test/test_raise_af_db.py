#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the database-backed RaiseAF workflow.
"""

import os
import sys
from pathlib import Path

import pytest

# Allow importing from src/ directory for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.raise_af import record_error, replay_fallback_queue
from actifix.persistence.database import reset_database_pool
from actifix.persistence.ticket_repo import (
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.state_paths import get_actifix_paths, init_actifix_files


@pytest.fixture
def actifix_paths(tmp_path, monkeypatch):
    """Prepare Actifix paths and configuration for tests."""
    data_dir = tmp_path / "actifix"
    state_dir = tmp_path / ".actifix"
    db_path = tmp_path / "data" / "actifix.db"

    monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "1")
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    yield paths

    reset_database_pool()
    reset_ticket_repository()


def test_record_error_persists_to_database(actifix_paths):
    """record_error should create a row in `data/actifix.db`."""
    entry = record_error(
        error_type="DBTestError",
        message="Database persistence test",
        source="tests/test_raise_af_db.py:test_record_error_persists_to_database",
        priority="P2",
        run_label="db-test",
        paths=actifix_paths,
    )

    assert entry is not None
    assert Path(os.environ["ACTIFIX_DB_PATH"]).exists()

    repo = get_ticket_repository()
    stored = repo.get_ticket(entry.ticket_id)
    assert stored is not None
    assert stored["message"] == "Database persistence test"
    assert stored["priority"] == "P2"
    assert stored["status"] == "Open"


def test_duplicate_guard_prevents_duplicate_rows(actifix_paths):
    """Duplicate guard should prevent duplicate tickets."""
    record_error(
        error_type="DuplicateTest",
        message="Dup message",
        source="tests/test_raise_af_db.py:test_duplicate_guard_prevents_duplicate_rows",
        priority="P1",
        run_label="dup-test",
        paths=actifix_paths,
    )

    duplicate = record_error(
        error_type="DuplicateTest",
        message="Dup message",
        source="tests/test_raise_af_db.py:test_duplicate_guard_prevents_duplicate_rows",
        priority="P1",
        run_label="dup-test",
        paths=actifix_paths,
        skip_ai_notes=True,
    )

    assert duplicate is None
    repo = get_ticket_repository()
    stats = repo.get_stats()
    assert stats["open"] == 1


def test_fallback_queue_flushes_to_database(actifix_paths, monkeypatch):
    """When the database is unavailable, the fallback queue queues entries and replays them."""
    from actifix.persistence import ticket_repo

    original_repo_factory = ticket_repo.get_ticket_repository
    monkeypatch.setattr(ticket_repo, "get_ticket_repository", lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    entry = record_error(
        error_type="FallbackTest",
        message="Fallback queue test",
        source="tests/test_raise_af_db.py:test_fallback_queue_flushes_to_database",
        priority="P2",
        run_label="fallback-test",
        paths=actifix_paths,
        skip_ai_notes=True,
    )

    assert entry is not None
    queue_file = actifix_paths.state_dir / "actifix_fallback_queue.json"
    assert queue_file.exists()

    monkeypatch.setattr(ticket_repo, "get_ticket_repository", original_repo_factory)
    replayed = replay_fallback_queue(actifix_paths.base_dir)

    assert replayed >= 1
    assert not queue_file.exists()

    repo = get_ticket_repository()
    stored = repo.check_duplicate_guard(entry.duplicate_guard)
    assert stored is not None
