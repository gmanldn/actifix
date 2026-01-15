#!/usr/bin/env python3
"""
Tests for soft-delete functionality.

Verifies that:
1. Soft-delete marks tickets as deleted without removing data
2. Soft-deleted tickets are excluded from normal queries
3. Soft-deleted tickets can be recovered
4. Hard-delete option permanently removes records
5. Statistics properly count soft-deleted tickets
"""

import threading
from datetime import datetime, timezone
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


def create_test_ticket(repo, ticket_id=None, priority=TicketPriority.P2):
    """Create a test ticket."""
    entry = ActifixEntry(
        message="Test ticket for soft-delete",
        source="test",
        run_label="test",
        entry_id=ticket_id or f"ACT-TEST-{datetime.now().timestamp()}",
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="Test",
        stack_trace="",
        duplicate_guard=f"soft-delete-test-{datetime.now().timestamp()}",
    )
    repo.create_ticket(entry)
    return entry.entry_id


class TestSoftDeleteBasics:
    """Test soft-delete basic functionality."""

    def test_soft_delete_marks_deleted(self, clean_db):
        """Verify soft-delete marks ticket as deleted without removing data."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-SOFT-001")

        # Delete ticket (soft-delete by default)
        success = repo.delete_ticket(ticket_id)
        assert success is True

        # Ticket should not appear in normal queries
        tickets = repo.get_tickets()
        assert ticket_id not in [t['id'] for t in tickets]

        # But the record should still exist in deleted state
        with repo.pool.connection() as conn:
            cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            assert row is not None, "Ticket data should still exist"
            assert row['deleted'] == 1, "Ticket should be marked as deleted"
            assert row['deleted_at'] is not None, "deleted_at timestamp should be set"

    def test_soft_delete_excludes_from_get_tickets(self, clean_db):
        """Verify soft-deleted tickets are excluded from get_tickets()."""
        repo = get_ticket_repository()

        # Create multiple tickets
        ticket1 = create_test_ticket(repo, "ACT-SOFT-002")
        ticket2 = create_test_ticket(repo, "ACT-SOFT-003")
        ticket3 = create_test_ticket(repo, "ACT-SOFT-004")

        # Verify all three appear initially
        tickets = repo.get_tickets()
        ticket_ids = [t['id'] for t in tickets]
        assert ticket1 in ticket_ids
        assert ticket2 in ticket_ids
        assert ticket3 in ticket_ids

        # Soft-delete one ticket
        repo.delete_ticket(ticket2)

        # Verify it's excluded
        tickets = repo.get_tickets()
        ticket_ids = [t['id'] for t in tickets]
        assert ticket1 in ticket_ids
        assert ticket2 not in ticket_ids  # Should be excluded
        assert ticket3 in ticket_ids

    def test_get_deleted_tickets(self, clean_db):
        """Verify get_deleted_tickets() returns only soft-deleted tickets."""
        repo = get_ticket_repository()

        # Create and delete some tickets
        ticket1 = create_test_ticket(repo, "ACT-SOFT-005")
        ticket2 = create_test_ticket(repo, "ACT-SOFT-006")
        ticket3 = create_test_ticket(repo, "ACT-SOFT-007")

        repo.delete_ticket(ticket1)
        repo.delete_ticket(ticket3)

        # Get deleted tickets
        deleted = repo.get_deleted_tickets()
        deleted_ids = [t['id'] for t in deleted]

        assert ticket1 in deleted_ids
        assert ticket2 not in deleted_ids
        assert ticket3 in deleted_ids
        assert len(deleted) == 2

    def test_recover_soft_deleted_ticket(self, clean_db):
        """Verify deleted tickets can be recovered."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-SOFT-008")

        # Soft-delete
        repo.delete_ticket(ticket_id)

        # Verify it's deleted
        deleted = repo.get_deleted_tickets()
        assert ticket_id in [t['id'] for t in deleted]

        # Recover
        success = repo.recover_ticket(ticket_id)
        assert success is True

        # Verify it's restored
        tickets = repo.get_tickets()
        assert ticket_id in [t['id'] for t in tickets]

        deleted = repo.get_deleted_tickets()
        assert ticket_id not in [t['id'] for t in deleted]

        # Verify deleted fields are cleared
        ticket = repo.get_ticket(ticket_id)
        assert ticket['deleted'] is False
        assert ticket['deleted_at'] is None

    def test_recover_nonexistent_deleted_ticket(self, clean_db):
        """Verify recover fails for non-deleted or nonexistent tickets."""
        repo = get_ticket_repository()

        # Try to recover nonexistent ticket
        success = repo.recover_ticket("ACT-NONEXISTENT")
        assert success is False

        # Create ticket but don't delete it
        ticket_id = create_test_ticket(repo, "ACT-SOFT-009")

        # Try to recover non-deleted ticket
        success = repo.recover_ticket(ticket_id)
        assert success is False


class TestSoftDeleteStats:
    """Test soft-delete impact on statistics."""

    def test_stats_exclude_soft_deleted(self, clean_db):
        """Verify get_stats() excludes soft-deleted tickets."""
        repo = get_ticket_repository()

        # Create tickets with different priorities
        p0_ticket = create_test_ticket(repo, "ACT-SOFT-010", TicketPriority.P0)
        p1_ticket = create_test_ticket(repo, "ACT-SOFT-011", TicketPriority.P1)
        p2_ticket = create_test_ticket(repo, "ACT-SOFT-012", TicketPriority.P2)

        # Get initial stats
        stats1 = repo.get_stats()
        total1 = stats1['total']

        # Delete one ticket
        repo.delete_ticket(p1_ticket)

        # Get new stats
        stats2 = repo.get_stats()
        total2 = stats2['total']

        # Total should decrease by 1
        assert total2 == total1 - 1
        assert stats2['by_priority']['P1'] == stats1['by_priority']['P1'] - 1

    def test_stats_track_deleted_count(self, clean_db):
        """Verify get_stats() includes count of deleted tickets."""
        repo = get_ticket_repository()

        # Create and delete some tickets
        ticket1 = create_test_ticket(repo, "ACT-SOFT-013")
        ticket2 = create_test_ticket(repo, "ACT-SOFT-014")

        # Initial deleted count should be 0
        stats1 = repo.get_stats()
        assert stats1['deleted'] == 0

        # Delete tickets
        repo.delete_ticket(ticket1)
        repo.delete_ticket(ticket2)

        # Deleted count should increase
        stats2 = repo.get_stats()
        assert stats2['deleted'] == 2


class TestHardDelete:
    """Test hard-delete functionality."""

    def test_hard_delete_removes_permanently(self, clean_db):
        """Verify hard-delete permanently removes data."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-SOFT-015")

        # Hard-delete
        success = repo.delete_ticket(ticket_id, soft_delete=False)
        assert success is True

        # Record should be completely gone
        with repo.pool.connection() as conn:
            cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            assert row is None, "Hard-deleted ticket should be completely removed"

        # Should not appear in deleted tickets
        deleted = repo.get_deleted_tickets()
        assert ticket_id not in [t['id'] for t in deleted]


class TestSoftDeleteFiltering:
    """Test soft-delete with various filters."""

    def test_filter_by_status_excludes_deleted(self, clean_db):
        """Verify status filters exclude soft-deleted tickets."""
        repo = get_ticket_repository()

        # Create open and completed tickets
        open_ticket = create_test_ticket(repo, "ACT-SOFT-016")
        completed_ticket = create_test_ticket(repo, "ACT-SOFT-017")

        # Mark one as completed
        repo.update_ticket(completed_ticket, {'status': 'Completed'})

        # Delete the completed one
        repo.delete_ticket(completed_ticket)

        # Filter by status
        completed = repo.get_tickets(TicketFilter(status="Completed"))
        assert completed_ticket not in [t['id'] for t in completed]

        open_tickets = repo.get_tickets(TicketFilter(status="Open"))
        assert open_ticket in [t['id'] for t in open_tickets]

    def test_filter_by_priority_excludes_deleted(self, clean_db):
        """Verify priority filters exclude soft-deleted tickets."""
        repo = get_ticket_repository()

        p0_ticket = create_test_ticket(repo, "ACT-SOFT-018", TicketPriority.P0)
        p1_ticket = create_test_ticket(repo, "ACT-SOFT-019", TicketPriority.P1)

        # Delete p0 ticket
        repo.delete_ticket(p0_ticket)

        # Filter by priority
        p0_tickets = repo.get_tickets(TicketFilter(priority="P0"))
        assert p0_ticket not in [t['id'] for t in p0_tickets]

        p1_tickets = repo.get_tickets(TicketFilter(priority="P1"))
        assert p1_ticket in [t['id'] for t in p1_tickets]


class TestSoftDeleteEdgeCases:
    """Test soft-delete edge cases."""

    def test_double_delete_soft_delete(self, clean_db):
        """Verify second soft-delete fails (already deleted)."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-SOFT-020")

        # First delete succeeds
        success1 = repo.delete_ticket(ticket_id, soft_delete=True)
        assert success1 is True

        # Second delete should fail (already deleted)
        success2 = repo.delete_ticket(ticket_id, soft_delete=True)
        assert success2 is False

    def test_delete_and_recover_cycle(self, clean_db):
        """Verify multiple delete/recover cycles work correctly."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo, "ACT-SOFT-021")

        for i in range(3):
            # Delete
            delete_success = repo.delete_ticket(ticket_id)
            assert delete_success is True

            # Recover
            recover_success = repo.recover_ticket(ticket_id)
            assert recover_success is True

            # Verify it's back
            ticket = repo.get_ticket(ticket_id)
            assert ticket is not None
            assert ticket['deleted'] is False

    def test_concurrent_soft_delete(self, clean_db):
        """Verify soft-delete is thread-safe."""
        repo = get_ticket_repository()
        results = {"errors": []}

        # Create a ticket
        ticket_id = create_test_ticket(repo, "ACT-SOFT-022")

        def try_delete():
            try:
                success = repo.delete_ticket(ticket_id)
                # Only the first thread should succeed
                if not success:
                    results["success"] = False
            except Exception as e:
                results["errors"].append(str(e))

        # Run delete from multiple threads
        threads = [threading.Thread(target=try_delete) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not results["errors"], f"Concurrency errors: {results['errors']}"

        # Ticket should be deleted
        deleted = repo.get_deleted_tickets()
        assert ticket_id in [t['id'] for t in deleted]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
