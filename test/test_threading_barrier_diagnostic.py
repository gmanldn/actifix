#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detailed diagnostic test to understand the threading issue.

This test adds extensive logging to track database transaction behavior
and see exactly where Thread 2 fails.
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

from actifix.persistence.database import reset_database_pool, get_database_pool
from actifix.persistence.ticket_repo import (
    TicketRepository,
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


def setup_test_env():
    """Create a temporary test environment."""
    tmp_dir = tempfile.mkdtemp(prefix="actifix_diag_")
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
        source="test_diag.py",
        run_label="diag-test",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="DiagError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


def test_transaction_isolation():
    """
    Test to understand transaction and isolation behavior.

    This will show if transactions are interfering with each other.
    """
    print("\n" + "=" * 80)
    print("TEST: Transaction Isolation and Lock Behavior")
    print("=" * 80)

    base, repo, db_path = setup_test_env()
    try:
        # Create 3 tickets
        ticket_ids = [
            "ACT-20260114-DIAG-0",
            "ACT-20260114-DIAG-1",
            "ACT-20260114-DIAG-2",
        ]

        print("\n[SETUP] Creating tickets...")
        for i, ticket_id in enumerate(ticket_ids):
            entry = build_entry(ticket_id, TicketPriority.P1, f"Diag ticket {i}")
            repo.create_ticket(entry)
            print(f"  Created {ticket_id}")

        # Now let's examine the transaction mechanism more carefully
        print("\n[DIAGNOSTIC] Understanding transaction behavior...")

        barrier = threading.Barrier(3)
        results = {
            "connection_ids": [None, None, None],
            "transaction_started": [False, False, False],
            "pre_query_results": [None, None, None],
            "post_update_results": [None, None, None],
            "lock_acquired": [False, False, False],
            "errors": [None, None, None],
        }
        results_lock = threading.Lock()

        def worker(thread_id: int, ticket_id: str):
            """Worker thread that logs transaction details."""
            try:
                # Get connection info
                pool = repo.pool
                conn = pool._get_connection()
                conn_id = id(conn)

                with results_lock:
                    results["connection_ids"][thread_id] = conn_id
                print(f"\n[THREAD {thread_id}] Connection ID: {hex(conn_id)}")
                print(f"[THREAD {thread_id}] SQLite connection: {conn}")
                print(f"[THREAD {thread_id}] Isolation level: {conn.isolation_level}")

                # Wait at barrier
                barrier.wait(timeout=5.0)
                print(f"[THREAD {thread_id}] All threads at barrier")

                # Now try to acquire lock with detailed diagnostics
                print(f"\n[THREAD {thread_id}] Starting lock acquisition for {ticket_id}...")

                now = datetime.now(timezone.utc)
                lease_expires = now + timedelta(seconds=10)

                # Let's manually trace through the acquire_lock logic
                try:
                    with pool.transaction() as conn:
                        with results_lock:
                            results["transaction_started"][thread_id] = True
                        print(f"[THREAD {thread_id}] Transaction started")

                        # Check if ticket exists and is not locked
                        cursor = conn.execute(
                            """
                            SELECT id, locked_by, locked_at, lease_expires
                            FROM tickets
                            WHERE id = ? AND (
                                locked_by IS NULL
                                OR lease_expires < ?
                            )
                            """,
                            (ticket_id, now.isoformat())
                        )

                        row = cursor.fetchone()
                        with results_lock:
                            results["pre_query_results"][thread_id] = (row is not None)
                        print(f"[THREAD {thread_id}] Pre-query result: {row is not None}")

                        if row is None:
                            print(f"[THREAD {thread_id}] Ticket not available (already locked or doesn't exist)")
                            # Check what the actual state is
                            cursor2 = conn.execute(
                                "SELECT id, locked_by, status FROM tickets WHERE id = ?",
                                (ticket_id,)
                            )
                            actual_row = cursor2.fetchone()
                            if actual_row:
                                print(f"[THREAD {thread_id}]   Actual state: locked_by={actual_row['locked_by']}, status={actual_row['status']}")
                            return

                        # Update the lock
                        print(f"[THREAD {thread_id}] Attempting UPDATE...")
                        cursor = conn.execute(
                            """
                            UPDATE tickets
                            SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress'
                            WHERE id = ?
                            """,
                            (
                                f"thread-{thread_id}",
                                now.isoformat(),
                                lease_expires.isoformat(),
                                ticket_id,
                            )
                        )
                        print(f"[THREAD {thread_id}] UPDATE complete, rows affected: {cursor.rowcount}")
                        with results_lock:
                            results["post_update_results"][thread_id] = cursor.rowcount
                        with results_lock:
                            results["lock_acquired"][thread_id] = True
                        print(f"[THREAD {thread_id}] Lock acquisition succeeded in transaction")

                except Exception as e:
                    print(f"[THREAD {thread_id}] Exception during transaction: {e}")
                    import traceback
                    traceback.print_exc()
                    with results_lock:
                        results["errors"][thread_id] = str(e)

                # Verify state after transaction
                print(f"\n[THREAD {thread_id}] Verifying state after transaction...")
                ticket = repo.get_ticket(ticket_id)
                print(f"[THREAD {thread_id}]   locked_by: {ticket['locked_by']}")
                print(f"[THREAD {thread_id}]   status: {ticket['status']}")

            except Exception as e:
                print(f"[THREAD {thread_id}] Outer exception: {e}")
                import traceback
                traceback.print_exc()
                with results_lock:
                    results["errors"][thread_id] = str(e)

        # Launch threads
        print("\n[LAUNCHER] Starting threads...")
        threads = []
        for i, ticket_id in enumerate(ticket_ids):
            t = threading.Thread(target=worker, args=(i, ticket_id))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=10.0)

        # Print results
        print("\n" + "=" * 80)
        print("DIAGNOSTIC RESULTS")
        print("=" * 80)

        for i in range(3):
            print(f"\nThread {i} ({ticket_ids[i]}):")
            print(f"  Connection ID: {hex(results['connection_ids'][i]) if results['connection_ids'][i] else None}")
            print(f"  Transaction started: {results['transaction_started'][i]}")
            print(f"  Pre-query result: {results['pre_query_results'][i]}")
            print(f"  Post-update rows: {results['post_update_results'][i]}")
            print(f"  Lock acquired: {results['lock_acquired'][i]}")
            if results['errors'][i]:
                print(f"  Error: {results['errors'][i]}")

        # Check final database state
        print("\n[FINAL] Database state:")
        for ticket_id in ticket_ids:
            ticket = repo.get_ticket(ticket_id)
            print(f"  {ticket_id}: locked_by={ticket['locked_by']}, status={ticket['status']}")

    finally:
        cleanup_test_env()


def test_raw_sqlite_transaction():
    """
    Test raw SQLite transaction behavior to understand the underlying issue.
    """
    print("\n" + "=" * 80)
    print("TEST: Raw SQLite Transaction Behavior")
    print("=" * 80)

    base, repo, db_path = setup_test_env()
    try:
        # Create a test database to understand transaction behavior
        print(f"\nDatabase path: {db_path}")

        # Create test table
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        conn.isolation_level = "DEFERRED"
        conn.execute("PRAGMA journal_mode = WAL")

        # Create test tickets
        for i in range(3):
            conn.execute(
                "INSERT INTO tickets (id, priority, error_type, message, source, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"RAW-TEST-{i}", "P1", "RawTest", f"Raw test {i}", "test", datetime.now(timezone.utc).isoformat(), "Open")
            )
        conn.commit()

        barrier = threading.Barrier(3)
        results = {"success": [False, False, False], "errors": [None, None, None]}
        results_lock = threading.Lock()

        def raw_worker(thread_id: int):
            """Worker using raw SQLite."""
            try:
                # Create connection for this thread
                thread_conn = sqlite3.connect(str(db_path), timeout=30.0)
                thread_conn.isolation_level = "DEFERRED"

                ticket_id = f"RAW-TEST-{thread_id}"

                barrier.wait(timeout=5.0)
                print(f"\n[RAW {thread_id}] Starting transaction...")

                thread_conn.execute("BEGIN")
                print(f"[RAW {thread_id}] BEGIN executed")

                # Query
                cursor = thread_conn.execute(
                    "SELECT locked_by FROM tickets WHERE id = ?",
                    (ticket_id,)
                )
                row = cursor.fetchone()
                print(f"[RAW {thread_id}] Query result: {row}")

                # Update
                cursor = thread_conn.execute(
                    "UPDATE tickets SET locked_by = ? WHERE id = ?",
                    (f"raw-thread-{thread_id}", ticket_id)
                )
                print(f"[RAW {thread_id}] UPDATE rows: {cursor.rowcount}")

                # Commit
                thread_conn.commit()
                print(f"[RAW {thread_id}] COMMIT executed")

                thread_conn.close()
                with results_lock:
                    results["success"][thread_id] = True

            except Exception as e:
                print(f"[RAW {thread_id}] Error: {e}")
                import traceback
                traceback.print_exc()
                with results_lock:
                    results["errors"][thread_id] = str(e)

        print("\n[RAW] Launching raw SQLite test threads...")
        threads = []
        for i in range(3):
            t = threading.Thread(target=raw_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10.0)

        print(f"\n[RAW] Results: {sum(results['success'])} succeeded")

        # Check final state
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        for i in range(3):
            cursor = conn.execute(
                "SELECT locked_by FROM tickets WHERE id = ?",
                (f"RAW-TEST-{i}",)
            )
            row = cursor.fetchone()
            print(f"  RAW-TEST-{i}: locked_by={row[0] if row else None}")
        conn.close()

    finally:
        cleanup_test_env()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DETAILED DIAGNOSTIC TESTS")
    print("=" * 80)

    test_transaction_isolation()
    test_raw_sqlite_transaction()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
