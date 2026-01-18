#!/usr/bin/env python3
"""Chaos tests for database failure simulation."""

from __future__ import annotations

import pytest

from test.chaos_db import chaos_sqlite_connect


def test_database_connection_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "actifix.db"))

    from actifix.persistence.database import get_database_pool, reset_database_pool, DatabaseConnectionError

    reset_database_pool()
    with chaos_sqlite_connect(monkeypatch):
        with pytest.raises(DatabaseConnectionError):
            get_database_pool()._get_connection()

    reset_database_pool()
