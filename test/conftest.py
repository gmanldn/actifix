import os
import sys
import pytest
from pathlib import Path


# ===== PYTEST CONFIGURATION WITH PROGRESS =====

def pytest_configure(config):
    """Configure pytest with performance optimizations and test categorization."""
    # Add custom markers for test categorization
    markers = [
        "unit: Fast unit tests with minimal dependencies (< 100ms)",
        "integration: Integration tests that involve multiple components (100ms - 1s)",
        "slow: Slow tests that may take > 1s (database-heavy, network, large fixtures)",
        "very_slow: Tests known to take > 5 seconds",
        "db: Tests that perform database operations (likely slow)",
        "api: API endpoint tests",
        "performance: Performance or benchmark tests",
        "security: Security-related tests",
        "architecture: Architecture validation tests",
        "concurrent: Concurrent/threading tests",
        "io: File I/O tests",
        "network: Network/external service tests",
    ]

    for marker in markers:
        config.addinivalue_line("markers", marker)

    # Pytest-timeout configuration
    config.option.timeout = 30
    config.option.timeout_method = "thread"

    # Disable verbose logging to reduce noise
    import logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlite3").setLevel(logging.WARNING)


@pytest.fixture(scope="session", autouse=True)
def session_setup():
    """One-time setup at session start."""
    # Ensure Raise_AF origin is set
    os.environ.setdefault("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    yield


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
def disable_actifix_capture(monkeypatch):
    """
    Disable Actifix ticket capture during tests by default.

    This prevents test exceptions from creating spurious tickets in the database.
    Individual tests can override by explicitly setting ACTIFIX_CAPTURE_ENABLED=1.

    ROOT CAUSE FIX: Test exceptions were creating tickets because capture was
    enabled during test runs. This fixture ensures tests don't pollute the ticket
    database unless explicitly testing ticket creation functionality.
    """
    # Only disable if not explicitly enabled by the test
    if "ACTIFIX_CAPTURE_ENABLED" not in os.environ:
        monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "0")
    yield


@pytest.fixture(autouse=True, scope="function")
def isolate_actifix_db(monkeypatch, tmp_path):
    """Use a fresh SQLite database per test to avoid cross-test leakage."""
    # Set database path BEFORE any imports that might use it
    db_path = tmp_path / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    
    # Reset pools and repositories
    from actifix.persistence.database import reset_database_pool
    from actifix.persistence.ticket_repo import reset_ticket_repository
    from actifix.persistence.event_repo import reset_event_repository
    
    reset_database_pool()
    reset_ticket_repository()
    reset_event_repository()
    
    yield
    
    # Clean up after test
    reset_database_pool()
    reset_ticket_repository()
    reset_event_repository()
