#!/usr/bin/env python3
"""
Tests for field length limits (DoS prevention).

Verifies that:
1. Message field has maximum length limit
2. Source field has maximum length limit
3. Error type field has maximum length limit
4. Stack trace field has maximum length limit
5. Oversized fields are rejected on creation
6. Oversized fields are rejected on update
7. Normal sized fields are accepted
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from actifix.persistence.ticket_repo import (
    get_ticket_repository,
    reset_ticket_repository,
    FieldLengthError,
    MAX_MESSAGE_LENGTH,
    MAX_SOURCE_LENGTH,
    MAX_ERROR_TYPE_LENGTH,
    MAX_STACK_TRACE_LENGTH,
)
from actifix.persistence.database import get_database_pool, reset_database_pool
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


class TestMessageFieldLimits:
    """Test message field length validation."""

    def test_create_ticket_message_within_limit(self, clean_db):
        """Verify tickets with normal message length are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="This is a normal error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-001",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-1",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with normal message should be created"

    def test_create_ticket_message_exceeds_limit(self, clean_db):
        """Verify tickets with oversized message are rejected."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="x" * (MAX_MESSAGE_LENGTH + 1),
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-002",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-2",
        )

        with pytest.raises(FieldLengthError, match="message"):
            repo.create_ticket(entry)

    def test_create_ticket_message_at_limit(self, clean_db):
        """Verify tickets with message exactly at limit are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="x" * MAX_MESSAGE_LENGTH,
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-003",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-3",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket at message limit should be created"

    def test_update_ticket_message_exceeds_limit(self, clean_db):
        """Verify updates with oversized message are rejected."""
        repo = get_ticket_repository()

        # Create initial ticket
        entry = ActifixEntry(
            message="Initial message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-004",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-4",
        )
        repo.create_ticket(entry)

        # Try to update with oversized message
        with pytest.raises(FieldLengthError, match="message"):
            repo.update_ticket("ACT-TEST-004", {"message": "x" * (MAX_MESSAGE_LENGTH + 1)})


class TestSourceFieldLimits:
    """Test source field length validation."""

    def test_create_ticket_source_within_limit(self, clean_db):
        """Verify tickets with normal source length are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="path/to/file.py:123",
            run_label="test",
            entry_id="ACT-TEST-005",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-5",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with normal source should be created"

    def test_create_ticket_source_exceeds_limit(self, clean_db):
        """Verify tickets with oversized source are rejected."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="/" + "a" * (MAX_SOURCE_LENGTH + 100),  # Oversized path
            run_label="test",
            entry_id="ACT-TEST-006",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-6",
        )

        with pytest.raises(FieldLengthError, match="source"):
            repo.create_ticket(entry)

    def test_create_ticket_source_at_limit(self, clean_db):
        """Verify tickets with source exactly at limit are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="x" * MAX_SOURCE_LENGTH,
            run_label="test",
            entry_id="ACT-TEST-007",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-7",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with source at limit should be created"


class TestErrorTypeFieldLimits:
    """Test error type field length validation."""

    def test_create_ticket_error_type_within_limit(self, clean_db):
        """Verify tickets with normal error type are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-008",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="ValueError",
            stack_trace="",
            duplicate_guard="test-8",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with normal error type should be created"

    def test_create_ticket_error_type_exceeds_limit(self, clean_db):
        """Verify tickets with oversized error type are rejected."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-009",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="E" * (MAX_ERROR_TYPE_LENGTH + 1),
            stack_trace="",
            duplicate_guard="test-9",
        )

        with pytest.raises(FieldLengthError, match="error_type"):
            repo.create_ticket(entry)


class TestStackTraceFieldLimits:
    """Test stack trace field length validation."""

    def test_create_ticket_stack_trace_within_limit(self, clean_db):
        """Verify tickets with normal stack trace are accepted."""
        repo = get_ticket_repository()

        stack_trace = "\n".join([f"  File 'test/test_runner.py', line {i}" for i in range(100)])

        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-010",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace=stack_trace,
            duplicate_guard="test-10",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with normal stack trace should be created"

    def test_create_ticket_stack_trace_exceeds_limit(self, clean_db):
        """Verify tickets with oversized stack trace are rejected."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-011",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="S" * (MAX_STACK_TRACE_LENGTH + 1),
            duplicate_guard="test-11",
        )

        with pytest.raises(FieldLengthError, match="stack_trace"):
            repo.create_ticket(entry)

    def test_create_ticket_stack_trace_at_limit(self, clean_db):
        """Verify tickets with stack trace exactly at limit are accepted."""
        repo = get_ticket_repository()

        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-012",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="S" * MAX_STACK_TRACE_LENGTH,
            duplicate_guard="test-12",
        )

        success = repo.create_ticket(entry)
        assert success is True, "Ticket with stack trace at limit should be created"


class TestUpdateFieldLimits:
    """Test field limits on ticket updates."""

    def test_update_ticket_source_exceeds_limit(self, clean_db):
        """Verify source updates that exceed limit are rejected."""
        repo = get_ticket_repository()

        # Create initial ticket
        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-013",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-13",
        )
        repo.create_ticket(entry)

        # Try to update with oversized source
        with pytest.raises(FieldLengthError, match="source"):
            repo.update_ticket("ACT-TEST-013", {"source": "x" * (MAX_SOURCE_LENGTH + 1)})

    def test_update_multiple_fields_one_exceeds_limit(self, clean_db):
        """Verify update fails if any field exceeds limit."""
        repo = get_ticket_repository()

        # Create initial ticket
        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-014",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-14",
        )
        repo.create_ticket(entry)

        # Try to update with one valid and one oversized field
        with pytest.raises(FieldLengthError, match="message"):
            repo.update_ticket("ACT-TEST-014", {
                "status": "In Progress",
                "message": "x" * (MAX_MESSAGE_LENGTH + 1),
            })

    def test_update_ticket_valid_update_succeeds(self, clean_db):
        """Verify valid updates still work after validation."""
        repo = get_ticket_repository()

        # Create initial ticket
        entry = ActifixEntry(
            message="Error message",
            source="test/test_runner.py",
            run_label="test",
            entry_id="ACT-TEST-015",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            stack_trace="",
            duplicate_guard="test-15",
        )
        repo.create_ticket(entry)

        # Valid update should succeed
        success = repo.update_ticket("ACT-TEST-015", {
            "status": "In Progress",
            "owner": "alice",
        })
        assert success is True, "Valid update should succeed"


class TestLimitConstants:
    """Test that length limit constants are reasonable."""

    def test_limits_are_sensible(self):
        """Verify length limits are set to reasonable values."""
        # Source paths shouldn't be extremely long
        assert MAX_SOURCE_LENGTH < MAX_MESSAGE_LENGTH, "Source limit should be smaller than message"
        assert MAX_SOURCE_LENGTH < MAX_STACK_TRACE_LENGTH, "Source limit should be smaller than stack trace"

        # Stack traces can be long but not unlimited
        assert MAX_STACK_TRACE_LENGTH > MAX_MESSAGE_LENGTH, "Stack traces can be longer than messages"
        assert MAX_STACK_TRACE_LENGTH < 1000000, "Stack trace limit shouldn't be absurdly large"

        # All limits should be positive
        assert MAX_MESSAGE_LENGTH > 0
        assert MAX_SOURCE_LENGTH > 0
        assert MAX_ERROR_TYPE_LENGTH > 0
        assert MAX_STACK_TRACE_LENGTH > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
