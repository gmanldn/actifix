#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug test: Threading with barrier and concurrent lock acquisition

This test reproduces the issue where multiple threads synchronize at a barrier
but then get stuck when trying to acquire database locks on different tickets.

The issue appears to be that threads are blocking on getting database connections
from the pool, even though each thread should get its own thread-local connection.
"""

import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from actifix.persistence.database import reset_database_pool, DatabasePool, DatabaseConfig
from actifix.persistence.ticket_repo import (
    TicketRepository,
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


def setup_test_env():
    """Create a temporary test environment."""
    tmp_dir = tempfile.mkdtemp(prefix="actifix_test_barrier_")
    base = Path(tmp_dir)
    data_dir = base / "actifix"
    state_dir = base / ".actifix"
    db_path = base / "data" / "actifix.db"

    os.environ["ACTIFIX_DATA_DIR"] = str(data_dir)
    os.environ["ACTIFIX_STATE_DIR"] = str(state_dir)
    os.environ["ACTIFIX_DB_PATH"] = str(db_path)

    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)

    return base, get_ticket_repository()


def cleanup_test_env():
    """Clean up test environment."""
    reset_database_pool()
    reset_ticket_repository()


def build_entry(ticket_id: str, priority: TicketPriority, message: str) -> ActifixEntry:
    """Helper to create a minimal ActifixEntry."""
    return ActifixEntry(
        message=message,
        source="test_barrier.py",
        run_label="barrier-test",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="BarrierTestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


def test_barrier_with_locks():
    """
    Test that reproduces the threading issue:
    - 3 threads created
    - Each thread waits at a barrier
    - After barrier, each thread tries to acquire a lock on a different ticket
    - Expected: All 3 threads should proceed and acquire their locks
    - Observed: Only 1 thread completes, others seem stuck
    """
    print("\n" + "=" * 80)
    print("TEST: Threading with Barrier and Concurrent Lock Acquisition")
    print("=" * 80)

    base, repo = setup_test_env()
    try:
        # Create 3 tickets
        ticket_ids = [
            "ACT-20260114-REACQ-0",
            "ACT-20260114-REACQ-1",
            "ACT-20260114-REACQ-2",
        ]

        print("\n[SETUP] Creating tickets...")
        for i, ticket_id in enumerate(ticket_ids):
            entry = build_entry(ticket_id, TicketPriority.P1, f"Test ticket {i}")
            result = repo.create_ticket(entry)
            print(f"  Created {ticket_id}: {result}")

        # Verify tickets exist
        stats = repo.get_stats()
        print(f"\n[SETUP] Stats after creation: {stats}")

        # Prepare barrier and results tracking
        barrier = threading.Barrier(3)
        results = {
            "thread_started": [False, False, False],
            "thread_at_barrier": [False, False, False],
            "thread_barrier_passed": [False, False, False],
            "thread_attempting_lock": [False, False, False],
            "thread_lock_acquired": [False, False, False],
            "thread_lock_released": [False, False, False],
            "thread_completed": [False, False, False],
            "thread_errors": [None, None, None],
        }
        results_lock = threading.Lock()

        def worker(thread_id: int, ticket_id: str):
            """Worker thread function."""
            try:
                with results_lock:
                    results["thread_started"][thread_id] = True
                print(f"\n[THREAD {thread_id}] Started for ticket {ticket_id}")
                print(f"[THREAD {thread_id}] Thread ID: {threading.current_thread().ident}")

                # Wait at barrier
                with results_lock:
                    results["thread_at_barrier"][thread_id] = True
                print(f"[THREAD {thread_id}] Waiting at barrier...")

                barrier.wait(timeout=5.0)

                with results_lock:
                    results["thread_barrier_passed"][thread_id] = True
                print(f"[THREAD {thread_id}] Passed barrier, all threads synchronized!")

                # Try to acquire lock
                with results_lock:
                    results["thread_attempting_lock"][thread_id] = True
                print(f"[THREAD {thread_id}] Attempting to acquire lock on {ticket_id}...")

                lock_result = repo.acquire_lock(
                    ticket_id,
                    locked_by=f"thread-{thread_id}",
                    lease_duration=timedelta(seconds=10),
                )

                if lock_result:
                    with results_lock:
                        results["thread_lock_acquired"][thread_id] = True
                    print(f"[THREAD {thread_id}] Lock acquired successfully!")
                    print(f"[THREAD {thread_id}]   locked_by: {lock_result.locked_by}")
                    print(f"[THREAD {thread_id}]   locked_at: {lock_result.locked_at}")
                    print(f"[THREAD {thread_id}]   lease_expires: {lock_result.lease_expires}")

                    # Hold the lock briefly
                    time.sleep(0.5)

                    # Release lock
                    release_result = repo.release_lock(ticket_id, locked_by=f"thread-{thread_id}")
                    with results_lock:
                        results["thread_lock_released"][thread_id] = release_result
                    print(f"[THREAD {thread_id}] Lock released: {release_result}")
                else:
                    print(f"[THREAD {thread_id}] ERROR: Failed to acquire lock!")
                    with results_lock:
                        results["thread_errors"][thread_id] = "Failed to acquire lock"

                with results_lock:
                    results["thread_completed"][thread_id] = True
                print(f"[THREAD {thread_id}] Completed successfully!")

            except Exception as e:
                print(f"[THREAD {thread_id}] EXCEPTION: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                with results_lock:
                    results["thread_errors"][thread_id] = str(e)

        # Launch threads
        print("\n[LAUNCHER] Starting 3 worker threads...")
        threads = []
        for i, ticket_id in enumerate(ticket_ids):
            t = threading.Thread(target=worker, args=(i, ticket_id), name=f"Worker-{i}")
            threads.append(t)
            t.start()

        # Wait for threads with timeout
        print("\n[LAUNCHER] Waiting for threads to complete (timeout: 10s)...")
        for i, t in enumerate(threads):
            t.join(timeout=10.0)
            if t.is_alive():
                print(f"[LAUNCHER] WARNING: Thread {i} still alive after timeout!")
            else:
                print(f"[LAUNCHER] Thread {i} finished")

        # Print results summary
        print("\n" + "=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)

        for i in range(3):
            print(f"\nThread {i} ({ticket_ids[i]}):")
            print(f"  Started: {results['thread_started'][i]}")
            print(f"  At barrier: {results['thread_at_barrier'][i]}")
            print(f"  Passed barrier: {results['thread_barrier_passed'][i]}")
            print(f"  Attempting lock: {results['thread_attempting_lock'][i]}")
            print(f"  Lock acquired: {results['thread_lock_acquired'][i]}")
            print(f"  Lock released: {results['thread_lock_released'][i]}")
            print(f"  Completed: {results['thread_completed'][i]}")
            if results['thread_errors'][i]:
                print(f"  ERROR: {results['thread_errors'][i]}")

        # Check final state
        print("\n[FINAL] Checking database state...")
        final_stats = repo.get_stats()
        print(f"  Total tickets: {final_stats['total']}")
        print(f"  Open: {final_stats['open']}")
        print(f"  In Progress: {final_stats['in_progress']}")
        print(f"  Completed: {final_stats['completed']}")
        print(f"  Locked: {final_stats['locked']}")

        # Check for any locks still held
        for ticket_id in ticket_ids:
            ticket = repo.get_ticket(ticket_id)
            print(f"  {ticket_id}: locked_by={ticket['locked_by']}, status={ticket['status']}")

        # Determine if test passed
        completed_count = sum(1 for c in results["thread_completed"] if c)
        acquired_count = sum(1 for a in results["thread_lock_acquired"] if a)

        print("\n" + "=" * 80)
        print(f"ANALYSIS: {completed_count}/3 threads completed, {acquired_count}/3 locks acquired")
        print("=" * 80)

        if completed_count == 3 and acquired_count == 3:
            print("SUCCESS: All threads completed and acquired locks!")
            return True
        else:
            print("FAILURE: Not all threads completed or acquired locks!")
            print("\nPOSSIBLE ROOT CAUSES:")
            if completed_count < 3:
                print("  1. Threads are blocked waiting for database connections")
                print("  2. Connection pool may have insufficient connections")
                print("  3. Transactions may be holding locks longer than expected")
            if acquired_count < completed_count:
                print("  1. Ticket locking logic has a race condition")
                print("  2. Database isolation level may be causing issues")
            return False

    finally:
        cleanup_test_env()


def test_simple_barrier():
    """
    Control test: Simple barrier test without database access.
    This should always work and proves barrier itself is functioning.
    """
    print("\n" + "=" * 80)
    print("CONTROL TEST: Simple Barrier Without Database")
    print("=" * 80)

    barrier = threading.Barrier(3)
    results = {"passed": [False, False, False]}
    results_lock = threading.Lock()

    def worker(thread_id: int):
        print(f"[THREAD {thread_id}] Waiting at barrier...")
        barrier.wait(timeout=5.0)
        with results_lock:
            results["passed"][thread_id] = True
        print(f"[THREAD {thread_id}] Passed barrier!")

    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,), name=f"SimpleWorker-{i}")
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=10.0)

    passed_count = sum(1 for p in results["passed"] if p)
    print(f"\nRESULT: {passed_count}/3 threads passed barrier")

    if passed_count == 3:
        print("SUCCESS: Barrier works correctly!")
        return True
    else:
        print("FAILURE: Barrier test failed!")
        return False


def inspect_database_pool_config():
    """Inspect the database pool configuration."""
    print("\n" + "=" * 80)
    print("DATABASE POOL CONFIGURATION")
    print("=" * 80)

    base, repo = setup_test_env()
    try:
        pool = repo.pool
        config = pool.config

        print(f"Database path: {config.db_path}")
        print(f"Enable WAL: {config.enable_wal}")
        print(f"Timeout: {config.timeout} seconds")
        print(f"Check same thread: {config.check_same_thread}")
        print(f"Isolation level: {config.isolation_level}")
        print(f"\nThread-local storage: {hasattr(pool._local, 'connection')}")
        print(f"Lock object: {pool._lock}")

    finally:
        cleanup_test_env()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ACTIFIX THREADING AND LOCKING DEBUG TEST")
    print("=" * 80)

    # Run control test first
    control_result = test_simple_barrier()

    # Inspect configuration
    inspect_database_pool_config()

    # Run main test
    main_result = test_barrier_with_locks()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Control test (simple barrier): {'PASS' if control_result else 'FAIL'}")
    print(f"Main test (barrier + locking): {'PASS' if main_result else 'FAIL'}")

    sys.exit(0 if main_result else 1)
