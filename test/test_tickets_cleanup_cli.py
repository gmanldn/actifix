import argparse
from datetime import datetime, timezone, timedelta

from actifix.main import cmd_tickets
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.persistence.ticket_repo import get_ticket_repository


def test_tickets_cleanup_cli_executes(monkeypatch, capsys):
    repo = get_ticket_repository()
    now = datetime.now(timezone.utc)

    repo.create_ticket(
        ActifixEntry(
            message="Duplicate CLI ticket",
            source="module.py:2",
            run_label="test",
            entry_id="ACT-DUP-CLI-001",
            created_at=now - timedelta(hours=5),
            priority=TicketPriority.P2,
            error_type="RuntimeError",
            stack_trace="trace-old",
            duplicate_guard="dup-cli-old",
        )
    )
    repo.create_ticket(
        ActifixEntry(
            message="Duplicate CLI ticket",
            source="module.py:2",
            run_label="test",
            entry_id="ACT-DUP-CLI-002",
            created_at=now - timedelta(minutes=1),
            priority=TicketPriority.P2,
            error_type="RuntimeError",
            stack_trace="trace-new",
            duplicate_guard="dup-cli-new",
        )
    )

    args = argparse.Namespace(
        project_root=None,
        tickets_action="cleanup",
        min_age_hours=0.0,
        execute=True,
    )
    result = cmd_tickets(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Duplicate Ticket Cleanup" in output
    assert "Duplicates closed" in output
