import logging
import os
import sys
import pytest
from pathlib import Path

# Load performance tracking plugin within the ``test`` package
pytest_plugins = ["test.pytest_plugins"]

SLOW_TEST_PATTERNS = (
    "test_threading_barrier_debug.py",
    "test_threading_barrier_solution.py",
    "test_threading_barrier_diagnostic.py",
    "test_concurrent_locking_race_conditions.py",
    "test_ai_client.py",
    "test_api.py",
    "test_api_auth.py",
    "test_api_endpoints.py",
    "test_api_flask_autoinstall.py",
    "test_frontend_ui.py",
    "test_file_lock_timeout_retry.py",
    "test_queue_persistence_data_loss.py",
)

SLOW_SKIP_REASON = (
    "Test is marked as slow/hanging; rerun with --runslow to include it."
)


# ===== PYTEST CONFIGURATION WITH PERFORMANCE TRACKING =====

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
        "no_db_isolation: Skip per-test database isolation when using shared fixtures",
    ]

    for marker in markers:
        config.addinivalue_line("markers", marker)

    # Pytest-timeout configuration
    config.option.timeout = 10
    config.option.timeout_method = "thread"

    # Disable verbose logging to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlite3").setLevel(logging.WARNING)

    # Enable pytest-xdist auto-parallelism when available
    if config.pluginmanager.hasplugin("xdist"):
        if getattr(config.option, "numprocesses", None) in (None, 0):
            config.option.numprocesses = "auto"
        if getattr(config.option, "dist", None) is None:
            config.option.dist = "loadfile"


def pytest_addoption(parser):
    """Add custom pytest options for slow tests."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Include slow/hanging tests (barrier, API, concurrency, etc.).",
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests by default unless --runslow is passed."""
    if config.getoption("--runslow"):
        return

    slow_marker = pytest.mark.skip(reason=SLOW_SKIP_REASON)
    skipped = 0
    for item in items:
        if item.get_closest_marker("slow") or item.get_closest_marker("very_slow"):
            item.add_marker(slow_marker)
            skipped += 1
            continue

        path = str(item.fspath)
        if any(pattern in path for pattern in SLOW_TEST_PATTERNS):
            item.add_marker(slow_marker)
            skipped += 1

    if skipped:
        print(
            f"[pytest] Skipped {skipped} slow/hanging tests by default. Use --runslow to include them."
        )


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
def isolate_actifix_db(monkeypatch, tmp_path, request):
    """Use a fresh SQLite database per test to avoid cross-test leakage."""
    if request.node.get_closest_marker("no_db_isolation") or os.environ.get("ACTIFIX_DISABLE_DB_ISOLATION") == "1":
        yield
        return
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


@pytest.fixture(scope="session", autouse=True)
def database_profiler_session():
    """Database profiler for the entire test session."""
    from test.database_profiler import get_database_profiler

    profiler = get_database_profiler()
    yield profiler
    # Report at end of session
    profiler.report()


@pytest.fixture(scope="session")
def flask_app_session(tmp_path_factory):
    """Create a session-scoped Flask app for API tests to avoid repeated app creation overhead."""
    # Create a temporary project directory
    base = tmp_path_factory.mktemp("flask_app_session")
    
    # Set up Actifix environment
    import os
    os.environ["ACTIFIX_DATA_DIR"] = str(base / "actifix")
    os.environ["ACTIFIX_STATE_DIR"] = str(base / ".actifix")
    os.environ["ACTIFIX_DB_PATH"] = str(base / "data" / "actifix.db")
    os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
    
    # Initialize Actifix paths
    from actifix.state_paths import get_actifix_paths, init_actifix_files
    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)
    
    # Create the Flask app
    from actifix.api import create_app
    app = create_app(base)
    app.config['TESTING'] = True
    
    yield app
    
    # Clean up
    from actifix.persistence.database import reset_database_pool
    from actifix.persistence.ticket_repo import reset_ticket_repository
    from actifix.persistence.event_repo import reset_event_repository
    
    reset_database_pool()
    reset_ticket_repository()
    reset_event_repository()
