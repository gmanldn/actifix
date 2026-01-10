#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
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
