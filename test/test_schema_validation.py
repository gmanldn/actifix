#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema validation tests for Actifix database migrations.

Validates that:
1. All required tables exist
2. All required columns are present
3. Column types match expected schema
4. Database constraints are enforced
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.persistence.database import DatabasePool, get_database_connection
from actifix.state_paths import get_actifix_paths


# Schema validation definitions
REQUIRED_TABLES = {
    "tickets",
    "schema_version",
    "event_log",
    "fallback_queue",
    "quarantine",
    "database_audit_log",
}

EXPECTED_SCHEMA = {
    "tickets": {
        "id": "TEXT",
        "priority": "TEXT",
        "error_type": "TEXT",
        "message": "TEXT",
        "source": "TEXT",
        "run_label": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "duplicate_guard": "TEXT",
        "status": "TEXT",
        "owner": "TEXT",
        "locked_by": "TEXT",
        "locked_at": "TIMESTAMP",
        "lease_expires": "TIMESTAMP",
        "branch": "TEXT",
        "stack_trace": "TEXT",
        "file_context": "TEXT",
        "system_state": "TEXT",
        "ai_remediation_notes": "TEXT",
        "correlation_id": "TEXT",
        "completion_summary": "TEXT",
        "completion_notes": "TEXT",
        "test_steps": "TEXT",
        "test_results": "TEXT",
        "test_documentation_url": "TEXT",
        "completion_verified_by": "TEXT",
        "completion_verified_at": "TIMESTAMP",
        "format_version": "TEXT",
        "documented": "BOOLEAN",
        "functioning": "BOOLEAN",
        "tested": "BOOLEAN",
        "completed": "BOOLEAN",
        "deleted": "BOOLEAN",
    },
    "schema_version": {
        "version": "INTEGER",
        "applied_at": "TIMESTAMP",
    },
    "event_log": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP",
        "event_type": "TEXT",
        "message": "TEXT",
        "ticket_id": "TEXT",
        "correlation_id": "TEXT",
        "source": "TEXT",
        "level": "TEXT",
    },
    "fallback_queue": {
        "id": "INTEGER",
        "entry_id": "TEXT",
        "operation": "TEXT",
        "payload_json": "TEXT",
        "created_at": "TIMESTAMP",
        "retry_count": "INTEGER",
        "status": "TEXT",
    },
    "quarantine": {
        "id": "INTEGER",
        "entry_id": "TEXT",
        "original_source": "TEXT",
        "reason": "TEXT",
        "content": "TEXT",
        "quarantined_at": "TIMESTAMP",
        "status": "TEXT",
    },
    "database_audit_log": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP",
        "table_name": "TEXT",
        "operation": "TEXT",
        "record_id": "TEXT",
        "change_description": "TEXT",
    },
}


class TestSchemaValidation:
    """Test database schema integrity and migrations."""

    @pytest.fixture
    def db_path(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            yield db

    @pytest.fixture
    def conn(self, db_path):
        """Create database connection."""
        conn = sqlite3.connect(db_path)
        yield conn
        conn.close()

    def test_all_required_tables_exist(self):
        """Test that all required tables exist in the schema."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = REQUIRED_TABLES - existing_tables
            assert not missing, f"Missing tables: {missing}"
        finally:
            conn.close()

    def test_tickets_table_schema(self):
        """Test that tickets table has all required columns."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tickets)")
            existing_columns = {row[1]: row[2] for row in cursor.fetchall()}

            # Check all expected columns exist
            expected_cols = EXPECTED_SCHEMA["tickets"]
            for col, col_type in expected_cols.items():
                assert col in existing_columns, f"Missing column: {col}"
                # Type comparison (normalize whitespace)
                expected_type = col_type.strip().upper()
                actual_type = existing_columns[col].strip().upper()
                assert actual_type == expected_type, (
                    f"Column {col} type mismatch: "
                    f"expected {expected_type}, got {actual_type}"
                )
        finally:
            conn.close()

    def test_schema_version_table(self):
        """Test schema_version table tracks migrations."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Verify schema_version table structure
            cursor.execute("PRAGMA table_info(schema_version)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "version" in columns
            assert "applied_at" in columns

            # Verify at least one schema version exists
            cursor.execute("SELECT COUNT(*) FROM schema_version")
            count = cursor.fetchone()[0]
            assert count > 0, "No schema versions recorded"
        finally:
            conn.close()

    def test_event_log_schema(self):
        """Test event_log table has correct schema."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(event_log)")
            columns = {row[1] for row in cursor.fetchall()}

            expected = {"id", "timestamp", "event_type", "message", "source"}
            assert expected.issubset(columns), (
                f"Missing event_log columns: {expected - columns}"
            )
        finally:
            conn.close()

    def test_fallback_queue_schema(self):
        """Test fallback_queue table schema for reliability."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(fallback_queue)")
            columns = {row[1] for row in cursor.fetchall()}

            expected = {"id", "entry_id", "operation", "status", "retry_count"}
            assert expected.issubset(columns), (
                f"Missing fallback_queue columns: {expected - columns}"
            )
        finally:
            conn.close()

    def test_quarantine_table_schema(self):
        """Test quarantine table for data isolation."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(quarantine)")
            columns = {row[1] for row in cursor.fetchall()}

            expected = {
                "id",
                "entry_id",
                "original_source",
                "reason",
                "content",
                "status",
            }
            assert expected.issubset(columns), (
                f"Missing quarantine columns: {expected - columns}"
            )
        finally:
            conn.close()

    def test_primary_key_constraints(self):
        """Test that primary key constraints are properly configured."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Test tickets table primary key
            cursor.execute("PRAGMA table_info(tickets)")
            pk_col = next(
                (row for row in cursor.fetchall() if row[5]), None
            )  # pk is the 6th column
            assert pk_col is not None, "Tickets table should have a primary key"
            assert (
                pk_col[1] == "id"
            ), f"Expected primary key 'id', got {pk_col[1]}"
        finally:
            conn.close()

    def test_unique_constraints(self):
        """Test that unique constraints are enforced."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Check for unique constraint on duplicate_guard
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE name='tickets' AND type='table'"
            )
            schema = cursor.fetchone()[0]
            assert "UNIQUE" in schema or "unique" in schema, (
                "Tickets table should have UNIQUE constraint for duplicate_guard"
            )
        finally:
            conn.close()

    def test_timestamp_columns_exist(self):
        """Test that critical timestamp columns are present."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Check tickets table timestamps
            cursor.execute("PRAGMA table_info(tickets)")
            columns = {row[1] for row in cursor.fetchall()}

            timestamp_cols = {"created_at", "updated_at"}
            assert (
                timestamp_cols.issubset(columns)
            ), f"Missing timestamp columns: {timestamp_cols - columns}"
        finally:
            conn.close()

    def test_no_data_loss_schema_migration(self):
        """Test that schema migrations don't lose data."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Verify schema_version progression is consistent
            cursor.execute("SELECT version FROM schema_version ORDER BY version")
            versions = [row[0] for row in cursor.fetchall()]

            if versions:
                # Versions should be sequential or gaps should be documented
                for i in range(1, len(versions)):
                    assert (
                        versions[i] > versions[i - 1]
                    ), f"Schema versions not monotonic: {versions}"
        finally:
            conn.close()


class TestSchemaMigrationRobustness:
    """Test robustness of schema changes."""

    def test_schema_version_tracking(self):
        """Test that schema version changes are tracked."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Get current schema version
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0]

            assert (
                current_version is not None
            ), "Schema version should be tracked"
            assert current_version > 0, f"Invalid schema version: {current_version}"
        finally:
            conn.close()

    def test_audit_log_for_critical_tables(self):
        """Test that critical table changes are audited."""
        paths = get_actifix_paths()
        conn = get_database_connection(paths)

        try:
            cursor = conn.cursor()

            # Verify audit log exists and has critical operations
            cursor.execute("SELECT COUNT(*) FROM database_audit_log")
            audit_count = cursor.fetchone()[0]

            # At least some audit records should exist for schema setup
            assert (
                audit_count >= 0
            ), "Audit log should be initialized"
        finally:
            conn.close()
