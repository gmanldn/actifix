import os
import pytest


@pytest.fixture(autouse=True)
def enforce_raise_af_origin(monkeypatch):
    """
    Ensure tests run with Raise_AF gate satisfied.

    The enforcement policy requires ACTIFIX_CHANGE_ORIGIN=raise_af for any
    Actifix operations. Tests set it by default but can override per-case.
    """
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    yield


@pytest.fixture(autouse=True)
def isolate_actifix_db(monkeypatch, tmp_path):
    """Use a fresh SQLite database per test to avoid cross-test leakage."""
    db_path = tmp_path / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    from actifix.persistence.database import reset_database_pool
    from actifix.persistence.ticket_repo import reset_ticket_repository
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()
