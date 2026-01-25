#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests that exercise the DoAF ticket processing flows.
"""

import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.do_af import (
    BackgroundAgentConfig,
    fix_highest_priority_ticket,
    process_next_ticket,
    process_tickets,
    run_background_agent,
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

    result = fix_highest_priority_ticket(
        paths=doaf_paths,
        completion_notes="Fixed critical issue in dashboard workflow",
        test_steps="Ran automated dashboard tests",
        test_results="All dashboard tests passed",
        summary="Automated dashboard fix"
    )
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

    def handler(ticket):
        return True

    processed = process_tickets(max_tickets=1, paths=doaf_paths, ai_handler=handler)
    assert len(processed) == 1


def test_background_agent_fallback_completion(doaf_paths, monkeypatch):
    repo = get_ticket_repository()
    entry = _build_entry("ACT-20260115-FALLBACK", TicketPriority.P2)
    repo.create_ticket(entry)

    monkeypatch.setenv("ACTIFIX_NONINTERACTIVE", "1")
    config = BackgroundAgentConfig(
        agent_id="test-agent",
        run_label="test-fallback",
        max_tickets=1,
        use_ai=False,
        fallback_complete=True,
    )
    processed = run_background_agent(config, paths=doaf_paths)
    assert processed == 1
    assert repo.get_ticket(entry.entry_id)["status"] == "Completed"


def test_background_agent_idle_no_tickets(doaf_paths, monkeypatch):
    config = BackgroundAgentConfig(
        agent_id="test-agent",
        run_label="test-idle",
        max_tickets=1,
        use_ai=False,
        fallback_complete=False,
    )
    event = threading.Event()

    def stop_after_wait(timeout):
        event.set()
        return True

    monkeypatch.setattr(event, "wait", stop_after_wait)
    processed = run_background_agent(config, paths=doaf_paths, stop_event=event)
    assert processed == 0


def test_background_agent_records_agent_voice(doaf_paths, monkeypatch):
    repo = get_ticket_repository()
    entry = _build_entry("ACT-20260115-VOICE", TicketPriority.P2)
    repo.create_ticket(entry)

    calls = []

    def fake_record_agent_voice(*args, **kwargs):
        calls.append((args, kwargs))
        return 1

    monkeypatch.setenv("ACTIFIX_NONINTERACTIVE", "1")
    monkeypatch.setattr("actifix.agent_voice.record_agent_voice", fake_record_agent_voice)

    config = BackgroundAgentConfig(
        agent_id="test-agent",
        run_label="test-agent-voice",
        max_tickets=1,
        use_ai=False,
        fallback_complete=True,
    )
    processed = run_background_agent(config, paths=doaf_paths)
    assert processed == 1
    assert calls
