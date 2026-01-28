import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from actifix.main import cmd_queue


def test_queue_replay_outputs_progress(monkeypatch, tmp_path, capsys):
    base_dir = tmp_path / "actifix"
    state_dir = tmp_path / ".actifix"
    base_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(base_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))

    queue_file = state_dir / "actifix_fallback_queue.json"
    created_at = datetime.now(timezone.utc).isoformat()
    entry = {
        "message": "Replay me",
        "source": "test/test_queue_replay_cli.py:1",
        "run_label": "test",
        "entry_id": "ACT-TEST-QUEUE-001",
        "created_at": created_at,
        "priority": "P2",
        "error_type": "TestError",
        "stack_trace": "",
        "file_context": {},
        "system_state": {},
        "ai_remediation_notes": "",
        "duplicate_guard": "dup-queue-001",
        "format_version": "1.0",
        "correlation_id": None,
    }
    queue_file.write_text(json.dumps([entry]), encoding="utf-8")

    args = argparse.Namespace(
        project_root=None,
        queue_action="replay",
    )
    result = cmd_queue(args)
    output = capsys.readouterr().out

    assert result == 0
    assert "Replaying fallback queue entries" in output
    assert "Replayed: 1" in output
