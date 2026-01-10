"""
Actifix Bootstrap - Single canonical entrypoint and environment normalization.

Provides the single entry point that must be used to start the system.
Establishes correct runtime environment, validates configuration, and
performs pre-run safety checks.
"""

import hashlib
import os
import sys
import signal
import atexit
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

from .state_paths import get_actifix_paths, init_actifix_files, ActifixPaths
from .log_utils import atomic_write, log_event


# Global state for the bootstrapped environment
_bootstrap_state: Optional["BootstrapState"] = None


@dataclass
class BootstrapState:
    """State of the bootstrapped Actifix environment."""
    
    # Core identifiers
    run_id: str
    correlation_id: str
    started_at: datetime
    
    # Paths
    paths: ActifixPaths
    project_root: Path
    
    # Status
    initialized: bool = False
    shutdown_requested: bool = False
    
    # Cleanup handlers
    cleanup_handlers: list = field(default_factory=list)
    
    # Process tracking
    pid: int = 0
    lock_file: Optional[Path] = None


def generate_run_id() -> str:
    """Generate unique run identifier."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    random_suffix = hashlib.sha256(os.urandom(8)).hexdigest()[:6]
    return f"run_{timestamp}_{random_suffix}"


def generate_correlation_id() -> str:
    """Generate correlation ID for tracing across components."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_suffix = hashlib.sha256(os.urandom(8)).hexdigest()[:8]
    return f"corr_{timestamp}_{random_suffix}"


def _validate_environment() -> list[str]:
    """
    Validate the runtime environment.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required, got {sys.version}")
    
    # Check required directories are writable
    cwd = Path.cwd()
    if not os.access(cwd, os.W_OK):
        errors.append(f"Current directory not writable: {cwd}")
    
    return errors


def _normalize_import_paths(project_root: Path) -> None:
    """Ensure project root is in Python path."""
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    
    # Also add src if it exists
    src_path = project_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _cleanup_stale_locks(paths: ActifixPaths) -> None:
    """Remove stale lock files from previous runs."""
    lock_file = paths.list_lock
    
    if lock_file.exists():
        try:
            # Check if lock is stale (file content has PID)
            content = lock_file.read_text().strip()
            if content.isdigit():
                pid = int(content)
                # Check if process is still running
                try:
                    os.kill(pid, 0)
                    # Process exists - lock is active
                except OSError:
                    # Process doesn't exist - stale lock
                    lock_file.unlink()
        except Exception:
            # Error reading lock, remove it
            try:
                lock_file.unlink()
            except OSError:
                pass


def _acquire_lock(paths: ActifixPaths) -> Path:
    """Acquire process lock file."""
    lock_file = paths.list_lock
    lock_file.write_text(str(os.getpid()))
    return lock_file


def _release_lock(lock_file: Optional[Path]) -> None:
    """Release process lock file."""
    if lock_file and lock_file.exists():
        try:
            lock_file.unlink()
        except OSError:
            pass


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    global _bootstrap_state
    if _bootstrap_state:
        _bootstrap_state.shutdown_requested = True
        shutdown()


def _atexit_handler() -> None:
    """Handle process exit cleanup."""
    shutdown()


def bootstrap(
    project_root: Optional[Path] = None,
    run_name: Optional[str] = None,
    fail_fast: bool = True,
) -> BootstrapState:
    """
    Bootstrap the Actifix system.
    
    This is the SINGLE CANONICAL ENTRYPOINT for the system.
    Must be called before any other Actifix operations.
    
    Args:
        project_root: Project root directory. Defaults to cwd.
        run_name: Optional name for this run.
        fail_fast: If True, raise on validation errors.
    
    Returns:
        BootstrapState with initialized environment.
    
    Raises:
        RuntimeError: If environment validation fails and fail_fast=True.
        RuntimeError: If already bootstrapped.
    """
    global _bootstrap_state
    
    if _bootstrap_state is not None:
        if _bootstrap_state.initialized:
            raise RuntimeError(
                "Actifix already bootstrapped. "
                "Call shutdown() before re-bootstrapping."
            )
    
    # Determine project root
    if project_root is None:
        project_root = Path.cwd()
    project_root = project_root.resolve()
    
    # Validate environment
    errors = _validate_environment()
    if errors and fail_fast:
        raise RuntimeError(
            f"Environment validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    
    # Normalize import paths
    _normalize_import_paths(project_root)
    
    # Get Actifix paths
    paths = get_actifix_paths(project_root=project_root)
    
    # Initialize files
    init_actifix_files(paths)
    
    # Cleanup stale locks
    _cleanup_stale_locks(paths)
    
    # Generate identifiers
    run_id = run_name or generate_run_id()
    correlation_id = generate_correlation_id()
    
    # Create state
    _bootstrap_state = BootstrapState(
        run_id=run_id,
        correlation_id=correlation_id,
        started_at=datetime.now(timezone.utc),
        paths=paths,
        project_root=project_root,
        pid=os.getpid(),
    )
    
    # Acquire lock
    _bootstrap_state.lock_file = _acquire_lock(paths)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    
    # Register atexit handler
    atexit.register(_atexit_handler)
    
    # Mark as initialized
    _bootstrap_state.initialized = True
    
    # Log bootstrap event
    log_event(
        paths.aflog_file,
        "BOOTSTRAP",
        f"Actifix bootstrapped: {run_id}",
        extra={
            "correlation_id": correlation_id,
            "project_root": str(project_root),
            "pid": os.getpid(),
        }
    )
    
    return _bootstrap_state


def get_state() -> Optional[BootstrapState]:
    """Get current bootstrap state, or None if not bootstrapped."""
    return _bootstrap_state


def require_bootstrap() -> BootstrapState:
    """
    Get bootstrap state, raising if not bootstrapped.
    
    Use this at the start of functions that require bootstrapping.
    
    Raises:
        RuntimeError: If not bootstrapped.
    """
    if _bootstrap_state is None or not _bootstrap_state.initialized:
        raise RuntimeError(
            "Actifix not bootstrapped. "
            "Call actifix.bootstrap() first."
        )
    return _bootstrap_state


def get_correlation_id() -> str:
    """Get current correlation ID for tracing."""
    state = get_state()
    if state:
        return state.correlation_id
    return "no-correlation"


def get_run_id() -> str:
    """Get current run ID."""
    state = get_state()
    if state:
        return state.run_id
    return "no-run"


def register_cleanup(handler: Callable[[], None]) -> None:
    """
    Register a cleanup handler to be called on shutdown.
    
    Args:
        handler: Callable with no arguments.
    """
    state = get_state()
    if state:
        state.cleanup_handlers.append(handler)


def shutdown() -> None:
    """
    Shutdown the Actifix system cleanly.
    
    Runs all registered cleanup handlers and releases resources.
    """
    global _bootstrap_state
    
    if _bootstrap_state is None:
        return
    
    if not _bootstrap_state.initialized:
        return
    
    # Run cleanup handlers in reverse order
    for handler in reversed(_bootstrap_state.cleanup_handlers):
        try:
            handler()
        except Exception:
            pass  # Don't fail shutdown on handler errors
    
    # Log shutdown
    try:
        log_event(
            _bootstrap_state.paths.aflog_file,
            "SHUTDOWN",
            f"Actifix shutdown: {_bootstrap_state.run_id}",
            extra={
                "correlation_id": _bootstrap_state.correlation_id,
                "duration_seconds": (
                    datetime.now(timezone.utc) - 
                    _bootstrap_state.started_at
                ).total_seconds(),
            }
        )
    except Exception:
        pass
    
    # Release lock
    _release_lock(_bootstrap_state.lock_file)
    
    # Clear state
    _bootstrap_state.initialized = False
    _bootstrap_state = None
    
    # Unregister atexit handler
    try:
        atexit.unregister(_atexit_handler)
    except Exception:
        pass


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested via signal."""
    state = get_state()
    return state.shutdown_requested if state else False


class ActifixContext:
    """
    Context manager for Actifix bootstrap.
    
    Usage:
        with ActifixContext() as ctx:
            # Do work with ctx.paths, ctx.run_id, etc.
            pass
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        run_name: Optional[str] = None,
    ):
        self.project_root = project_root
        self.run_name = run_name
        self.state: Optional[BootstrapState] = None
    
    def __enter__(self) -> BootstrapState:
        self.state = bootstrap(
            project_root=self.project_root,
            run_name=self.run_name,
        )
        return self.state
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        shutdown()
        return False  # Don't suppress exceptions
