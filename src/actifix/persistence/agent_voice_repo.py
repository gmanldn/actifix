#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AgentVoice repository.

Stores agent activity/notes in SQLite for review. Enforces a hard cap on total
rows by pruning the oldest entries after each insert.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .database import get_database_pool

DEFAULT_MAX_AGENT_VOICE_ROWS = 1_000_000


@dataclass(frozen=True)
class AgentVoiceEntry:
    id: int
    created_at: str
    agent_id: str
    run_label: Optional[str]
    level: str
    thought: str
    extra_json: Optional[str]
    correlation_id: Optional[str]


class AgentVoiceRepository:
    """Repository for writing/reading agent_voice rows."""

    def __init__(self, max_rows: int = DEFAULT_MAX_AGENT_VOICE_ROWS):
        if max_rows <= 0:
            raise ValueError("max_rows must be positive")
        self.max_rows = int(max_rows)

    def append(
        self,
        *,
        agent_id: str,
        thought: str,
        run_label: Optional[str] = None,
        level: str = "INFO",
        extra: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> int:
        """Insert a new agent voice row and prune to max_rows."""
        if not agent_id:
            raise ValueError("agent_id is required")
        if not thought:
            raise ValueError("thought is required")

        extra_json = None
        if extra is not None:
            extra_json = json.dumps(extra, default=str)

        pool = get_database_pool()
        with pool.transaction(immediate=True) as conn:
            cursor = conn.execute(
                """
                INSERT INTO agent_voice (agent_id, run_label, level, thought, extra_json, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (agent_id, run_label, level, thought, extra_json, correlation_id),
            )
            row_id = int(cursor.lastrowid)
            self._prune_locked(conn)
            return row_id

    def count(self) -> int:
        pool = get_database_pool()
        with pool.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM agent_voice").fetchone()
            return int(row["c"] if row else 0)

    def list_recent(self, limit: int = 50, agent_id: Optional[str] = None) -> list[AgentVoiceEntry]:
        limit = max(1, min(int(limit), 1000))
        pool = get_database_pool()
        with pool.connection() as conn:
            if agent_id:
                rows = conn.execute(
                    """
                    SELECT id, created_at, agent_id, run_label, level, thought, extra_json, correlation_id
                    FROM agent_voice
                    WHERE agent_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (agent_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, created_at, agent_id, run_label, level, thought, extra_json, correlation_id
                    FROM agent_voice
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [
            AgentVoiceEntry(
                id=int(r["id"]),
                created_at=str(r["created_at"]),
                agent_id=str(r["agent_id"]),
                run_label=r["run_label"],
                level=str(r["level"]),
                thought=str(r["thought"]),
                extra_json=r["extra_json"],
                correlation_id=r["correlation_id"],
            )
            for r in rows
        ]

    def _prune_locked(self, conn) -> None:
        """Prune to max_rows using the provided (write-locked) connection."""
        # Find the minimum id among the newest max_rows entries; delete anything older.
        # This avoids a large OFFSET scan while still being deterministic by id.
        cutoff = conn.execute(
            """
            SELECT MIN(id) AS cutoff_id
            FROM (SELECT id FROM agent_voice ORDER BY id DESC LIMIT ?)
            """,
            (self.max_rows,),
        ).fetchone()
        if cutoff is None or cutoff["cutoff_id"] is None:
            return
        cutoff_id = int(cutoff["cutoff_id"])
        conn.execute("DELETE FROM agent_voice WHERE id < ?", (cutoff_id,))


_global_agent_voice_repo: Optional[AgentVoiceRepository] = None


def get_agent_voice_repository(max_rows: int = DEFAULT_MAX_AGENT_VOICE_ROWS) -> AgentVoiceRepository:
    """Return a process-global AgentVoiceRepository."""
    global _global_agent_voice_repo
    if _global_agent_voice_repo is None or _global_agent_voice_repo.max_rows != int(max_rows):
        _global_agent_voice_repo = AgentVoiceRepository(max_rows=max_rows)
    return _global_agent_voice_repo


def reset_agent_voice_repository() -> None:
    global _global_agent_voice_repo
    _global_agent_voice_repo = None
