#!/usr/bin/env python3
"""
Tests for database audit log functionality.

Verifies that:
1. Audit log table is created with correct schema
2. Database changes can be logged to the audit table
3. Audit log includes all relevant information
4. Schema migration v4→v5 works correctly
5. Audit log queries work properly
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from actifix.persistence.database import (
    get_database_pool,
    reset_database_pool,
    log_database_audit,
    serialize_json_field,
    deserialize_json_field,
)


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    reset_database_pool()
    yield
    reset_database_pool()


class TestDatabaseAuditLogSchema:
    """Test audit log table schema and creation."""

    def test_audit_log_table_created(self, clean_db):
        """Verify audit log table is created."""
        pool = get_database_pool()

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='database_audit_log'"
            )
            assert cursor.fetchone() is not None, "Audit log table should be created"

    def test_audit_log_table_columns(self, clean_db):
        """Verify audit log table has correct columns."""
        pool = get_database_pool()

        with pool.connection() as conn:
            cursor = conn.execute("PRAGMA table_info(database_audit_log)")
            columns = {row[1] for row in cursor.fetchall()}

            required_columns = {
                'id', 'timestamp', 'table_name', 'operation',
                'record_id', 'user_context', 'old_values', 'new_values',
                'change_description', 'ip_address', 'session_id'
            }

            assert required_columns.issubset(columns), \
                f"Missing columns: {required_columns - columns}"

    def test_audit_log_operation_constraint(self, clean_db):
        """Verify CHECK constraint on operation column."""
        pool = get_database_pool()

        # Valid operations should succeed
        for op in ['INSERT', 'UPDATE', 'DELETE']:
            with pool.transaction() as conn:
                conn.execute(
                    "INSERT INTO database_audit_log (table_name, operation) VALUES (?, ?)",
                    ('test_table', op)
                )

        # Invalid operation should fail
        with pytest.raises(Exception):
            with pool.transaction() as conn:
                conn.execute(
                    "INSERT INTO database_audit_log (table_name, operation) VALUES (?, ?)",
                    ('test_table', 'INVALID')
                )

    def test_audit_log_indexes_created(self, clean_db):
        """Verify audit log indexes are created."""
        pool = get_database_pool()

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='database_audit_log'"
            )
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                'idx_audit_log_timestamp',
                'idx_audit_log_table',
                'idx_audit_log_operation',
                'idx_audit_log_record_id',
                'idx_audit_log_user',
                'idx_audit_log_table_record',
            }

            assert expected_indexes.issubset(indexes), \
                f"Missing indexes: {expected_indexes - indexes}"


class TestDatabaseAuditLogging:
    """Test audit log entry creation."""

    def test_log_database_audit_basic(self, clean_db):
        """Verify basic audit log entry is recorded."""
        pool = get_database_pool()

        success = log_database_audit(
            pool=pool,
            table_name="tickets",
            operation="INSERT",
            record_id="ACT-TEST-001",
            user_context="alice",
            change_description="Created new ticket"
        )

        assert success is True

        # Verify entry was logged
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM database_audit_log WHERE record_id = ?",
                ("ACT-TEST-001",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['table_name'] == "tickets"
            assert row['operation'] == "INSERT"
            assert row['user_context'] == "alice"
            assert row['change_description'] == "Created new ticket"

    def test_log_database_audit_with_values(self, clean_db):
        """Verify audit log captures old and new values."""
        pool = get_database_pool()

        old_values = {"status": "Open", "owner": None}
        new_values = {"status": "In Progress", "owner": "bob"}

        success = log_database_audit(
            pool=pool,
            table_name="tickets",
            operation="UPDATE",
            record_id="ACT-TEST-002",
            user_context="bob",
            old_values=old_values,
            new_values=new_values,
            change_description="Updated ticket status"
        )

        assert success is True

        # Verify values are serialized correctly
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT old_values, new_values FROM database_audit_log WHERE record_id = ?",
                ("ACT-TEST-002",)
            )
            row = cursor.fetchone()
            assert row is not None

            stored_old = json.loads(row['old_values'])
            stored_new = json.loads(row['new_values'])

            assert stored_old == old_values
            assert stored_new == new_values

    def test_log_database_audit_with_context(self, clean_db):
        """Verify audit log captures IP and session context."""
        pool = get_database_pool()

        success = log_database_audit(
            pool=pool,
            table_name="event_log",
            operation="INSERT",
            record_id="LOG-001",
            user_context="charlie",
            ip_address="192.168.1.100",
            session_id="session-abc123",
            change_description="Logged event"
        )

        assert success is True

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT ip_address, session_id FROM database_audit_log WHERE record_id = ?",
                ("LOG-001",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['ip_address'] == "192.168.1.100"
            assert row['session_id'] == "session-abc123"

    def test_log_database_audit_timestamp(self, clean_db):
        """Verify audit log records timestamp."""
        from datetime import timedelta
        pool = get_database_pool()

        before = datetime.now(timezone.utc)

        log_database_audit(
            pool=pool,
            table_name="tickets",
            operation="DELETE",
            record_id="ACT-TEST-003",
            user_context="dave",
            change_description="Deleted ticket"
        )

        after = datetime.now(timezone.utc) + timedelta(seconds=1)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM database_audit_log WHERE record_id = ?",
                ("ACT-TEST-003",)
            )
            row = cursor.fetchone()
            assert row is not None

            timestamp_str = row['timestamp']
            timestamp = datetime.fromisoformat(timestamp_str)

            # Normalize to UTC for comparison
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Verify timestamp is within expected range (with 1 second margin for SQLite precision)
            assert (before - timedelta(seconds=1)) <= timestamp <= after


class TestAuditLogQueries:
    """Test querying the audit log."""

    def test_query_audit_log_by_table(self, clean_db):
        """Verify querying audit log by table name."""
        pool = get_database_pool()

        # Log changes to different tables
        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", record_id="T1", user_context="user1")
        log_database_audit(pool=pool, table_name="event_log", operation="INSERT", record_id="E1", user_context="user2")
        log_database_audit(pool=pool, table_name="tickets", operation="UPDATE", record_id="T2", user_context="user3")

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM database_audit_log WHERE table_name = 'tickets'"
            )
            row = cursor.fetchone()
            assert row['count'] == 2

    def test_query_audit_log_by_user(self, clean_db):
        """Verify querying audit log by user context."""
        pool = get_database_pool()

        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", user_context="alice")
        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", user_context="bob")
        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", user_context="alice")

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM database_audit_log WHERE user_context = 'alice'"
            )
            row = cursor.fetchone()
            assert row['count'] == 2

    def test_query_audit_log_by_operation(self, clean_db):
        """Verify querying audit log by operation type."""
        pool = get_database_pool()

        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", user_context="user")
        log_database_audit(pool=pool, table_name="tickets", operation="UPDATE", user_context="user")
        log_database_audit(pool=pool, table_name="tickets", operation="DELETE", user_context="user")
        log_database_audit(pool=pool, table_name="tickets", operation="UPDATE", user_context="user")

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM database_audit_log WHERE operation = 'UPDATE'"
            )
            row = cursor.fetchone()
            assert row['count'] == 2

    def test_query_audit_log_by_record_id(self, clean_db):
        """Verify querying audit log by record ID."""
        pool = get_database_pool()

        ticket_id = "ACT-AUDIT-001"
        log_database_audit(pool=pool, table_name="tickets", operation="INSERT", record_id=ticket_id)
        log_database_audit(pool=pool, table_name="tickets", operation="UPDATE", record_id=ticket_id)

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM database_audit_log WHERE record_id = ?",
                (ticket_id,)
            )
            row = cursor.fetchone()
            assert row['count'] == 2

    def test_query_audit_log_ordered_by_timestamp(self, clean_db):
        """Verify audit log can be queried in timestamp order."""
        pool = get_database_pool()

        for i in range(5):
            log_database_audit(pool=pool, table_name="tickets", operation="INSERT", record_id=f"T{i}")

        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM database_audit_log ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()

            # Verify ordering
            for i in range(len(rows) - 1):
                assert rows[i]['timestamp'] >= rows[i + 1]['timestamp']


class TestAuditLogMigration:
    """Test schema migration for audit log."""

    def test_schema_version_5_after_migration(self, clean_db):
        """Verify schema version is updated to 5 after migration."""
        pool = get_database_pool()

        with pool.connection() as conn:
            cursor = conn.execute("SELECT MAX(version) as v FROM schema_version")
            row = cursor.fetchone()
            assert row['v'] == 5, f"Expected schema version 5, got {row['v']}"

    def test_migration_from_v4_to_v5(self, clean_db):
        """Verify audit log table is created during migration."""
        pool = get_database_pool()

        # Verify table exists
        with pool.connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name='database_audit_log'"
            )
            count = cursor.fetchone()['count']
            assert count == 1, "Audit log table should exist after migration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
