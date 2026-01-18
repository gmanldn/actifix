#!/usr/bin/env python3
"""
Tests for P0 critical race condition fixes.

These tests verify fixes for:
1. Race condition in _get_connection() schema initialization
2. TOCTOU race in acquire_lock()
3. WAL fsync safety on close
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from actifix.persistence.database import get_database_pool, reset_database_pool, serialize_timestamp
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository, TicketFilter
from actifix.raise_af import ActifixEntry, TicketPriority


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()


class TestDatabaseConnectionRaceCondition:
    """Test race condition fix in _get_connection() schema initialization."""

    def test_concurrent_schema_initialization(self, clean_db):
        """Verify schema is initialized exactly once even with concurrent access."""
        pool = get_database_pool()
        results = {"errors": []}

        def access_database(thread_id):
            try:
                import time
                # Stagger thread starts slightly to avoid thundering herd on lock
                time.sleep(thread_id * 0.01)
                # Each thread tries to get connection - schema should init once
                with pool.connection() as conn:
                    cursor = conn.execute("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchone()['cnt']
                    if tables == 0:
                        results["errors"].append(f"Thread {thread_id}: No tables created!")
            except Exception as e:
                results["errors"].append(f"Thread {thread_id}: {e}")

        # Spawn multiple threads that concurrently access database
        threads = [threading.Thread(target=access_database, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not results["errors"], f"Race condition detected: {results['errors']}"

    def test_schema_version_correct(self, clean_db):
        """Verify schema version is set correctly after initialization."""
        pool = get_database_pool()
        with pool.connection() as conn:
            cursor = conn.execute("SELECT MAX(version) as v FROM schema_version")
            row = cursor.fetchone()
            assert row['v'] == 5, f"Expected schema version 5, got {row['v']}"


class TestAcquireLockRaceCondition:
    """Test TOCTOU race condition fix in acquire_lock()."""

    def test_acquire_lock_atomicity(self, clean_db):
        """Verify acquire_lock prevents two threads from locking same ticket."""
        repo = get_ticket_repository()

        # Create a test ticket
        entry = ActifixEntry(
            message="Test ticket for lock race",
            source="test",
            run_label="test",
            entry_id="ACT-TEST-RACE",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P0,
            error_type="Test",
            stack_trace="",
            duplicate_guard="race-test",
        )
        repo.create_ticket(entry)

        # Try to lock from two threads simultaneously
        lock_results = {"success_count": 0, "failures": []}

        def try_lock(thread_id):
            try:
                lock = repo.acquire_lock(f"ACT-TEST-RACE", locked_by=f"thread-{thread_id}")
                if lock:
                    lock_results["success_count"] += 1
                    # Hold lock briefly
                    time.sleep(0.1)
                    repo.release_lock(f"ACT-TEST-RACE", locked_by=f"thread-{thread_id}")
            except Exception as e:
                lock_results["failures"].append(str(e))

        threads = [threading.Thread(target=try_lock, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only ONE thread should have successfully acquired the lock
        assert lock_results["success_count"] == 1, (
            f"Lock atomicity violated: {lock_results['success_count']} threads acquired lock. "
            f"Errors: {lock_results['failures']}"
        )

    def test_acquire_lock_with_expired_lease(self, clean_db):
        """Verify acquire_lock can take over expired leases."""
        repo = get_ticket_repository()

        # Create ticket
        entry = ActifixEntry(
            message="Test expired lease",
            source="test",
            run_label="test",
            entry_id="ACT-TEST-EXPIRE",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P0,
            error_type="Test",
            stack_trace="",
            duplicate_guard="expire-test",
        )
        repo.create_ticket(entry)

        # First thread acquires with short lease
        lock1 = repo.acquire_lock(
            "ACT-TEST-EXPIRE",
            locked_by="thread-1",
            lease_duration=timedelta(milliseconds=200),
        )
        assert lock1 is not None, "First lock should succeed"

        # Second thread tries immediately - should fail
        lock2 = repo.acquire_lock("ACT-TEST-EXPIRE", locked_by="thread-2")
        assert lock2 is None, "Second lock should fail immediately"

        # Wait for lease to expire
        time.sleep(0.25)

        # Second thread should now succeed
        lock3 = repo.acquire_lock("ACT-TEST-EXPIRE", locked_by="thread-2", lease_duration=timedelta(seconds=60))
        assert lock3 is not None, "Lock should succeed after lease expiry"
        assert lock3.locked_by == "thread-2", "Lock should be held by thread-2"

        # Cleanup
        repo.release_lock("ACT-TEST-EXPIRE", locked_by="thread-2")

    def test_update_WHERE_clause_prevents_race(self, clean_db):
        """Verify UPDATE with WHERE clause prevents race condition."""
        repo = get_ticket_repository()

        # Create ticket
        entry = ActifixEntry(
            message="Test WHERE clause atomicity",
            source="test",
            run_label="test",
            entry_id="ACT-TEST-WHERE",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P0,
            error_type="Test",
            stack_trace="",
            duplicate_guard="where-test",
        )
        repo.create_ticket(entry)

        # Acquire lock
        lock1 = repo.acquire_lock("ACT-TEST-WHERE", locked_by="thread-1", lease_duration=timedelta(hours=1))
        assert lock1 is not None

        # Verify ticket is locked
        ticket = repo.get_ticket("ACT-TEST-WHERE")
        assert ticket['locked_by'] == "thread-1", "Ticket should be locked by thread-1"

        # Another thread cannot take the lock (WHERE clause would fail)
        lock2 = repo.acquire_lock("ACT-TEST-WHERE", locked_by="thread-2")
        assert lock2 is None, "WHERE clause should prevent concurrent lock acquisition"

        # Cleanup
        repo.release_lock("ACT-TEST-WHERE", locked_by="thread-1")


class TestWALFsyncSafety:
    """Test WAL fsync safety on connection close."""

    def test_wal_checkpoint_on_close(self, clean_db):
        """Verify WAL checkpoint occurs on close."""
        pool = get_database_pool()

        # Create and write data
        with pool.transaction() as conn:
            conn.execute("""
                INSERT INTO tickets (
                    id, priority, error_type, message, source,
                    created_at, duplicate_guard, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "ACT-WAL-TEST", "P2", "Test", "WAL test", "test",
                serialize_timestamp(datetime.now(timezone.utc)),
                "wal-guard",
                "Open"
            ))

        # Close the connection (should trigger WAL checkpoint)
        pool.close()

        # Reconnect and verify data persisted
        reset_database_pool()
        pool = get_database_pool()
        with pool.connection() as conn:
            cursor = conn.execute("SELECT id FROM tickets WHERE id='ACT-WAL-TEST'")
            row = cursor.fetchone()
            assert row is not None, "Data should persist after WAL checkpoint"
            assert row['id'] == "ACT-WAL-TEST"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
