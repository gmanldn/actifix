"""
Test DoAF idempotency guard to prevent double-completing tickets.
"""

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Add src to path so we can import actifix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.do_af import mark_ticket_complete, get_open_tickets, get_completed_tickets, get_ticket_stats
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.persistence.database import reset_database_pool
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.persistence.event_repo import get_event_repository, EventFilter
from actifix.state_paths import get_actifix_paths


@pytest.fixture
def temp_actifix_paths(monkeypatch):
    """Create temporary Actifix paths for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        state_dir = base / ".actifix"
        state_dir.mkdir()
        db_path = base / "data" / "actifix.db"
        monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))

        paths = get_actifix_paths(
            project_root=base,
            base_dir=base / "actifix",
            state_dir=state_dir,
            logs_dir=base / "logs",
        )

        # Create directories
        paths.base_dir.mkdir(parents=True, exist_ok=True)
        paths.logs_dir.mkdir(parents=True, exist_ok=True)

        yield paths

        reset_database_pool()
        reset_ticket_repository()


def _create_ticket(ticket_id: str, priority: TicketPriority, message: str) -> None:
    repo = get_ticket_repository()
    entry = ActifixEntry(
        message=message,
        source="tests/do_af.py:1",
        run_label="test-run",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        stack_trace="",
        duplicate_guard=f"ACTIFIX-{ticket_id}",
    )
    repo.create_ticket(entry)


def test_idempotency_guard_prevents_double_completion(temp_actifix_paths):
    """Test that mark_ticket_complete skips already-completed tickets."""
    paths = temp_actifix_paths

    ticket_id = "ACT-20260101-TEST123"
    _create_ticket(ticket_id, TicketPriority.P3, "Idempotency test")

    # First call: mark as complete (should succeed)
    result1 = mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Fixed successfully", paths=paths
    )
    assert result1 is True

    # Second call: should be skipped
    result2 = mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Already fixed", paths=paths
    )
    assert result2 is False

    # Verify event log has skip event
    repo = get_event_repository()
    events = repo.get_events(EventFilter(event_type="TICKET_ALREADY_COMPLETED", limit=10))
    assert any(event.get("event_type") == "TICKET_ALREADY_COMPLETED" for event in events)
    assert any("idempotency_guard" in (event.get("extra_json") or "") for event in events)


def test_ticket_queries_use_database(temp_actifix_paths):
    """Test get_open_tickets/get_completed_tickets/get_ticket_stats in DB mode."""
    paths = temp_actifix_paths

    _create_ticket("ACT-20260101-OPEN1", TicketPriority.P1, "Open ticket 1")
    _create_ticket("ACT-20260101-OPEN2", TicketPriority.P2, "Open ticket 2")
    mark_ticket_complete("ACT-20260101-OPEN2", completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="done", paths=paths)

    open_tickets = get_open_tickets(paths)
    assert any(ticket.ticket_id == "ACT-20260101-OPEN1" for ticket in open_tickets)

    completed_tickets = get_completed_tickets(paths)
    assert any(ticket.ticket_id == "ACT-20260101-OPEN2" for ticket in completed_tickets)

    stats = get_ticket_stats(paths)
    assert stats["total"] >= 2
    assert stats["completed"] >= 1
