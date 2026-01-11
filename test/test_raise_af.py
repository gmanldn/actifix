#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import actifix.raise_af as ra


def test_fallback_queue_uses_state_dir_and_replays(monkeypatch, tmp_path):
    base_dir = tmp_path / "actifix_data"
    state_dir = tmp_path / ".actifix_state"

    monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "1")
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))

    original_append = ra._append_ticket_impl

    def fail_append(*args, **kwargs):
        raise PermissionError("blocked")

    monkeypatch.setattr(ra, "_append_ticket_impl", fail_append)

    entry = ra.record_error(
        message="fallback queue test",
        source="tests/example.py:10",
        run_label="unittest",
        base_dir=base_dir,
        error_type="TestError",
        capture_context=False,
        skip_ai_notes=True,
    )

    queue_file = state_dir / "actifix_fallback_queue.json"
    assert entry is not None
    assert queue_file.exists()

    queue = json.loads(queue_file.read_text())
    assert queue[0]["message"] == "fallback queue test"

    # Restore normal append and replay queued entries
    monkeypatch.setattr(ra, "_append_ticket_impl", original_append)
    replayed = ra.replay_fallback_queue(base_dir=base_dir)

    content = (base_dir / "ACTIFIX-LIST.md").read_text()
    assert "fallback queue test" in content
    assert replayed == 1
    assert not queue_file.exists()


def test_redact_secrets_and_duplicate_guard_stability():
    text = "api_key=sk-1234567890abcdef1234 and password=supersecret"
    redacted = ra.redact_secrets_from_text(text)
    assert "sk-1234567890abcdef1234" not in redacted
    assert "supersecret" not in redacted

    guard_one = ra.generate_duplicate_guard("core/module.py", "Error 1234 happened", "ValueError")
    guard_two = ra.generate_duplicate_guard("core/module.py", "Error 5678 happened", "ValueError")
    assert guard_one == guard_two  # numeric parts normalized


def test_assess_duplicate_guard_rules(tmp_path):
    base_dir = tmp_path / "actifix"
    base_dir.mkdir()
    list_file = base_dir / "ACTIFIX-LIST.md"
    guard = "ACTIFIX-dup-guard"

    now = datetime.now(timezone.utc)

    open_created = now.isoformat()
    stale_created = (now - timedelta(days=2)).isoformat()
    recent_created = (now - timedelta(hours=1)).isoformat()

    # Open ticket should always count as duplicate
    list_file.write_text(
        "\n".join(
            [
                "# Actifix Ticket List",
                "## Active Items",
                f"### ACT-OPEN - [P2] Error @ {open_created}: Open item",
                "- **Priority**: P2",
                "- **Error Type**: Error",
                "- **Source**: `tests.py:1`",
                "- **Run**: test-run",
                f"- **Created**: {open_created}",
                f"- **Duplicate Guard**: `{guard}`",
                "- **Status**: Open",
                "",
                "## Completed Items",
                "",
            ]
        )
    )

    assessment = ra.assess_duplicate_guard(guard, base_dir)
    assert assessment.is_duplicate is True
    assert assessment.status.lower().startswith("open")

    # Completed but stale should be treated as new after window
    list_file.write_text(
        "\n".join(
            [
                "# Actifix Ticket List",
                "## Active Items",
                "_None_",
                "## Completed Items",
                f"### ACT-COMP - [P2] Error @ {stale_created}: Old issue",
                "- **Priority**: P2",
                "- **Error Type**: Error",
                "- **Source**: `tests.py:1`",
                "- **Run**: test-run",
                f"- **Created**: {stale_created}",
                f"- **Duplicate Guard**: `{guard}`",
                "- **Status**: Completed",
            ]
        )
    )

    assessment = ra.assess_duplicate_guard(guard, base_dir, reopen_window=timedelta(hours=1))
    assert assessment.is_duplicate is False

    # Recent completion within window should still be duplicate
    list_file.write_text(
        "\n".join(
            [
                "# Actifix Ticket List",
                "## Active Items",
                "_None_",
                "## Completed Items",
                f"### ACT-COMP - [P2] Error @ {recent_created}: Recent issue",
                "- **Priority**: P2",
                "- **Error Type**: Error",
                "- **Source**: `tests.py:1`",
                "- **Run**: test-run",
                f"- **Created**: {recent_created}",
                f"- **Duplicate Guard**: `{guard}`",
                "- **Status**: Completed",
            ]
        )
    )

    assessment = ra.assess_duplicate_guard(guard, base_dir, reopen_window=timedelta(hours=2))
    assert assessment.is_duplicate is True
