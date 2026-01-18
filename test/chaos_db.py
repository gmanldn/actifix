"""Helpers for simulating database failures in tests."""

from __future__ import annotations

import contextlib
import sqlite3
from typing import Iterator, Optional


@contextlib.contextmanager
def chaos_sqlite_connect(monkeypatch, exc: Optional[Exception] = None) -> Iterator[None]:
    """Force sqlite3.connect to raise the provided exception."""
    error = exc or sqlite3.OperationalError("chaos: sqlite3.connect failed")

    def _boom(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(sqlite3, "connect", _boom)
    yield
