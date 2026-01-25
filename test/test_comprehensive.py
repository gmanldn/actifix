"""
Comprehensive validation of Actifix 100-ticket suite (database-backed).
"""

from datetime import datetime, timezone

import pytest

from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority

pytestmark = pytest.mark.slow


@pytest.fixture
def comprehensive_tickets():
    repo = get_ticket_repository()
    for i in range(1, 101):
        ticket_id = f"ACT-20260101-T{i:03d}"
        entry = ActifixEntry(
            message=f"T{i:03d}: comprehensive test ticket",
            source="tests/comprehensive.py:1",
            run_label="comprehensive",
            entry_id=ticket_id,
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="ComprehensiveTest",
            stack_trace="",
            duplicate_guard=f"ACTIFIX-comp-{i:03d}",
        )
        repo.create_ticket(entry)
        if i <= 90:
            repo.mark_complete(
                ticket_id,
                completion_notes=(
                    f"Implementation: Comprehensive test {i:03d} completed successfully with full validation.\n"
                    "Files:\n"
                    "- src/actifix/do_af.py"
                ),
                test_steps="Ran comprehensive test suite with 100 tickets",
                test_results="90 tickets validated and marked complete with quality documentation",
                summary="Processed comprehensive test ticket"
            )
    return repo


def test_comprehensive_tickets_exist(comprehensive_tickets):
    """All 100 comprehensive test tickets should exist in the database."""
    tickets = comprehensive_tickets.get_tickets()
    t_tickets = [ticket for ticket in tickets if ticket["message"].startswith("T")]
    assert len(t_tickets) == 100


def test_comprehensive_tickets_in_completed_section(comprehensive_tickets):
    """At least 90 comprehensive tickets should be completed."""
    completed = comprehensive_tickets.get_completed_tickets()
    completed_t = [ticket for ticket in completed if ticket["message"].startswith("T")]
    assert len(completed_t) >= 90


def test_completion_summary_present(comprehensive_tickets):
    """Processed tickets should include a completion summary marker."""
    completed = comprehensive_tickets.get_completed_tickets()
    summaries = [ticket.get("completion_summary") for ticket in completed]
    assert any(summary and "Processed comprehensive test ticket" in summary for summary in summaries)
