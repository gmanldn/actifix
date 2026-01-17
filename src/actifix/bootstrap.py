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
from typing import Optional

from .raise_af import record_error, ACTIFIX_CAPTURE_ENV_VAR, enforce_raise_af_only
from .state_paths import get_actifix_paths, init_actifix_files, ActifixPaths


def enable_actifix_capture():
    """Enable actifix error capture for development."""
    os.environ[ACTIFIX_CAPTURE_ENV_VAR] = "1"


def disable_actifix_capture():
    """Disable actifix error capture."""
    if ACTIFIX_CAPTURE_ENV_VAR in os.environ:
        del os.environ[ACTIFIX_CAPTURE_ENV_VAR]


def capture_exception(exc_type, exc_value, exc_traceback):
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


def install_exception_handler():
    """Install global exception handler for actifix development."""
    original_handler = sys.excepthook
    
    def actifix_excepthook(exc_type, exc_value, exc_traceback):
        # Capture with actifix first
        capture_exception(exc_type, exc_value, exc_traceback)
        
        # Then call the original handler
        original_handler(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = actifix_excepthook
    return original_handler


def uninstall_exception_handler(original_handler):
    """Restore the original exception handler."""
    sys.excepthook = original_handler


def bootstrap_actifix_development():
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
    
    print(f"[Actifix] Data directory: {data_dir}")
    print(f"[Actifix] State directory: {state_dir}")
    print("[Actifix] Self-development mode active - actifix will track its own development issues!")
    
    return original_handler


def bootstrap(project_root: Optional[Path] = None) -> ActifixPaths:
    """
    Initialize Actifix paths for a project.

    Args:
        project_root: Optional project root to initialize.

    Returns:
        Initialized ActifixPaths.
    """
    enforce_raise_af_only(get_actifix_paths(project_root=project_root))
    paths = get_actifix_paths(project_root=project_root)
    init_actifix_files(paths)
    return paths


def shutdown() -> None:
    """Shutdown hook for Actifix lifecycle (no-op placeholder)."""
    return None


class ActifixContext:
    """Context manager to bootstrap Actifix lifecycle."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self.paths: Optional[ActifixPaths] = None

    def __enter__(self) -> ActifixPaths:
        self.paths = bootstrap(self.project_root)
        return self.paths

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        shutdown()


def create_initial_ticket():
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


def track_development_progress(milestone: str, details: str = ""):
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
