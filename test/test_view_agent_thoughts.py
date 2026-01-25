"""Tests for the view_agentThoughts script and symlink."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from actifix.persistence.agent_voice_repo import AgentVoiceRepository
from actifix.persistence.database import get_database_pool, reset_database_pool


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    reset_database_pool()
    yield db_path
    reset_database_pool()


def test_view_agent_thoughts_root_is_symlink():
    root = Path(__file__).parent.parent
    link = root / "view_agentThoughts.py"
    assert link.exists()
    assert link.is_symlink()
    assert os.readlink(link) == "scripts/view_agentThoughts.py"


def test_view_agent_thoughts_outputs_recent_only(isolated_db):
    repo = AgentVoiceRepository(max_rows=100)
    repo.append(agent_id="agent-a", thought="recent-thought", run_label="unit")

    # Insert an older row (>1 day) directly so the filter can exclude it.
    old_ts = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    pool = get_database_pool()
    with pool.transaction(immediate=True) as conn:
        conn.execute(
            """
            INSERT INTO agent_voice (created_at, agent_id, run_label, level, thought)
            VALUES (?, ?, ?, ?, ?)
            """,
            (old_ts, "agent-a", "unit", "INFO", "old-thought"),
        )

    root = Path(__file__).parent.parent
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "view_agentThoughts.py"), "--days", "1", "--limit", "50"],
        cwd=str(root),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert "recent-thought" in proc.stdout
    assert "old-thought" not in proc.stdout

