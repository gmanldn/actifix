#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent voice logging.

Convenience wrapper for recording agent activity into the SQLite AgentVoice
table with Actifix-standard error capture.
"""

from __future__ import annotations

from typing import Any, Optional

from .raise_af import record_error, TicketPriority
from .persistence.agent_voice_repo import get_agent_voice_repository


def record_agent_voice(
    thought: str,
    *,
    agent_id: str = "actifix-agent",
    run_label: Optional[str] = None,
    level: str = "INFO",
    extra: Optional[dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    max_rows: int = 1_000_000,
) -> int:
    """Record a single agent voice row and return its row id."""
    try:
        repo = get_agent_voice_repository(max_rows=max_rows)
        return repo.append(
            agent_id=agent_id,
            run_label=run_label,
            level=level,
            thought=thought,
            extra=extra,
            correlation_id=correlation_id,
        )
    except Exception as exc:
        record_error(
            message=f"Failed to record agent voice: {exc}",
            source="actifix/agent_voice.py:record_agent_voice",
            run_label=run_label or "agent-voice",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
            capture_context=True,
        )
        raise

