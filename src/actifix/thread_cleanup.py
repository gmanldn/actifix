"""Thread cleanup utilities for Actifix startup.

This module provides utilities to detect and clean up orphan threads
during system initialization, ensuring a clean startup state.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Sequence

from .log_utils import log_event


@dataclass(frozen=True)
class ThreadInfo:
    """Information about a thread."""
    
    name: str
    ident: int | None
    daemon: bool
    alive: bool


def enumerate_threads() -> Sequence[ThreadInfo]:
    """Enumerate all active threads in the current process.
    
    Returns:
        List of ThreadInfo objects for each active thread.
    """
    threads = []
    for thread in threading.enumerate():
        threads.append(ThreadInfo(
            name=thread.name,
            ident=thread.ident,
            daemon=thread.daemon,
            alive=thread.is_alive(),
        ))
    return threads


def is_orphan_thread(thread_info: ThreadInfo) -> bool:
    """Determine if a thread is an orphan that should be cleaned up.
    
    A thread is considered an orphan if:
    - It's a daemon thread (non-daemon threads should be managed by their owner)
    - It's not the main thread
    - It's not a known system thread (like threading._shutdown_locks_lock owner)
    
    Args:
        thread_info: Thread information to check.
        
    Returns:
        True if the thread is an orphan, False otherwise.
    """
    # Main thread is never an orphan
    if thread_info.name == "MainThread":
        return False
    
    # Keep system threads (like pytest workers, etc.)
    system_thread_prefixes = (
        "pytest",
        "Dummy-",  # threading module internal threads
        "pydevd",  # debugger threads
    )
    if any(thread_info.name.startswith(prefix) for prefix in system_thread_prefixes):
        return False
    
    # Daemon threads that are alive and not system threads are potential orphans
    return thread_info.daemon and thread_info.alive


def cleanup_orphan_threads(timeout: float = 2.0) -> int:
    """Clean up orphan threads at startup.
    
    This function identifies and attempts to clean up orphan threads.
    Since daemon threads don't have a standard way to be stopped,
    this function logs their presence for monitoring purposes.
    
    Args:
        timeout: Maximum time to wait for threads to stop (seconds).
        
    Returns:
        Number of orphan threads detected.
    """
    threads = enumerate_threads()
    orphans = [t for t in threads if is_orphan_thread(t)]
    
    if not orphans:
        log_event("THREAD_CLEANUP_SUCCESS", "No orphan threads detected at startup")
        return 0
    
    # Log detected orphans
    orphan_names = [t.name for t in orphans]
    log_event(
        "THREAD_CLEANUP_ORPHANS_DETECTED",
        f"Detected {len(orphans)} orphan thread(s): {', '.join(orphan_names)}"
    )
    
    # For daemon threads, we can't force-stop them safely.
    # The best we can do is log their presence and let them complete naturally.
    # They will be terminated when the main thread exits.
    
    # Give threads a brief moment to complete if they're finishing
    time.sleep(min(timeout, 0.5))
    
    # Re-check thread status
    remaining_threads = enumerate_threads()
    remaining_orphans = [t for t in remaining_threads if is_orphan_thread(t)]
    
    if len(remaining_orphans) < len(orphans):
        log_event(
            "THREAD_CLEANUP_PARTIAL",
            f"Cleaned {len(orphans) - len(remaining_orphans)} orphan thread(s), "
            f"{len(remaining_orphans)} remaining"
        )
    
    return len(orphans)


def get_thread_summary() -> dict[str, object]:
    """Get a summary of current thread state.
    
    Returns:
        Dictionary with thread statistics and details.
    """
    threads = enumerate_threads()
    orphans = [t for t in threads if is_orphan_thread(t)]
    
    return {
        "total_threads": len(threads),
        "daemon_threads": sum(1 for t in threads if t.daemon),
        "orphan_threads": len(orphans),
        "main_thread_alive": any(t.name == "MainThread" for t in threads),
        "thread_names": [t.name for t in threads],
        "orphan_names": [t.name for t in orphans],
    }


def log_thread_state() -> None:
    """Log current thread state for diagnostics."""
    summary = get_thread_summary()
    log_event(
        "THREAD_STATE_SUMMARY",
        f"Threads: {summary['total_threads']} total, "
        f"{summary['daemon_threads']} daemon, "
        f"{summary['orphan_threads']} orphans. "
        f"Names: {', '.join(summary['thread_names'])}"
    )