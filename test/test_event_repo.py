#!/usr/bin/env python3
"""
Tests for the persistence event repository which now backs AFLog via SQLite.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import pytest

from actifix.persistence.database import reset_database_pool
from actifix.persistence.event_repo import (
    EventFilter,
    EventRepository,
    get_event_repository,
    reset_event_repository,
)


def _create_ticket_for_event(repo: EventRepository, ticket_id: str) -> None:
    """Insert a bare-bones ticket for FK-safe event logging."""
    with repo.pool.transaction() as conn:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO tickets (id, priority, error_type, message, source, created_at, duplicate_guard)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                "P2",
                "event_repo_seed",
                "Seed for event repository tests",
                "tests.event_repo",
                now,
                f"seed-{ticket_id}",
            ),
        )


@pytest.fixture(autouse=True)
def isolate_event_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ensure each test runs against its own temporary database."""
    db_path = tmp_path / "event_repo.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    reset_database_pool()
    reset_event_repository()
    yield
    reset_event_repository()
    reset_database_pool()


def test_event_repository_records_and_filters() -> None:
    repo = EventRepository()
    assert repo.get_event_count() == 0

    # Create tickets for FK constraint
    _create_ticket_for_event(repo, "ACT-001")
    _create_ticket_for_event(repo, "ACT-002")

    event_id_alpha = repo.log_event(
        event_type="alpha",
        message="First entry",
        ticket_id="ACT-001",
        correlation_id="corr-1",
        extra_json='{"payload": 1}',
        level="DEBUG",
        source="tests.event_repo",
    )
    assert isinstance(event_id_alpha, int)

    event_id_beta = repo.log_event(
        event_type="beta",
        message="Second entry",
        ticket_id="ACT-002",
        correlation_id="corr-2",
        level="INFO",
        source="tests.event_repo",
    )
    assert event_id_beta != event_id_alpha
    assert repo.get_event_count() == 2

    all_events = repo.get_events()
    assert len(all_events) == 2
    assert all_events[0]["event_type"] == "beta"
    assert all_events[1]["ticket_id"] == "ACT-001"

    alpha_events = repo.get_events(EventFilter(event_type="alpha", limit=5))
    assert len(alpha_events) == 1
    assert alpha_events[0]["correlation_id"] == "corr-1"

    paged = repo.get_events(EventFilter(limit=1, offset=1))
    assert len(paged) == 1
    assert paged[0]["event_type"] == "alpha"

    assert repo.get_events_for_ticket("ACT-002")[0]["event_type"] == "beta"
    assert repo.get_events_by_correlation("corr-1")[0]["ticket_id"] == "ACT-001"
    assert repo.get_events_by_type("beta", limit=1)[0]["source"] == "tests.event_repo"
    recent = repo.get_recent_events(limit=1)
    assert recent[0]["event_type"] == "beta"

    old_ts = datetime(2000, 1, 1, tzinfo=timezone.utc)
    repo.log_event(
        event_type="ancient",
        message="Old entry",
        timestamp=old_ts,
        level="WARNING",
    )
    assert repo.get_event_count() == 3
    deleted = repo.prune_old_events(days_to_keep=365)
    assert deleted >= 1
    assert repo.get_event_count() == 2

    stats = repo.get_stats()
    assert stats["total"] == repo.get_event_count()
    assert stats["by_type"]["alpha"] == 1
    assert stats["by_level"]["INFO"] == 1


def test_event_repository_singleton_reset() -> None:
    repo_one = get_event_repository()
    repo_one.log_event(event_type="singleton", message="single")

    repo_two = get_event_repository()
    assert repo_two is repo_one
    assert repo_two.get_event_count() >= 1

    reset_event_repository()
    repo_three = get_event_repository()
    assert repo_three is not repo_one
    assert repo_three.get_event_count() >= 1
