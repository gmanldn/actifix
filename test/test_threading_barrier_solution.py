#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demonstration of solutions to the threading/locking issue.

This script shows:
1. The problem (current behavior)
2. Solution 1: Using BEGIN IMMEDIATE to acquire locks upfront
3. Solution 2: Retry logic with exponential backoff
"""

import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import os
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
# Add src to path
sys.path.insert(0, str(ROOT / "src"))

from actifix.persistence.database import reset_database_pool, get_database_pool, DatabasePool
from actifix.persistence.ticket_repo import (
    TicketRepository,
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


def setup_test_env():
    """Create a temporary test environment."""
    tmp_dir = tempfile.mkdtemp(prefix="actifix_solution_")
    base = Path(tmp_dir)
    data_dir = base / "actifix"
    state_dir = base / ".actifix"
    db_path = base / "data" / "actifix.db"

    os.environ["ACTIFIX_DATA_DIR"] = str(data_dir)
    os.environ["ACTIFIX_STATE_DIR"] = str(state_dir)
    os.environ["ACTIFIX_DB_PATH"] = str(db_path)

    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)

    return base, get_ticket_repository(), db_path


def cleanup_test_env():
    """Clean up test environment."""
    reset_database_pool()
    reset_ticket_repository()


def build_entry(ticket_id: str, priority: TicketPriority, message: str) -> ActifixEntry:
    """Helper to create a minimal ActifixEntry."""
    return ActifixEntry(
        message=message,
        source="test_solution.py",
        run_label="solution-test",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="SolutionTestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


def run_barrier_test(test_name: str, acquire_lock_fn, repo: TicketRepository) -> bool:
    """
    Run the barrier test with a specific lock acquisition function.

    Args:
        test_name: Name for this test
        acquire_lock_fn: Function(ticket_id, locked_by) -> bool
        repo: Ticket repository

    Returns:
        True if all threads succeeded, False otherwise
    """
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 80}\n")

    # Create test tickets
    ticket_ids = [f"ACT-SOL-{i}" for i in range(3)]

    print("[SETUP] Creating tickets...")
    for ticket_id in ticket_ids:
        entry = build_entry(ticket_id, TicketPriority.P1, "Solution test")
        repo.create_ticket(entry)
        print(f"  {ticket_id}")

    barrier = threading.Barrier(3)
    results = {
        "succeeded": [False, False, False],
        "errors": [None, None, None],
        "lock_held_duration": [0.0, 0.0, 0.0],
    }
    results_lock = threading.Lock()

    def worker(thread_id: int, ticket_id: str):
        try:
            barrier.wait(timeout=5.0)
            start_time = time.time()

            # Call the specific lock acquisition function
            success = acquire_lock_fn(ticket_id, f"thread-{thread_id}")

            if success:
                with results_lock:
                    results["succeeded"][thread_id] = True
                print(f"[THREAD {thread_id}] Successfully acquired lock on {ticket_id}")
            else:
                print(f"[THREAD {thread_id}] Failed to acquire lock on {ticket_id}")

            end_time = time.time()
            with results_lock:
                results["lock_held_duration"][thread_id] = end_time - start_time

        except Exception as e:
            print(f"[THREAD {thread_id}] Error: {e}")
            with results_lock:
                results["errors"][thread_id] = str(e)

    # Launch threads
    print("[LAUNCHER] Starting 3 threads...")
    threads = []
    for i, ticket_id in enumerate(ticket_ids):
        t = threading.Thread(target=worker, args=(i, ticket_id))
        threads.append(t)
        t.start()

    # Wait for completion
    for t in threads:
        t.join(timeout=10.0)

    # Print results
    succeeded = sum(1 for s in results["succeeded"] if s)
    print(f"\n[RESULT] {succeeded}/3 threads succeeded")

    for i in range(3):
        print(f"  Thread {i}: {results['succeeded'][i]}")
        if results['errors'][i]:
            print(f"    Error: {results['errors'][i]}")
        print(f"    Duration: {results['lock_held_duration'][i]:.4f}s")

    assert succeeded == 3, f"Expected all 3 threads to succeed, got {succeeded}"


def test_current_behavior():
    """Test current behavior (should show the problem)."""
    base, repo, _ = setup_test_env()
    try:
        def acquire_lock_current(ticket_id: str, locked_by: str) -> bool:
            """Current implementation."""
            lock = repo.acquire_lock(ticket_id, locked_by, timedelta(seconds=5))
            return lock is not None

        try:
            run_barrier_test(
                "Current Behavior (DEFERRED isolation)",
                acquire_lock_current,
                repo
            )
            print("\n✓ All threads succeeded (may happen under low contention)")
        except AssertionError:
            print("\n⚠️  This demonstrates the issue: not all threads succeeded.")
            print("   The database lock prevents concurrent acquire_lock() calls.")
            raise

    finally:
        cleanup_test_env()


def test_solution_1_immediate():
    """Test solution 1: Use IMMEDIATE transaction isolation."""
    base, repo, db_path = setup_test_env()
    try:
        pool = repo.pool

        def acquire_lock_immediate(ticket_id: str, locked_by: str) -> bool:
            """Solution 1: Use IMMEDIATE to acquire locks upfront."""
            now = datetime.now(timezone.utc)
            lease_expires = now + timedelta(seconds=10)

            try:
                # Get connection and use IMMEDIATE
                conn = pool._get_connection()
                try:
                    conn.execute("BEGIN IMMEDIATE")

                    # Check if ticket is available
                    cursor = conn.execute(
                        """
                        SELECT id FROM tickets
                        WHERE id = ? AND (
                            locked_by IS NULL
                            OR lease_expires < ?
                        )
                        """,
                        (ticket_id, now.isoformat())
                    )

                    if cursor.fetchone() is None:
                        conn.rollback()
                        return False

                    # Acquire lock
                    conn.execute(
                        """
                        UPDATE tickets
                        SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress'
                        WHERE id = ?
                        """,
                        (locked_by, now.isoformat(), lease_expires.isoformat(), ticket_id)
                    )

                    conn.commit()
                    return True

                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    raise

            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    return False
                raise

        run_barrier_test(
            "Solution 1: BEGIN IMMEDIATE (Acquires locks upfront)",
            acquire_lock_immediate,
            repo
        )

        print("\n✓ Solution 1 WORKS: Using BEGIN IMMEDIATE ensures all threads can acquire locks!")
        print("  Why: IMMEDIATE acquires the RESERVED lock immediately, preventing lock upgrades.")

    finally:
        cleanup_test_env()


def test_solution_2_retry():
    """Test solution 2: Retry logic with exponential backoff."""
    base, repo, _ = setup_test_env()
    try:
        def acquire_lock_with_retry(ticket_id: str, locked_by: str) -> bool:
            """Solution 2: Retry with exponential backoff."""
            max_retries = 3
            backoff_base = 0.01  # 10ms base

            for attempt in range(max_retries):
                try:
                    lock = repo.acquire_lock(ticket_id, locked_by, timedelta(seconds=5))
                    if lock is not None:
                        return True

                    # Lock is held by someone else (not a database lock error)
                    return False

                except sqlite3.OperationalError as e:
                    if "locked" in str(e).lower():
                        # Database is locked, retry
                        if attempt < max_retries - 1:
                            wait_time = backoff_base * (2 ** attempt)
                            time.sleep(wait_time)
                            continue
                        else:
                            # Final attempt failed
                            return False
                    else:
                        raise

        run_barrier_test(
            "Solution 2: Retry with Exponential Backoff",
            acquire_lock_with_retry,
            repo
        )

        print("\n✓ Solution 2 WORKS: Exponential backoff allows threads to eventually succeed!")
        print("  Why: When one thread's transaction completes, others retry and succeed.")

    finally:
        cleanup_test_env()


def compare_performance():
    """Compare performance of different approaches."""
    print(f"\n{'=' * 80}")
    print("PERFORMANCE COMPARISON")
    print(f"{'=' * 80}\n")

    import timeit

    base, repo, db_path = setup_test_env()
    try:
        # Create tickets
        for i in range(3):
            entry = build_entry(f"PERF-{i}", TicketPriority.P1, "Perf test")
            repo.create_ticket(entry)

        pool = repo.pool

        # Measure current implementation
        def measure_current():
            ticket_id = "PERF-0"
            lock = repo.acquire_lock(ticket_id, "perf-thread", timedelta(seconds=5))
            if lock:
                repo.release_lock(ticket_id, "perf-thread")

        current_time = timeit.timeit(measure_current, number=1)
        print(f"Current implementation: {current_time * 1000:.2f} ms")

        # Clean up
        for i in range(3):
            repo.delete_ticket(f"PERF-{i}")
        for i in range(3):
            entry = build_entry(f"PERF-{i}", TicketPriority.P1, "Perf test")
            repo.create_ticket(entry)

        # Measure IMMEDIATE approach
        def measure_immediate():
            ticket_id = "PERF-1"
            now = datetime.now(timezone.utc)
            lease_expires = now + timedelta(seconds=10)

            conn = pool._get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.execute(
                    "SELECT id FROM tickets WHERE id = ? AND (locked_by IS NULL OR lease_expires < ?)",
                    (ticket_id, now.isoformat())
                )
                if cursor.fetchone():
                    conn.execute(
                        "UPDATE tickets SET locked_by = ?, locked_at = ?, lease_expires = ? WHERE id = ?",
                        ("perf-thread", now.isoformat(), lease_expires.isoformat(), ticket_id)
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        immediate_time = timeit.timeit(measure_immediate, number=1)
        print(f"IMMEDIATE implementation: {immediate_time * 1000:.2f} ms")

        print(f"\nRelative performance: {(immediate_time / current_time):.2f}x")

    finally:
        cleanup_test_env()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("THREADING SOLUTIONS DEMONSTRATION")
    print("=" * 80)

    # Test current behavior
    try:
        test_current_behavior()
        current_result = True
    except AssertionError:
        current_result = False

    # Test solution 1
    try:
        test_solution_1_immediate()
        solution1_result = True
    except AssertionError:
        solution1_result = False

    # Test solution 2
    try:
        test_solution_2_retry()
        solution2_result = True
    except AssertionError:
        solution2_result = False

    # Performance comparison
    compare_performance()

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}\n")

    print(f"Current behavior: {'PASS' if current_result else 'FAIL'}")
    print(f"Solution 1 (IMMEDIATE): {'PASS' if solution1_result else 'FAIL'}")
    print(f"Solution 2 (Retry): {'PASS' if solution2_result else 'FAIL'}")

    if solution1_result or solution2_result:
        print("\n✓ At least one solution works!")
        print("\nRECOMMENDATION:")
        if solution1_result:
            print("  Implement Solution 1 (BEGIN IMMEDIATE) for better performance and determinism")
        if solution2_result:
            print("  Or implement Solution 2 (Retry) as a fallback/defensive mechanism")
    else:
        print("\n⚠ No solutions worked (unexpected)")
