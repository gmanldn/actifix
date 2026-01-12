#!/usr/bin/env python3
"""Minimal event repository stub for compatibility with persistence APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class EventFilter:
    """Lightweight filter placeholder for event queries."""
    event_type: Optional[str] = None
    limit: int = 50


class EventRepository:
    """Stub event repository implementation (no-op)."""

    def __init__(self) -> None:
        self._events: list[Dict[str, Any]] = []

    def record_event(self, event: Dict[str, Any]) -> None:
        """Record a synthetic event (stored only in memory)."""
        self._events.append(event)

    def list_events(self, filter: EventFilter | None = None) -> list[Dict[str, Any]]:
        """Return in-memory events optionally filtered by type."""
        events = self._events
        if filter is None or not filter.event_type:
            return events[-filter.limit:] if filter else events
        return [e for e in events if e.get("event_type") == filter.event_type][-filter.limit:]


_global_event_repo: Optional[EventRepository] = None


def get_event_repository() -> EventRepository:
    """Return a singleton EventRepository instance."""
    global _global_event_repo
    if _global_event_repo is None:
        _global_event_repo = EventRepository()
    return _global_event_repo


def reset_event_repository() -> None:
    """Reset the cached EventRepository (for testing)."""
    global _global_event_repo
    _global_event_repo = None
