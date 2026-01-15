#!/usr/bin/env python3
"""
Tests for ticket audit logging functionality.

Verifies that:
1. Ticket creation is logged to audit table
2. Ticket updates are logged with old and new values
3. Ticket deletions are logged
4. Audit logs include user context
5. Audit logs include timestamps and descriptions
"""

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from actifix.persistence.database import get_database_pool, reset_database_pool
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("ACTIFIX_USER", "test_user")
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()


def create_test_entry(ticket_id=None):
    """Create a test ticket entry."""
    return ActifixEntry(
        message="Test ticket for audit logging",
        source="test.py",
        run_label="test_run",
        entry_id=ticket_id or f"ACT-AUDIT-{datetime.now().timestamp()}",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P2,
        error_type="TestError",
        stack_trace="test stack trace",
        duplicate_guard=f"audit-test-{datetime.now().timestamp()}",
    )


class TestTicketCreationAudit:
    """Test audit logging of ticket creation."""

    def test_create_ticket_logged(self, clean_db):
        """Verify ticket creation is logged to audit table."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-001")
        repo.create_ticket(entry)

        # Verify audit entry exists
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM database_audit_log WHERE record_id = ? AND operation = 'INSERT'",
                ("ACT-AUDIT-001",)
            )
            audit = cursor.fetchone()
            assert audit is not None, "Ticket creation should be logged"
            assert audit['table_name'] == "tickets"
            assert audit['user_context'] == "test_user"

    def test_create_ticket_audit_includes_values(self, clean_db):
        """Verify creation audit log includes ticket details."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-002")
        repo.create_ticket(entry)

        # Verify audit entry has new values
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT new_values FROM database_audit_log WHERE record_id = ?",
                ("ACT-AUDIT-002",)
            )
            row = cursor.fetchone()
            assert row is not None
            new_values = json.loads(row['new_values'])

            assert new_values['id'] == "ACT-AUDIT-002"
            assert new_values['priority'] == "P2"
            assert new_values['status'] == "Open"
            assert new_values['source'] == "test.py"

    def test_create_ticket_audit_description(self, clean_db):
        """Verify creation audit includes description."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-003")
        repo.create_ticket(entry)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT change_description FROM database_audit_log WHERE record_id = ?",
                ("ACT-AUDIT-003",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert "Created ticket" in row['change_description']


class TestTicketUpdateAudit:
    """Test audit logging of ticket updates."""

    def test_update_ticket_logged(self, clean_db):
        """Verify ticket update is logged to audit table."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-004")
        repo.create_ticket(entry)

        # Update ticket
        repo.update_ticket("ACT-AUDIT-004", {"status": "In Progress", "owner": "alice"})

        # Verify update was logged
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM database_audit_log WHERE record_id = ? AND operation = 'UPDATE' ORDER BY id",
                ("ACT-AUDIT-004",)
            )
            audits = cursor.fetchall()
            assert len(audits) > 0, "Ticket update should be logged"

    def test_update_ticket_audit_includes_old_values(self, clean_db):
        """Verify update audit includes old values."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-005")
        repo.create_ticket(entry)

        # Update ticket
        repo.update_ticket("ACT-AUDIT-005", {"status": "In Progress"})

        # Verify old values are captured
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT old_values FROM database_audit_log WHERE record_id = ? AND operation = 'UPDATE' ORDER BY id DESC LIMIT 1",
                ("ACT-AUDIT-005",)
            )
            row = cursor.fetchone()
            assert row is not None
            old_values = json.loads(row['old_values'])
            assert old_values['status'] == "Open"

    def test_update_ticket_audit_includes_new_values(self, clean_db):
        """Verify update audit includes new values."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-006")
        repo.create_ticket(entry)

        # Update ticket
        repo.update_ticket("ACT-AUDIT-006", {"status": "Completed"})

        # Verify new values are captured
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT new_values FROM database_audit_log WHERE record_id = ? AND operation = 'UPDATE' ORDER BY id DESC LIMIT 1",
                ("ACT-AUDIT-006",)
            )
            row = cursor.fetchone()
            assert row is not None
            new_values = json.loads(row['new_values'])
            assert new_values['status'] == "Completed"

    def test_update_ticket_multiple_fields(self, clean_db):
        """Verify update with multiple fields is logged correctly."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-007")
        repo.create_ticket(entry)

        # Update multiple fields
        repo.update_ticket("ACT-AUDIT-007", {
            "status": "In Progress",
            "owner": "bob",
        })

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT change_description FROM database_audit_log WHERE record_id = ? AND operation = 'UPDATE' ORDER BY id DESC LIMIT 1",
                ("ACT-AUDIT-007",)
            )
            row = cursor.fetchone()
            assert row is not None
            desc = row['change_description']
            assert "status" in desc
            assert "owner" in desc


class TestTicketDeletionAudit:
    """Test audit logging of ticket deletion."""

    def test_soft_delete_logged(self, clean_db):
        """Verify soft delete is logged to audit table."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-008")
        repo.create_ticket(entry)

        # Soft delete
        repo.delete_ticket("ACT-AUDIT-008", soft_delete=True)

        # Verify deletion was logged (soft delete logs as UPDATE with SOFT_DELETE description)
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM database_audit_log WHERE record_id = ? AND operation = 'UPDATE' AND change_description LIKE '%SOFT_DELETE%'",
                ("ACT-AUDIT-008",)
            )
            audit = cursor.fetchone()
            assert audit is not None, "Soft delete should be logged"

    def test_hard_delete_logged(self, clean_db):
        """Verify hard delete is logged to audit table."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-009")
        repo.create_ticket(entry)

        # Hard delete
        repo.delete_ticket("ACT-AUDIT-009", soft_delete=False)

        # Verify deletion was logged
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM database_audit_log WHERE record_id = ? AND operation = 'DELETE'",
                ("ACT-AUDIT-009",)
            )
            audit = cursor.fetchone()
            assert audit is not None, "Hard delete should be logged"


class TestAuditUserContext:
    """Test user context in audit logs."""

    def test_audit_uses_actifix_user_env(self, clean_db, monkeypatch):
        """Verify audit uses ACTIFIX_USER environment variable."""
        monkeypatch.setenv("ACTIFIX_USER", "alice")

        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-010")
        repo.create_ticket(entry)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT user_context FROM database_audit_log WHERE record_id = ?",
                ("ACT-AUDIT-010",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['user_context'] == "alice"

    def test_audit_uses_user_env_fallback(self, clean_db, monkeypatch):
        """Verify audit falls back to USER environment variable."""
        monkeypatch.delenv("ACTIFIX_USER", raising=False)
        monkeypatch.setenv("USER", "bob")

        # Reset repo to pick up new env var
        reset_ticket_repository()
        reset_database_pool()

        repo = get_ticket_repository()
        pool = get_database_pool()

        entry = create_test_entry("ACT-AUDIT-011")
        repo.create_ticket(entry)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT user_context FROM database_audit_log WHERE record_id = ?",
                ("ACT-AUDIT-011",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['user_context'] == "bob"


class TestAuditTimestamp:
    """Test timestamp recording in audit logs."""

    def test_audit_records_timestamp(self, clean_db):
        """Verify audit log records timestamp."""
        repo = get_ticket_repository()
        pool = get_database_pool()

        before = datetime.now(timezone.utc)

        entry = create_test_entry("ACT-AUDIT-012")
        repo.create_ticket(entry)

        after = datetime.now(timezone.utc) + timedelta(seconds=1)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM database_audit_log WHERE record_id = ?",
                ("ACT-AUDIT-012",)
            )
            row = cursor.fetchone()
            assert row is not None

            ts_str = row['timestamp']
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            # Allow 1 second margin for timing
            assert (before - timedelta(seconds=1)) <= ts <= after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
