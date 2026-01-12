#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Actifix migration helpers that move Markdown tickets into the database.
"""

from pathlib import Path
import pytest

from actifix.migrate_to_db import parse_markdown_ticket, migrate_tickets
from actifix.raise_af import TicketPriority
from actifix.persistence.database import reset_database_pool
from actifix.persistence.ticket_repo import reset_ticket_repository
from actifix.state_paths import get_actifix_paths, init_actifix_files


@pytest.fixture
def db_environment(tmp_path, monkeypatch):
    """Prepare Actifix directories and database path for migration tests."""
    data_dir = tmp_path / "actifix"
    state_dir = tmp_path / ".actifix"
    db_path = tmp_path / "data" / "actifix.db"

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    yield paths

    reset_database_pool()
    reset_ticket_repository()


def _sample_markdown_block(ticket_id: str, priority: str = "P1") -> str:
    """Return a markdown block resembling a migrated ticket."""
    return f"""
### {ticket_id} - [{priority}] DatabaseError: Connection refused
- **Priority**: {priority}
- **Error Type**: DatabaseError
- **Source**: `db.py:42`
- **Run**: migration-test
- **Created**: 2026-01-13T12:00:00+00:00
- **Duplicate Guard**: `{ticket_id}-guard`

```
Traceback (most recent call last):
    ...
```
"""


def test_parse_markdown_ticket_full_fields():
    """Ensure the parser extracts every field from the markdown format."""
    block = _sample_markdown_block("ACT-20260113-ABC123")
    entry = parse_markdown_ticket(block)
    assert entry is not None
    assert entry.entry_id == "ACT-20260113-ABC123"
    assert entry.priority == TicketPriority.P1
    assert entry.source == "db.py:42"
    assert entry.run_label == "migration-test"
    assert "Traceback" in entry.stack_trace


def test_migrate_tickets_success(db_environment):
    """The migration script should import unique tickets and skip duplicates."""
    paths = db_environment
    list_file = paths.base_dir / "ACTIFIX-LIST.md"
    list_file.write_text(
        _sample_markdown_block("ACT-20260113-ABC123")
        + "\n\n"
        + _sample_markdown_block("ACT-20260113-ABC123")
        + "\n\n"
        + _sample_markdown_block("ACT-20260114-DEF456", priority="P2")
    )

    result = migrate_tickets()

    assert result["success"] is True
    assert result["migrated"] == 2
    assert result["skipped"] == 1


def test_migrate_tickets_missing_file(tmp_path, monkeypatch):
    """Migration should fail cleanly when the markdown archive is absent."""
    data_dir = tmp_path / "actifix"
    state_dir = tmp_path / ".actifix"
    db_path = tmp_path / "data" / "actifix.db"

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))

    result = migrate_tickets()

    assert result["success"] is False
    assert result["error"] == "ACTIFIX-LIST.md not found"
