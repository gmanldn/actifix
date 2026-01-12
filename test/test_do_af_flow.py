#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests that exercise the DoAF ticket processing flows.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.do_af import (
    fix_highest_priority_ticket,
    process_next_ticket,
    process_tickets,
)
from actifix.persistence.database import reset_database_pool
from actifix.persistence.ticket_repo import (
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


def _build_entry(ticket_id: str, priority: TicketPriority) -> ActifixEntry:
    return ActifixEntry(
        message="doaf flow test",
        source="doaf.test:1",
        run_label="doaf",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="FlowTest",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


@pytest.fixture
def doaf_paths(tmp_path, monkeypatch):
    base = tmp_path
    data_dir = base / "actifix"
    state_dir = base / ".actifix"
    db_path = base / "data" / "actifix.db"

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)
    yield paths

    reset_database_pool()
    reset_ticket_repository()


def test_fix_highest_priority_ticket_triggers_logging(doaf_paths):
    repo = get_ticket_repository()
    entry = _build_entry("ACT-20260115-DOAF", TicketPriority.P0)
    repo.create_ticket(entry)

    result = fix_highest_priority_ticket(paths=doaf_paths, summary="Automated dashboard fix")
    assert result["processed"] is True
    assert result["ticket_id"] == entry.entry_id
    assert repo.get_ticket(entry.entry_id)["status"] == "Completed"


def test_process_next_ticket_with_custom_handler(doaf_paths):
    repo = get_ticket_repository()
    entry = _build_entry("ACT-20260115-HANDLER", TicketPriority.P1)
    repo.create_ticket(entry)

    handled = []

    def handler(ticket):
        handled.append(ticket.ticket_id)
        return True

    ticket = process_next_ticket(ai_handler=handler, paths=doaf_paths, use_ai=False)
    assert ticket is not None
    assert handled == [entry.entry_id]
    assert repo.get_ticket(entry.entry_id)["status"] == "Completed"


def test_process_tickets_respects_limit(doaf_paths):
    repo = get_ticket_repository()
    repo.create_ticket(_build_entry("ACT-20260115-ONE", TicketPriority.P2))
    repo.create_ticket(_build_entry("ACT-20260115-TWO", TicketPriority.P3))

    processed = process_tickets(max_tickets=1, paths=doaf_paths)
    assert len(processed) == 1
