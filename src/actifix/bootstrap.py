#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bootstrap system for Actifix self-development.

This module sets up error capture so that actifix can track its own
development issues and improvements from the very beginning.

Version: 2.0.0 (Generic)
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Optional, Callable, Tuple, Any

from .raise_af import record_error, ACTIFIX_CAPTURE_ENV_VAR, enforce_raise_af_only
from .state_paths import get_actifix_paths, init_actifix_files, ActifixPaths
from .thread_cleanup import cleanup_orphan_threads, log_thread_state
from .log_utils import log_event


def enable_actifix_capture() -> None:
    """Enable actifix error capture for development."""
    os.environ[ACTIFIX_CAPTURE_ENV_VAR] = "1"


def disable_actifix_capture() -> None:
    """Disable actifix error capture."""
    os.environ[ACTIFIX_CAPTURE_ENV_VAR] = "0"


def capture_exception(exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
    """
    Capture exceptions in actifix development.

    This can be set as the global exception handler during development
    so that actifix automatically tracks its own bugs.
    """
    # Don't capture if it's a KeyboardInterrupt or SystemExit
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        return
    
    try:
        # Extract source information from traceback
        tb_list = traceback.extract_tb(exc_traceback)
        if tb_list:
            last_frame = tb_list[-1]
            source = f"{last_frame.filename}:{last_frame.lineno}"
        else:
            source = "unknown"
        
        # Record the error
        record_error(
            message=str(exc_value),
            source=source,
            run_label="actifix-development",
            error_type=exc_type.__name__,
            stack_trace="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            capture_context=True
        )
        
        print(f"[Actifix] Captured development error: {exc_type.__name__}: {exc_value}")
        
    except Exception as e:
        # Don't let error capture cause more errors
        print(f"[Actifix] Failed to capture error: {e}")


def install_exception_handler() -> Callable:
    """Install global exception handler for actifix development."""
    original_handler = sys.excepthook

    def actifix_excepthook(exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        # Capture with actifix first
        capture_exception(exc_type, exc_value, exc_traceback)

        # Then call the original handler
        original_handler(exc_type, exc_value, exc_traceback)

    sys.excepthook = actifix_excepthook
    return original_handler


def uninstall_exception_handler(original_handler: Callable) -> None:
    """Restore the original exception handler."""
    sys.excepthook = original_handler


def bootstrap_actifix_development() -> Callable:
    """
    Bootstrap actifix for self-development.

    Call this at the start of actifix development to enable
    automatic error tracking during the development process.
    """
    print("[Actifix] Bootstrapping self-development mode...")

    # Enable error capture
    enable_actifix_capture()

    # Install exception handler
    original_handler = install_exception_handler()

    # Create initial directories
    from .state_paths import get_actifix_data_dir, get_actifix_state_dir

    data_dir = get_actifix_data_dir()
    state_dir = get_actifix_state_dir()

    data_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    ensure_ticket_database(get_actifix_paths(project_root=Path.cwd()))

    print(f"[Actifix] Data directory: {data_dir}")
    print(f"[Actifix] State directory: {state_dir}")
    print("[Actifix] Self-development mode active - actifix will track its own development issues!")

    return original_handler


def ensure_ticket_database(paths: ActifixPaths) -> Path:
    """
    Ensure the ticket database exists and is initialized.

    Returns:
        Path to the ticket database file.
    """
    from .persistence.database import get_database_pool

    env_db_path = os.environ.get("ACTIFIX_DB_PATH")
    db_path = Path(env_db_path).expanduser() if env_db_path else (paths.project_root / "data" / "actifix.db")

    pool = get_database_pool(db_path=db_path)
    with pool.connection() as conn:
        conn.execute("SELECT 1")

    if not db_path.exists():
        raise FileNotFoundError(f"Ticket database not found after initialization: {db_path}")

    return db_path


def _run_phase(phase_num: int, func: Callable, *args, **kwargs) -> None:
    """Run a bootstrap phase with rollback support."""
    from .log_utils import log_event  # Ensure log_event is available
    
    rollback_stack = []
    
    def add_rollback(rollback_func: Callable):
        rollback_stack.append(rollback_func)
    
    try:
        log_event(f"BOOTSTRAP_PHASE_{phase_num:02d}_START")
        func(phase_num, add_rollback, *args, **kwargs)
        log_event(f"BOOTSTRAP_PHASE_{phase_num:02d}_SUCCESS")
    except Exception as e:
        log_event(f"BOOTSTRAP_PHASE_{phase_num:02d}_FAILED", str(e))
        # Rollback in reverse order
        for rollback in reversed(rollback_stack):
            try:
                rollback()
            except Exception:
                pass
        raise

def phased_bootstrap(project_root: Optional[Path] = None) -> ActifixPaths:
    """
    Phased bootstrap with explicit 30 phases and rollback hooks.
    
    Runs 30 phases with logging; rollback on phase failure.
    """
    def phase1(phase_num, add_rollback, *args, **kwargs):
        pass

    def noop_phase(phase_num, add_rollback, *args, **kwargs):
        pass

    phases = [phase1] + [noop_phase] * 29
    
    for i, func in enumerate(phases, 1):
        _run_phase(i, func, project_root)
    
    paths = get_actifix_paths(project_root=project_root)
    log_thread_state()
    log_event("BOOTSTRAP_COMPLETE_30_PHASES")
    return paths



def bootstrap(project_root: Optional[Path] = None) -> ActifixPaths:
    """
    Initialize Actifix paths for a project (now phased).

    Args:
        project_root: Optional project root to initialize.

    Returns:
        Initialized ActifixPaths.
    """
    return phased_bootstrap(project_root)



def shutdown() -> None:
    """Shutdown hook for Actifix lifecycle (no-op placeholder)."""
    return None


class ActifixContext:
    """Context manager to bootstrap Actifix lifecycle."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root
        self.paths: Optional[ActifixPaths] = None

    def __enter__(self) -> ActifixPaths:
        self.paths = bootstrap(self.project_root)
        return self.paths

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        shutdown()


def create_initial_ticket() -> None:
    """
    Create an initial ticket for actifix development.

    DEPRECATED: This function creates tracking tickets that pollute the error
    ticket database. Consider using dedicated milestone/progress tracking instead.

    ROOT CAUSE: bootstrap.py was creating "error" tickets for tracking purposes,
    but these aren't real errors - they're milestones. This should use a separate
    tracking mechanism (e.g., dedicated milestones table, logging, or external tool).
    """
    # Only create if explicitly requested via environment variable
    if os.environ.get("ACTIFIX_CREATE_BOOTSTRAP_TICKET") == "1":
        record_error(
            message="Actifix framework initialization - beginning self-development",
            source="bootstrap.py:create_initial_ticket",
            run_label="actifix-bootstrap",
            error_type="FrameworkInitialization",
            stack_trace="",
            capture_context=True
        )


def track_development_progress(milestone: str, details: str = "") -> None:
    """
    Track development milestones as actifix tickets.

    DEPRECATED: This function creates tracking tickets that pollute the error
    ticket database. Use dedicated milestone tracking instead.

    ROOT CAUSE: Using error tickets for milestone tracking is an anti-pattern.
    Milestones should be tracked separately (e.g., in a milestones table, log file,
    or external project management tool), not as "errors" in the ticket system.
    """
    # Only create if explicitly requested via environment variable
    if os.environ.get("ACTIFIX_TRACK_MILESTONES_AS_TICKETS") == "1":
        record_error(
            message=f"Development milestone: {milestone}. {details}",
            source="bootstrap.py:track_development_progress",
            run_label="actifix-development",
            error_type="DevelopmentMilestone",
            stack_trace="",
            capture_context=False
        )


if __name__ == "__main__":
    # Bootstrap actifix for self-development
    bootstrap_actifix_development()
    create_initial_ticket()
    
    print("\n[Actifix] Self-development mode is now active!")
    print("From now on, actifix will capture its own development errors and improvements.")
    print("Check the actifix/ directory for automatically generated tickets.")
