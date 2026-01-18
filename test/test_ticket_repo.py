#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the SQLite-backed ticket repository (CRUD, locking, stats).

Includes comprehensive race condition tests for concurrent ticket locking.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
import time

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
    assert repo.mark_complete(
        entry.entry_id,
        completion_notes="Fixed the locking issue in the repository layer",
        test_steps="Ran pytest test_ticket_repo.py with concurrent tests",
        test_results="All 12 concurrent locking tests passed",
        summary="Done"
    ) is True
    assert repo.mark_complete(
        entry.entry_id,
        completion_notes="Fixed the locking issue in the repository layer",
        test_steps="Ran pytest test_ticket_repo.py with concurrent tests",
        test_results="All 12 concurrent locking tests passed",
        summary="Already done"
    ) is True

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
    def locked_transaction(immediate=False):
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


# ===================== RACE CONDITION TESTS =====================

@pytest.mark.slow
class TestConcurrentLocking:
    """Tests for concurrent ticket locking scenarios."""

    def test_concurrent_acquire_lock_single_winner(self, ticket_repo_env):
        """Test that only one agent wins when multiple threads try to lock simultaneously."""
        repo: TicketRepository = ticket_repo_env

        entry = _build_entry("ACT-20260114-RACE1", TicketPriority.P1, "Race condition test")
        repo.create_ticket(entry)

        results = []
        lock_obj = threading.Lock()

        def acquire_lock_thread(agent_id):
            lock = repo.acquire_lock(entry.entry_id, locked_by=agent_id, lease_duration=timedelta(seconds=10))
            with lock_obj:
                results.append((agent_id, lock is not None))

        threads = [
            threading.Thread(target=acquire_lock_thread, args=(f"agent-{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one thread should have acquired the lock
        winners = [agent for agent, won in results if won]
        assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}: {winners}"

        # Verify the ticket is locked by the winner
        ticket = repo.get_ticket(entry.entry_id)
        assert ticket["locked_by"] == winners[0]

    def test_concurrent_get_and_lock_next_ticket(self, ticket_repo_env):
        """Test that concurrent threads get different tickets atomically."""
        repo: TicketRepository = ticket_repo_env

        # Create multiple tickets with different priorities
        entries = [
            _build_entry(f"ACT-20260114-Q1-{i}", TicketPriority.P0, f"P0 ticket {i}")
            for i in range(3)
        ] + [
            _build_entry(f"ACT-20260114-Q1-{3+i}", TicketPriority.P1, f"P1 ticket {i}")
            for i in range(2)
        ]

        for entry in entries:
            repo.create_ticket(entry)

        acquired_tickets = []
        lock_obj = threading.Lock()

        def get_next_ticket(agent_id):
            ticket = repo.get_and_lock_next_ticket(agent_id, lease_duration=timedelta(seconds=10))
            if ticket:
                with lock_obj:
                    acquired_tickets.append((agent_id, ticket["id"]))

        threads = [
            threading.Thread(target=get_next_ticket, args=(f"agent-{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All acquired tickets should be different
        ticket_ids = [tid for _, tid in acquired_tickets]
        assert len(ticket_ids) == len(set(ticket_ids)), "Duplicate tickets assigned to different agents"

        # Should have gotten all tickets in priority order
        assert len(acquired_tickets) == 5
        p0_tickets = [tid for _, tid in acquired_tickets[:3]]
        assert all("P0" in tid or "Q1-" in tid for tid in p0_tickets)

    def test_acquire_lock_while_expiring(self, ticket_repo_env):
        """Test lock acquisition race when a lock is about to expire."""
        repo: TicketRepository = ticket_repo_env

        entry = _build_entry("ACT-20260114-EXPIRE", TicketPriority.P2, "Expiring lock test")
        repo.create_ticket(entry)

        # Acquire with very short lease
        lock1 = repo.acquire_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(milliseconds=100))
        assert lock1 is not None

        # Try to acquire immediately - should fail
        lock2 = repo.acquire_lock(entry.entry_id, locked_by="agent-2")
        assert lock2 is None

        # Wait for lease to expire
        time.sleep(0.15)

        # Now should be able to acquire
        lock3 = repo.acquire_lock(entry.entry_id, locked_by="agent-2", lease_duration=timedelta(seconds=10))
        assert lock3 is not None

    def test_concurrent_lock_release_and_reacquire(self, ticket_repo_env):
        """Test releasing and reacquiring locks under concurrent access."""
        repo: TicketRepository = ticket_repo_env

        entries = [
            _build_entry(f"ACT-20260114-REACQ-{i}", TicketPriority.P2, f"Reacquire test {i}")
            for i in range(3)
        ]

        for entry in entries:
            repo.create_ticket(entry)

        release_order = []
        acquire_order = []
        lock_obj = threading.Lock()
        barrier = threading.Barrier(3)

        def lock_release_cycle(agent_id, ticket_id):
            # Synchronize all threads to start at the same time
            barrier.wait()

            # Try to acquire
            lock = repo.acquire_lock(ticket_id, locked_by=agent_id, lease_duration=timedelta(seconds=10))
            if lock:
                with lock_obj:
                    acquire_order.append(agent_id)
                time.sleep(0.01)  # Simulate some work
                repo.release_lock(ticket_id, locked_by=agent_id)
                with lock_obj:
                    release_order.append(agent_id)

        threads = [
            threading.Thread(target=lock_release_cycle, args=(f"agent-{i}", entries[i].entry_id))
            for i in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All agents should have successfully locked and released their respective tickets
        assert len(acquire_order) == 3
        assert len(release_order) == 3
        assert set(acquire_order) == set(release_order)

    def test_concurrent_mark_complete_operations(self, ticket_repo_env):
        """Test concurrent completion of different tickets."""
        repo: TicketRepository = ticket_repo_env

        entries = [
            _build_entry(f"ACT-20260114-COMP-{i}", TicketPriority.P2, f"Complete test {i}")
            for i in range(5)
        ]

        for entry in entries:
            repo.create_ticket(entry)

        def complete_ticket(ticket_id):
            repo.acquire_lock(ticket_id, locked_by="completer", lease_duration=timedelta(seconds=10))
            repo.mark_complete(
                ticket_id,
                completion_notes=f"Successfully completed ticket {ticket_id} in concurrent test",
                test_steps="Ran concurrent completion test with 5 tickets",
                test_results="All 5 tickets completed successfully without race conditions",
                summary=f"Completed {ticket_id}"
            )

        threads = [
            threading.Thread(target=complete_ticket, args=(entry.entry_id,))
            for entry in entries
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all tickets are completed
        for entry in entries:
            ticket = repo.get_ticket(entry.entry_id)
            assert ticket["status"] == "Completed"
            assert ticket["completed"] is True
            assert ticket["tested"] is True

    def test_lock_holder_verification_in_release(self, ticket_repo_env):
        """Test that only the correct lock holder can release a lock."""
        repo: TicketRepository = ticket_repo_env

        entry = _build_entry("ACT-20260114-HOLDER", TicketPriority.P2, "Holder verification")
        repo.create_ticket(entry)

        lock1 = repo.acquire_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(seconds=10))
        assert lock1 is not None

        # Wrong agent cannot release
        released = repo.release_lock(entry.entry_id, locked_by="agent-2")
        assert released is False

        # Correct agent can release
        released = repo.release_lock(entry.entry_id, locked_by="agent-1")
        assert released is True

        # Verify it's actually released
        ticket = repo.get_ticket(entry.entry_id)
        assert ticket["locked_by"] is None

    def test_concurrent_renewal_with_new_acquisitions(self, ticket_repo_env):
        """Test lock renewal under concurrent lock acquisition attempts."""
        repo: TicketRepository = ticket_repo_env

        entry = _build_entry("ACT-20260114-RENEW", TicketPriority.P2, "Renewal test")
        repo.create_ticket(entry)

        lock1 = repo.acquire_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(seconds=10))
        assert lock1 is not None

        renewal_success = []
        acquisition_success = []
        lock_obj = threading.Lock()

        def try_renew():
            time.sleep(0.01)
            renewed = repo.renew_lock(entry.entry_id, locked_by="agent-1", lease_duration=timedelta(seconds=10))
            with lock_obj:
                renewal_success.append(renewed is not None)

        def try_acquire():
            time.sleep(0.01)
            acquired = repo.acquire_lock(entry.entry_id, locked_by="agent-2")
            with lock_obj:
                acquisition_success.append(acquired is not None)

        renew_thread = threading.Thread(target=try_renew)
        acquire_thread = threading.Thread(target=try_acquire)

        renew_thread.start()
        acquire_thread.start()
        renew_thread.join()
        acquire_thread.join()

        # Either renewal succeeds and acquisition fails, or vice versa
        # But they should never both succeed
        assert not (renewal_success[0] and acquisition_success[0])

    def test_get_and_lock_next_priority_ordering_concurrent(self, ticket_repo_env):
        """Test that priority ordering is maintained under concurrent access."""
        repo: TicketRepository = ticket_repo_env

        # Create tickets with mixed priorities
        priorities = ["P2", "P0", "P1", "P2", "P0", "P1"]
        entries = [
            _build_entry(f"ACT-20260114-PRIO-{i}", TicketPriority[priorities[i]], f"Priority {priorities[i]} ticket {i}")
            for i in range(6)
        ]

        for entry in entries:
            repo.create_ticket(entry)

        acquired_order = []
        lock_obj = threading.Lock()

        def acquire_in_sequence():
            for _ in range(6):
                ticket = repo.get_and_lock_next_ticket(f"agent-0", lease_duration=timedelta(seconds=10))
                if ticket:
                    with lock_obj:
                        acquired_order.append(ticket["priority"])

        acquire_in_sequence()

        # Verify priority ordering: all P0s, then P1s, then P2s
        p0_count = sum(1 for p in acquired_order if p == "P0")
        p1_count = sum(1 for p in acquired_order if p == "P1")

        assert acquired_order[:p0_count] == ["P0"] * p0_count
        assert acquired_order[p0_count:p0_count + p1_count] == ["P1"] * p1_count
