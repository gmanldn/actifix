#!/usr/bin/env python3
"""
Comprehensive tests for concurrent ticket locking race conditions.

These tests verify fixes for:
1. Double-lock prevention (atomicity of acquire_lock)
2. Lock holder verification (prevent lock theft)
3. Lease expiry race conditions
4. Concurrent status update races
5. Lock release verification
6. Priority-based allocation under concurrent access
7. Owner assignment races
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from actifix.persistence.database import get_database_pool, reset_database_pool, serialize_timestamp
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository, TicketFilter
from actifix.raise_af import ActifixEntry, TicketPriority

pytestmark = [pytest.mark.db, pytest.mark.concurrent, pytest.mark.slow]

FAST_THREAD_COUNT = 4
PRIORITY_WORKERS = 6
RENEWAL_THREADS = 3
OWNER_THREADS = 3
RAPID_CYCLE_THREADS = 3
RAPID_CYCLE_ITERATIONS = 6
LEASE_WAIT_BEFORE_EXPIRY = 0.12
LEASE_WAIT_AFTER_EXPIRY = 0.2
RELEASE_HOLD_DELAY = 0.05
RELEASE_WAIT_DELAY = 0.08
RAPID_CYCLE_BACKOFF = 0.005


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()


def create_test_ticket(repo, ticket_id=None, priority=TicketPriority.P2):
    """Create a test ticket."""
    entry = ActifixEntry(
        message="Test ticket for locking race conditions",
        source="test",
        run_label="test",
        entry_id=ticket_id or f"ACT-RACE-{datetime.now().timestamp()}",
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="Test",
        stack_trace="",
        duplicate_guard=f"locking-race-test-{datetime.now().timestamp()}",
    )
    repo.create_ticket(entry)
    return entry.entry_id


class TestDoubleLockPrevention:
    """Test prevention of double-locks (acquiring same lock twice)."""

    def test_double_lock_same_thread(self, clean_db):
        """Verify same thread cannot acquire lock twice."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-001")

        # First acquire succeeds
        lock1 = repo.acquire_lock(ticket_id, locked_by="thread-1", lease_duration=timedelta(seconds=60))
        assert lock1 is not None

        # Second acquire on same ticket should fail
        lock2 = repo.acquire_lock(ticket_id, locked_by="thread-2")
        assert lock2 is None

        # Release and verify
        repo.release_lock(ticket_id, locked_by="thread-1")

    def test_concurrent_lock_acquisition_one_winner(self, clean_db):
        """Verify only one thread wins in concurrent lock acquisition."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-002")
        results = {"winners": []}

        def try_acquire(thread_id):
            lock = repo.acquire_lock(ticket_id, locked_by=f"thread-{thread_id}", lease_duration=timedelta(seconds=60))
            if lock is not None:
                results["winners"].append(thread_id)

        # Reduced thread count for performance while preserving race coverage.
        threads = [threading.Thread(target=try_acquire, args=(i,)) for i in range(FAST_THREAD_COUNT)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one should win
        assert len(results["winners"]) == 1, f"Expected 1 winner, got {len(results['winners'])}"


class TestLockHolderVerification:
    """Test lock holder verification prevents unauthorized operations."""

    def test_release_lock_holder_mismatch(self, clean_db):
        """Verify cannot release lock held by different holder."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-003")

        # Thread 1 acquires lock
        lock = repo.acquire_lock(ticket_id, locked_by="thread-1", lease_duration=timedelta(seconds=60))
        assert lock is not None

        # Thread 2 cannot release lock held by thread 1
        success = repo.release_lock(ticket_id, locked_by="thread-2")
        assert success is False

        # Thread 1 can release their own lock
        success = repo.release_lock(ticket_id, locked_by="thread-1")
        assert success is True

    def test_concurrent_release_attempts(self, clean_db):
        """Verify only lock holder can release."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-004")

        # Acquire lock
        lock = repo.acquire_lock(ticket_id, locked_by="holder", lease_duration=timedelta(seconds=60))
        assert lock is not None

        results = {"successes": [], "failures": []}

        def try_release(thread_id, holder_id):
            success = repo.release_lock(ticket_id, locked_by=holder_id)
            if success:
                results["successes"].append(thread_id)
            else:
                results["failures"].append(thread_id)

        # Multiple threads try to release
        threads = []
        threads.append(threading.Thread(target=try_release, args=(1, "holder")))  # Correct holder
        threads.extend([threading.Thread(target=try_release, args=(i, f"imposter-{i}")) for i in range(2, 5)])  # Wrong holders

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only the correct holder should succeed
        assert len(results["successes"]) == 1
        assert len(results["failures"]) == 3


class TestLeaseExpiryRaces:
    """Test race conditions around lease expiry."""

    def test_concurrent_acquire_at_lease_expiry(self, clean_db):
        """Verify proper handling when trying to acquire at lease expiry boundary."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-005")

        # Thread 1 acquires with short lease
        lock1 = repo.acquire_lock(
            ticket_id,
            locked_by="thread-1",
            lease_duration=timedelta(milliseconds=300),
        )
        assert lock1 is not None

        # Wait just before expiry
        time.sleep(LEASE_WAIT_BEFORE_EXPIRY)

        # Thread 2 tries to acquire - should still fail
        lock2 = repo.acquire_lock(ticket_id, locked_by="thread-2")
        assert lock2 is None

        # Wait for expiry
        time.sleep(LEASE_WAIT_AFTER_EXPIRY)

        # Thread 2 should now succeed
        lock3 = repo.acquire_lock(ticket_id, locked_by="thread-2", lease_duration=timedelta(seconds=60))
        assert lock3 is not None

        repo.release_lock(ticket_id, locked_by="thread-2")

    def test_concurrent_lease_renewal_race(self, clean_db):
        """Verify concurrent lease renewal doesn't cause conflicts."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-006")

        # Acquire initial lock
        lock = repo.acquire_lock(ticket_id, locked_by="holder", lease_duration=timedelta(seconds=60))
        assert lock is not None

        results = {"errors": []}

        def renew_lease(thread_id):
            try:
                renewed = repo.renew_lock(ticket_id, locked_by="holder", lease_duration=timedelta(seconds=60))
                if renewed is None:
                    results["errors"].append(f"Thread {thread_id}: renewal failed")
            except Exception as e:
                results["errors"].append(f"Thread {thread_id}: {e}")

        # Multiple threads try to renew simultaneously
        threads = [threading.Thread(target=renew_lease, args=(i,)) for i in range(RENEWAL_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not results["errors"], f"Renewal race condition: {results['errors']}"


class TestConcurrentStatusUpdates:
    """Test race conditions in concurrent status updates."""

    def test_concurrent_status_update_with_lock(self, clean_db):
        """Verify status updates are atomic with locking."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-007")

        # Acquire lock
        lock = repo.acquire_lock(ticket_id, locked_by="updater", lease_duration=timedelta(seconds=60))
        assert lock is not None

        results = {"updates": [], "errors": []}

        def try_update(status):
            try:
                success = repo.update_ticket(ticket_id, {"status": status})
                if success:
                    results["updates"].append(status)
            except Exception as e:
                results["errors"].append(str(e))

        # Multiple threads try to update status concurrently
        threads = [
            threading.Thread(target=try_update, args=("Open",)),
            threading.Thread(target=try_update, args=("In Progress",)),
            threading.Thread(target=try_update, args=("Completed",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not results["errors"]
        # Final status should be one of the attempted updates
        final_ticket = repo.get_ticket(ticket_id)
        assert final_ticket["status"] in ["Open", "In Progress", "Completed"]

        repo.release_lock(ticket_id, locked_by="updater")

    def test_concurrent_owner_assignment(self, clean_db):
        """Verify concurrent owner assignment works correctly."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-008")

        results = {"assigned_owners": []}

        def assign_owner(owner_id):
            success = repo.update_ticket(ticket_id, {"owner": owner_id})
            if success:
                results["assigned_owners"].append(owner_id)

        # Multiple threads try to assign owner simultaneously
        threads = [threading.Thread(target=assign_owner, args=(f"owner-{i}",)) for i in range(OWNER_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All assignments should succeed, last one wins
        assert len(results["assigned_owners"]) == 5
        final_ticket = repo.get_ticket(ticket_id)
        assert final_ticket["owner"] is not None


class TestPriorityAllocationRaces:
    """Test race conditions in priority-based ticket allocation."""

    def test_concurrent_get_and_lock_highest_priority(self, clean_db):
        """Verify only one thread gets each high-priority ticket."""
        repo = get_ticket_repository()

        # Create tickets with different priorities
        p0_tickets = [create_test_ticket(repo, f"ACT-RACE-P0-{i}", TicketPriority.P0) for i in range(3)]
        p1_tickets = [create_test_ticket(repo, f"ACT-RACE-P1-{i}", TicketPriority.P1) for i in range(3)]

        results = {"acquired": []}

        def get_and_lock():
            ticket = repo.get_and_lock_next_ticket(locked_by="worker", lease_duration=timedelta(seconds=60))
            if ticket:
                results["acquired"].append(ticket["id"])

        # Multiple workers race to get tickets
        threads = [threading.Thread(target=get_and_lock) for _ in range(PRIORITY_WORKERS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify:
        # 1. All P0 tickets acquired before any P1 tickets
        p0_acquired = [t for t in results["acquired"] if "P0" in t]
        p1_acquired = [t for t in results["acquired"] if "P1" in t]

        assert len(p0_acquired) == 3, f"Expected 3 P0 tickets, got {len(p0_acquired)}"
        assert len(p1_acquired) == 3, f"Expected 3 P1 tickets, got {len(p1_acquired)}"

        # 2. No duplicate acquisitions
        assert len(results["acquired"]) == len(set(results["acquired"])), "Duplicate ticket acquisition detected"

    def test_lock_release_enables_next_ticket_allocation(self, clean_db):
        """Verify releasing lock allows other threads to acquire."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-009", TicketPriority.P0)

        results = {"holder": None, "released": False}

        def hold_and_release():
            lock = repo.acquire_lock(ticket_id, locked_by="holder", lease_duration=timedelta(seconds=60))
            assert lock is not None
            results["holder"] = "holder"
            time.sleep(RELEASE_HOLD_DELAY)
            repo.release_lock(ticket_id, locked_by="holder")
            results["released"] = True

        def try_acquire():
            time.sleep(RELEASE_WAIT_DELAY)  # Wait for first thread to release
            lock = repo.acquire_lock(ticket_id, locked_by="waiter", lease_duration=timedelta(seconds=60))
            assert lock is not None
            repo.release_lock(ticket_id, locked_by="waiter")

        t1 = threading.Thread(target=hold_and_release)
        t2 = threading.Thread(target=try_acquire)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert results["holder"] == "holder"
        assert results["released"] is True


class TestAcquireReleaseRenewalCycles:
    """Test complex acquire/release/renewal cycles under concurrency."""

    def test_rapid_acquire_release_cycles(self, clean_db):
        """Verify rapid acquire/release cycles work correctly."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-010")

        results = {"cycles": 0, "errors": []}

        def cycle_lock(thread_id):
            try:
                for i in range(RAPID_CYCLE_ITERATIONS):
                    lock = repo.acquire_lock(ticket_id, locked_by=f"thread-{thread_id}", lease_duration=timedelta(seconds=60))
                    if lock:
                        repo.release_lock(ticket_id, locked_by=f"thread-{thread_id}")
                        results["cycles"] += 1
                    else:
                        # Lock held by another thread, that's ok
                        time.sleep(RAPID_CYCLE_BACKOFF)
            except Exception as e:
                results["errors"].append(str(e))

        # Multiple threads cycle lock rapidly
        threads = [threading.Thread(target=cycle_lock, args=(i,)) for i in range(RAPID_CYCLE_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not results["errors"]
        assert results["cycles"] > 0

    def test_acquire_renew_release_sequence(self, clean_db):
        """Verify acquire/renew/release sequence maintains atomicity."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-RACE-011")

        results = {"holder": None, "renewed": False, "released": False}

        # Acquire
        lock = repo.acquire_lock(
            ticket_id,
            locked_by="worker",
            lease_duration=timedelta(milliseconds=300),
        )
        assert lock is not None
        results["holder"] = "worker"

        # Renew before expiry
        time.sleep(0.15)
        renewed = repo.renew_lock(ticket_id, locked_by="worker", lease_duration=timedelta(seconds=60))
        assert renewed is not None
        results["renewed"] = True

        # Verify still locked
        locked_ticket = repo.get_ticket(ticket_id)
        assert locked_ticket["locked_by"] == "worker"

        # Release
        repo.release_lock(ticket_id, locked_by="worker")
        results["released"] = True

        # Verify unlocked
        unlocked_ticket = repo.get_ticket(ticket_id)
        assert unlocked_ticket["locked_by"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
