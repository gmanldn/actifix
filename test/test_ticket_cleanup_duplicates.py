from datetime import datetime, timezone, timedelta

from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.persistence.ticket_cleanup import cleanup_duplicate_tickets


def test_cleanup_duplicate_tickets_auto_completes_older():
    repo = get_ticket_repository()
    now = datetime.now(timezone.utc)

    entries = [
        ActifixEntry(
            message="Duplicate ticket message",
            source="module.py:1",
            run_label="test",
            entry_id="ACT-DUP-001",
            created_at=now - timedelta(hours=2),
            priority=TicketPriority.P2,
            error_type="RuntimeError",
            stack_trace="trace-old",
            duplicate_guard="dup-old",
        ),
        ActifixEntry(
            message="Duplicate ticket message",
            source="module.py:1",
            run_label="test",
            entry_id="ACT-DUP-002",
            created_at=now - timedelta(minutes=5),
            priority=TicketPriority.P2,
            error_type="RuntimeError",
            stack_trace="trace-new",
            duplicate_guard="dup-new",
        ),
    ]

    for entry in entries:
        created = repo.create_ticket(entry)
        assert created is True

    results = cleanup_duplicate_tickets(repo, min_age_hours=0.0, dry_run=False)

    assert results["duplicate_groups"] == 1
    assert results["duplicates_closed"] == 1

    older_ticket = repo.get_ticket("ACT-DUP-001")
    newer_ticket = repo.get_ticket("ACT-DUP-002")

    assert older_ticket["status"] == "Completed"
    assert newer_ticket["status"] == "Open"
