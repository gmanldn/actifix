#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
View recent agent thoughts (AgentVoice rows).

Shows the last N days of agent voice rows from the canonical SQLite database.

Usage:
  python3 scripts/view_agentThoughts.py
  python3 scripts/view_agentThoughts.py --days 1 --limit 200
  python3 scripts/view_agentThoughts.py --agent-id scripts/start.py
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from actifix.persistence.agent_voice_repo import AgentVoiceRepository


def _parse_created_at(raw: str) -> Optional[datetime]:
    raw = (raw or "").strip()
    if not raw:
        return None
    # SQLite CURRENT_TIMESTAMP default is "YYYY-MM-DD HH:MM:SS" (no tz).
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="View recent AgentVoice thoughts")
    parser.add_argument("--days", type=float, default=1.0, help="How many days back to include (default: 1)")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to show (default: 200)")
    parser.add_argument("--agent-id", type=str, default="", help="Filter by agent_id (optional)")
    args = parser.parse_args(argv)

    db_path = Path(os.environ.get("ACTIFIX_DB_PATH") or (ROOT / "data" / "actifix.db")).expanduser()
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    days = max(0.0, float(args.days))
    limit = max(1, min(int(args.limit), 10000))
    agent_id = args.agent_id.strip() or None

    cutoff = datetime.now() - timedelta(days=days)
    repo = AgentVoiceRepository()

    # Fetch more than the display limit so we can filter by time without underfilling.
    candidates = repo.list_recent(limit=min(10000, max(limit * 5, limit)), agent_id=agent_id)
    entries = []
    for e in candidates:
        created = _parse_created_at(e.created_at)
        if created is None:
            continue
        if created >= cutoff:
            entries.append((created, e))
        if len(entries) >= limit:
            break

    print("=" * 100)
    header_agent = f" agent_id={agent_id}" if agent_id else ""
    print(f"ACTIFIX AGENT THOUGHTS (last {days:g} day(s)){header_agent}")
    print("=" * 100)
    print(f"Database: {db_path}")
    print(f"Rows shown: {len(entries)} (limit {limit})")
    print()

    if not entries:
        print("No agent thoughts found in the requested window.")
        return 0

    for created, e in entries:
        ts = created.isoformat(sep=" ", timespec="seconds")
        run_label = e.run_label or "-"
        print("-" * 100)
        print(f"{ts} | {e.level} | agent_id={e.agent_id} | run_label={run_label} | row_id={e.id}")
        print(e.thought)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

