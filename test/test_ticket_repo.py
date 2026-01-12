#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the SQLite-backed ticket repository (CRUD, locking, stats).
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlite3

from actifix.persistence.database import reset_database_pool, serialize_timestamp
from actifix.persistence.ticket_repo import (
    TicketRepository,
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


@pytest.fixture
def ticket_repo_env(tmp_path, monkeypatch):
    """Prepare a clean Actifix database environment for each test."""
    base = tmp_path
    data_dir = base / "actifix"
    state_dir = base / ".actifix"
    db_path = base / "data" / "actifix.db"

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))

    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)

    yield get_ticket_repository()

    reset_database_pool()
    reset_ticket_repository()


def _build_entry(ticket_id: str, priority: TicketPriority, message: str) -> ActifixEntry:
    """Helper to create a minimal ActifixEntry."""
    return ActifixEntry(
        message=message,
        source="tests/ticket_repo.py",
        run_label="repo-test",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


def test_ticket_repository_locking_and_completion(ticket_repo_env):
    repo: TicketRepository = ticket_repo_env

    entry = _build_entry("ACT-20260114-LOCK1", TicketPriority.P1, "Lock test")
    assert repo.create_ticket(entry) is True

    locked = repo.acquire_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(seconds=5))
    assert locked is not None
    stored = repo.get_ticket(entry.entry_id)
    assert stored["locked_by"] == "agent-1"

    # Lock once more while held should fail
    assert repo.acquire_lock(entry.entry_id, locked_by="agent-2") is None

    renewed = repo.renew_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(seconds=5))
    assert renewed is not None
    assert repo.release_lock(entry.entry_id, locked_by="agent-1") is True

    # Mark complete twice to ensure status remains completed
    assert repo.mark_complete(entry.entry_id, summary="Done") is True
    assert repo.mark_complete(entry.entry_id, summary="Already done") is True

    ticket = repo.get_ticket(entry.entry_id)
    assert ticket["status"] == "Completed"
    assert ticket["completion_summary"] == "Already done"

    stats = repo.get_stats()
    assert stats["total"] == 1
    assert stats["completed"] == 1
    assert stats["open"] == 0


def test_ticket_repository_next_ticket_and_duplicates(ticket_repo_env):
    repo: TicketRepository = ticket_repo_env

    entry1 = _build_entry("ACT-20260114-OPEN1", TicketPriority.P1, "Primary")
    entry2 = _build_entry("ACT-20260114-OPEN2", TicketPriority.P2, "Secondary")
    repo.create_ticket(entry1)
    repo.create_ticket(entry2)

    next_ticket = repo.get_and_lock_next_ticket("agent-2", priority_filter=["P0", "P1"])
    assert next_ticket is not None
    assert next_ticket["id"] == entry1.entry_id
    assert next_ticket["locked_by"] == "agent-2"

    # Duplicate guard query finds the earlier ticket
    duplicate = repo.check_duplicate_guard(entry1.duplicate_guard)
    assert duplicate is not None

    open_tickets = repo.get_open_tickets()
    assert any(t["id"] == entry2.entry_id for t in open_tickets)

    completed = repo.get_completed_tickets()
    assert completed == []


def test_acquire_lock_ignores_sqlite_locked(ticket_repo_env, monkeypatch):
    repo: TicketRepository = ticket_repo_env

    entry = _build_entry("ACT-20260114-LOCKERR", TicketPriority.P2, "Locked test")
    repo.create_ticket(entry)

    @contextmanager
    def locked_transaction():
        raise sqlite3.OperationalError("database is locked")
        yield

    monkeypatch.setattr(repo.pool, "transaction", locked_transaction)

    assert repo.acquire_lock(entry.entry_id, locked_by="agent-locked") is None


def test_ticket_repository_expired_lock_cleanup(ticket_repo_env):
    repo: TicketRepository = ticket_repo_env

    entry = _build_entry("ACT-20260114-EXP1", TicketPriority.P2, "Expiration test")
    repo.create_ticket(entry)
    assert repo.acquire_lock(entry.entry_id, locked_by="agent-x") is not None

    # Force the lease to expire by backdating the timestamp
    expired_ts = serialize_timestamp(datetime.now(timezone.utc) - timedelta(days=1))
    with repo.pool.transaction() as conn:
        conn.execute(
            "UPDATE tickets SET lease_expires = ? WHERE id = ?",
            (expired_ts, entry.entry_id),
        )

    expired = repo.get_expired_locks()
    assert any(ticket["id"] == entry.entry_id for ticket in expired)

    assert repo.cleanup_expired_locks() >= 1
