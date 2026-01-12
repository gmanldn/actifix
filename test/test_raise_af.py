#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import actifix.raise_af as ra


def test_fallback_queue_uses_state_dir_and_replays(monkeypatch, tmp_path):
    base_dir = tmp_path / "actifix_data"
    state_dir = tmp_path / ".actifix_state"

    monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "1")
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(data_dir / "actifix.db"))
    from actifix.persistence.database import reset_database_pool
    reset_database_pool()

    from actifix.persistence import ticket_repo
    original_repo = ticket_repo.get_ticket_repository

    def fail_repo():
        raise RuntimeError("db down")

    monkeypatch.setattr(ticket_repo, "get_ticket_repository", fail_repo)

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

    # Restore normal repo and replay queued entries
    monkeypatch.setattr(ticket_repo, "get_ticket_repository", original_repo)
    reset_database_pool()
    replayed = ra.replay_fallback_queue(base_dir=base_dir)

    from actifix.persistence.ticket_repo import get_ticket_repository
    repo = get_ticket_repository()
    stored = repo.get_ticket(entry.entry_id)
    assert stored is not None
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
