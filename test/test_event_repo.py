#!/usr/bin/env python3
"""
Tests for the persistence event repository helpers.
"""

import pytest

from actifix.persistence.event_repo import (
    EventFilter,
    EventRepository,
    get_event_repository,
    reset_event_repository,
)


def test_event_repository_records_and_filters():
    repo = EventRepository()
    repo.record_event({"event_type": "alpha", "payload": 1})
    repo.record_event({"event_type": "beta", "payload": 2})
    assert len(repo.list_events()) == 2

    window = EventFilter(event_type="alpha", limit=1)
    filtered = repo.list_events(window)
    assert filtered == [{"event_type": "alpha", "payload": 1}]


def test_event_repository_singleton_reset():
    reset_event_repository()
    repo_one = get_event_repository()
    repo_one.record_event({"event_type": "singleton", "payload": "x"})

    repo_two = get_event_repository()
    assert repo_two.list_events() == [{"event_type": "singleton", "payload": "x"}]

    reset_event_repository()
    repo_three = get_event_repository()
    assert repo_three.list_events() == []
