#!/usr/bin/env python3
"""
Tests for Ticket Completion Quality Gate System

Verifies that:
1. Tickets cannot be marked complete without completion_notes (min 20 chars)
2. Tickets cannot be marked complete without test_steps (min 10 chars)
3. Tickets cannot be marked complete without test_results (min 10 chars)
4. Validation errors prevent any database changes
5. Valid completions succeed and store evidence
"""

import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from actifix.do_af import mark_ticket_complete
from actifix.persistence.database import get_database_pool, reset_database_pool
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()


def create_test_ticket(repo, ticket_id=None) -> str:
    """Create a test ticket and return its ID."""
    entry = ActifixEntry(
        message="Test ticket for quality gate verification",
        source="test",
        run_label="test",
        entry_id=ticket_id or f"ACT-QUALITY-GATE-{datetime.now().timestamp()}",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P1,
        error_type="QualityGateTest",
        stack_trace="",
        duplicate_guard=f"quality-gate-{datetime.now().timestamp()}",
    )
    repo.create_ticket(entry)
    return entry.entry_id


class TestCompletionNotesValidation:
    """Test completion_notes field validation."""

    def test_empty_completion_notes_rejected(self, clean_db):
        """Verify empty completion_notes are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="completion_notes required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="",  # ❌ EMPTY
                test_steps="Ran pytest tests successfully",
                test_results="All 10 tests passed"
            )

        # Verify ticket remains Open
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'
        assert ticket['completed'] == 0

    def test_completion_notes_too_short(self, clean_db):
        """Verify completion_notes below 20 chars are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="completion_notes required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="Fixed the bug",  # ❌ 13 chars, need 20
                test_steps="Ran pytest tests successfully",
                test_results="All 10 tests passed"
            )

        # Verify ticket remains Open
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_completion_notes_whitespace_only(self, clean_db):
        """Verify whitespace-only completion_notes are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="completion_notes required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="    \n   \t  ",  # ❌ Just whitespace
                test_steps="Ran pytest tests successfully",
                test_results="All 10 tests passed"
            )

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_completion_notes_minimum_length_accepted(self, clean_db):
        """Verify exactly 20 chars in completion_notes is accepted."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        # Exactly 20 chars
        notes = "x" * 20

        success = repo.mark_complete(
            ticket_id,
            completion_notes=notes,
            test_steps="Ran pytest tests successfully",
            test_results="All 10 tests passed"
        )

        assert success is True
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Completed'
        assert ticket['completion_notes'] == notes


class TestTestStepsValidation:
    """Test test_steps field validation."""

    def test_empty_test_steps_rejected(self, clean_db):
        """Verify empty test_steps are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="test_steps required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="Fixed null pointer by adding validation at lines 42-48",
                test_steps="",  # ❌ EMPTY
                test_results="All 10 tests passed"
            )

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_test_steps_too_short(self, clean_db):
        """Verify test_steps below 10 chars are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="test_steps required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="Fixed null pointer by adding validation at lines 42-48",
                test_steps="Tested",  # ❌ 6 chars, need 10
                test_results="All 10 tests passed"
            )

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_test_steps_minimum_length_accepted(self, clean_db):
        """Verify exactly 10 chars in test_steps is accepted."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        # Exactly 10 chars
        steps = "x" * 10

        success = repo.mark_complete(
            ticket_id,
            completion_notes="Fixed null pointer by adding validation at lines 42-48",
            test_steps=steps,
            test_results="All 10 tests passed"
        )

        assert success is True
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Completed'
        assert ticket['test_steps'] == steps


class TestTestResultsValidation:
    """Test test_results field validation."""

    def test_empty_test_results_rejected(self, clean_db):
        """Verify empty test_results are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="test_results required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="Fixed null pointer by adding validation at lines 42-48",
                test_steps="Ran pytest test_validation.py with -v flag",
                test_results=""  # ❌ EMPTY
            )

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_test_results_too_short(self, clean_db):
        """Verify test_results below 10 chars are rejected."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        with pytest.raises(ValueError, match="test_results required"):
            repo.mark_complete(
                ticket_id,
                completion_notes="Fixed null pointer by adding validation at lines 42-48",
                test_steps="Ran pytest test_validation.py with -v flag",
                test_results="All pass"  # ❌ 8 chars, need 10
            )

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_test_results_minimum_length_accepted(self, clean_db):
        """Verify exactly 10 chars in test_results is accepted."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        # Exactly 10 chars
        results = "x" * 10

        success = repo.mark_complete(
            ticket_id,
            completion_notes="Fixed null pointer by adding validation at lines 42-48",
            test_steps="Ran pytest test_validation.py with -v flag",
            test_results=results
        )

        assert success is True
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Completed'
        assert ticket['test_results'] == results


class TestSuccessfulCompletion:
    """Test successful ticket completion with valid evidence."""

    def test_complete_with_all_required_fields(self, clean_db):
        """Verify ticket completes successfully with all required fields."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        success = repo.mark_complete(
            ticket_id,
            completion_notes="Fixed null pointer exception by adding validation at lines 42-48 in database.py. Defensive checks prevent NullPointerException.",
            test_steps="Ran pytest test_database.py with -v. Added 15 new unit tests. Manual regression testing on 5 scenarios. Verified with gdb debugger.",
            test_results="All 47 tests passing. 99% code coverage. Zero memory leaks detected. Graceful error handling verified. Performance improved 35%."
        )

        assert success is True

        # Verify all fields stored correctly
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Completed'
        assert ticket['completed'] == 1
        assert ticket['documented'] == 1
        assert ticket['functioning'] == 1
        assert ticket['tested'] == 1

        # Verify evidence stored
        assert "null pointer" in ticket['completion_notes'].lower()
        assert "pytest" in ticket['test_steps'].lower()
        assert "all" in ticket['test_results'].lower()

    def test_complete_with_optional_fields(self, clean_db):
        """Verify optional fields can be provided."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        success = repo.mark_complete(
            ticket_id,
            completion_notes="Fixed null pointer exception by adding validation at lines 42-48",
            test_steps="Ran pytest test_database.py with full coverage",
            test_results="All 47 tests passing with 99% code coverage",
            summary="Database validation hardening",
            test_documentation_url="test/test_database.py:42-158"
        )

        assert success is True

        ticket = repo.get_ticket(ticket_id)
        assert ticket['completion_summary'] == "Database validation hardening"
        assert ticket['test_documentation_url'] == "test/test_database.py:42-158"

    def test_complete_idempotency(self, clean_db):
        """Verify cannot complete already-completed ticket."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        # First completion succeeds
        success1 = repo.mark_complete(
            ticket_id,
            completion_notes="Fixed the issue by adding proper validation checks",
            test_steps="Ran pytest test suite completely",
            test_results="All tests passing with excellent coverage"
        )
        assert success1 is True

        # Second completion fails (ticket already completed)
        success2 = repo.mark_complete(
            ticket_id,
            completion_notes="Different notes for second completion attempt",
            test_steps="Different test steps",
            test_results="Different test results"
        )
        assert success2 is False


class TestValidationErrorHandling:
    """Test error handling in application layer."""

    def test_do_af_mark_complete_validation_failure(self, clean_db, monkeypatch):
        """Verify mark_ticket_complete handles validation failures."""
        monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        # Try to complete with invalid completion_notes
        success = mark_ticket_complete(
            ticket_id,
            completion_notes="Too short",  # ❌ Only 9 chars
            test_steps="Ran pytest tests successfully",
            test_results="All tests passing"
        )

        # Should return False, not raise
        assert success is False

        # Ticket should remain Open
        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Open'

    def test_do_af_mark_complete_valid(self, clean_db, monkeypatch):
        """Verify mark_ticket_complete succeeds with valid data."""
        monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        success = mark_ticket_complete(
            ticket_id,
            completion_notes="Fixed null pointer by adding proper validation checks throughout database module",
            test_steps="Ran pytest test_database.py with full coverage and manual testing",
            test_results="All 47 tests passing with 99% code coverage and zero memory leaks"
        )

        assert success is True

        ticket = repo.get_ticket(ticket_id)
        assert ticket['status'] == 'Completed'


class TestDataIntegrity:
    """Test that validation prevents partial/corrupt states."""

    def test_validation_failure_no_side_effects(self, clean_db):
        """Verify validation failure doesn't corrupt ticket state."""
        repo = get_ticket_repository()
        ticket_id = create_test_ticket(repo)

        original_ticket = repo.get_ticket(ticket_id)
        original_status = original_ticket['status']

        # Try invalid completion
        try:
            repo.mark_complete(
                ticket_id,
                completion_notes="",  # ❌ Invalid
                test_steps="Valid test steps that are long enough",
                test_results="Valid test results that are long enough"
            )
        except ValueError:
            pass

        # Verify no changes made
        current_ticket = repo.get_ticket(ticket_id)
        assert current_ticket['status'] == original_status
        assert current_ticket['completed'] == original_ticket['completed']
        assert current_ticket['completion_notes'] == original_ticket['completion_notes']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
