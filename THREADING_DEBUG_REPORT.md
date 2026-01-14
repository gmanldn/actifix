# Threading and Database Locking Debug Report

## Executive Summary

The test revealed a critical issue with concurrent ticket locking in the Actifix system. When three threads synchronize at a barrier and then attempt to acquire locks on different ticket IDs, only one thread succeeds while the others fail with "database is locked" errors.

**Root Cause:** SQLite database lock contention due to long-running transactions blocking concurrent operations.

---

## Problem Description

### Test Setup
- 3 threads created with barrier synchronization
- Each thread tries to acquire a lock on a different ticket ID:
  - Thread 0 → ACT-20260114-REACQ-0
  - Thread 1 → ACT-20260114-REACQ-1
  - Thread 2 → ACT-20260114-REACQ-2

### Expected Behavior
All three threads should:
1. Hit the barrier and synchronize
2. Each acquire a lock on their respective ticket
3. Release the lock and complete

### Actual Behavior
- Thread 0: ✅ Successfully acquires lock on ACT-20260114-REACQ-0
- Thread 1: ❌ Fails with "database is locked" error
- Thread 2: ❌ Fails with "database is locked" error

After all threads complete, all tickets show `locked_by=None` and `status=Open` (all locks were released).

---

## Root Cause Analysis

### The Problem: SQLite DEFERRED Transaction Locking

The database pool is configured with:
```python
isolation_level: Optional[str] = "DEFERRED"
```

With DEFERRED isolation level in SQLite:
- **BEGIN** is issued but no locks are acquired
- Locks are acquired lazily when the first SQL statement needs them
- **Read operations** acquire SHARED locks (multiple readers allowed)
- **Write operations** acquire RESERVED → PENDING → EXCLUSIVE locks

### Transaction Sequence

When all three threads call `repo.acquire_lock()` at nearly the same time:

```
Time  Thread 0                Thread 1                Thread 2
────  ────────────────────    ──────────────────────  ──────────────────
1     BEGIN                   BEGIN                   BEGIN
2     SELECT (acquires        SELECT (waits...)       SELECT (waits...)
      SHARED lock)
3     UPDATE (upgrades to     [BLOCKED]               [BLOCKED]
      RESERVED → EXCLUSIVE)
4     UPDATE succeeds
5     Commit (releases lock)
6                             SELECT succeeds
7                             UPDATE (acquire lock)
8                             UPDATE blocked
                              by other operations
```

### Why Thread 1 and 2 Get "Database is Locked"

1. **Thread 0** acquires an EXCLUSIVE lock with its transaction
2. **Thread 1** tries to execute SELECT but Thread 0 still holds the exclusive lock
3. Thread 1 gets "database is locked" during the SELECT query itself
4. Same for Thread 2

The issue is that with SQLite's DEFERRED transaction model:
- Once any thread starts a write transaction (Thread 0's UPDATE), it locks the database
- Other threads' SELECT statements are blocked waiting for locks
- If the timeout (30 seconds) is exceeded before Thread 0 commits, other threads fail

**Critical Detail:** The database timeout is 30 seconds, but concurrent transaction scheduling can cause timeouts to be exceeded even with sufficient time if multiple transactions fight over locks.

---

## Technical Details

### Connection Pool Configuration

File: `src/actifix/persistence/database.py`

```python
@dataclass
class DatabaseConfig:
    db_path: Path
    enable_wal: bool = True                    # Write-Ahead Logging enabled
    timeout: float = 30.0                      # 30-second timeout
    check_same_thread: bool = False            # Multi-threaded access allowed
    isolation_level: Optional[str] = "DEFERRED" # Lazy lock acquisition
```

### Transaction Mechanism

```python
@contextlib.contextmanager
def transaction(self) -> Iterator[sqlite3.Connection]:
    conn = self._get_connection()
    try:
        conn.execute("BEGIN")                   # Explicit BEGIN
        yield conn
        conn.commit()                           # Explicit COMMIT
    except Exception:
        conn.rollback()
        raise
```

### Lock Acquisition Code

File: `src/actifix/persistence/ticket_repo.py`, line 309-372

```python
def acquire_lock(self, ticket_id: str, locked_by: str,
                 lease_duration: timedelta = timedelta(hours=1)
                 ) -> Optional[TicketLock]:
    with self.pool.transaction() as conn:      # Opens transaction
        # SELECT to check if ticket is available
        cursor = conn.execute(
            "SELECT id, locked_by, locked_at, lease_expires FROM tickets WHERE id = ? AND (...)",
            (ticket_id, serialize_timestamp(now))
        )
        row = cursor.fetchone()

        if row is None:
            return None

        # UPDATE to acquire lock
        conn.execute(
            "UPDATE tickets SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress' WHERE id = ?",
            (locked_by, serialize_timestamp(now), serialize_timestamp(lease_expires), ticket_id,)
        )
        # Transaction commits here (implicitly in context manager)
```

---

## Diagnostic Test Results

### Test Output Summary

From `test_threading_barrier_diagnostic.py`:

```
[THREAD 0] UPDATE complete, rows affected: 1
[THREAD 0] Lock acquisition succeeded in transaction

[THREAD 2] Exception during transaction: database is locked
[THREAD 1] Exception during transaction: database is locked

[FINAL] Database state:
  ACT-20260114-DIAG-0: locked_by=thread-0, status=In Progress
  ACT-20260114-DIAG-1: locked_by=None, status=Open
  ACT-20260114-DIAG-2: locked_by=None, status=Open
```

### Key Observations

1. **Connection IDs are different:** Each thread gets its own thread-local SQLite connection
   - Thread 0: `0x107b37a60`
   - Thread 1: `0x107b37970`
   - Thread 2: `0x107b37c40`
   - ✓ This is correct behavior

2. **Isolation levels are DEFERRED for all:** `isolation_level: DEFERRED`
   - ✓ This is configured correctly

3. **All three threads start transactions:** All execute `BEGIN` successfully
   - ✓ This is expected

4. **First SELECT queries succeed:** Thread 0, 1, and 2 all get `Pre-query result: True`
   - ⚠️ This is surprising - suggests all threads acquired SHARED locks
   - But then Thread 0's UPDATE succeeds while 1 and 2 fail on UPDATE

5. **The UPDATE is where threads 1 and 2 fail:** They get "database is locked" on the UPDATE statement
   - ✓ This confirms the lock contention issue

---

## Why WAL Mode Doesn't Fully Solve This

The database is configured with WAL (Write-Ahead Logging) enabled:

```python
if self.config.enable_wal:
    conn.execute("PRAGMA journal_mode = WAL")
```

WAL mode is designed to improve concurrency by:
- Allowing readers to run concurrently with writers
- Separating reads from writes

**However:** WAL mode still enforces serialization for concurrent writers. Multiple threads cannot UPDATE different rows simultaneously if they're in overlapping transactions. The write lock at the database level still prevents concurrent modifications.

---

## Why This Matters for Actifix

The ticket locking system relies on atomic compare-and-swap operations:
1. Check if ticket is locked
2. If not locked, acquire lock
3. All within a single transaction

This pattern requires:
- Isolation from other transactions
- Atomic multi-statement execution
- Strong consistency

SQLite's locking model provides this, but at the cost of serialization under heavy concurrent load.

---

## Solutions and Recommendations

### Short-term Fix: Reduce Transaction Scope

The current implementation holds a transaction open for the entire `acquire_lock` operation:

```python
# CURRENT (Long transaction)
with self.pool.transaction() as conn:
    cursor = conn.execute("SELECT ...")
    if row is not None:
        conn.execute("UPDATE ...")
    # Transaction held until this point
```

**Problem:** This can hold the database lock for too long, blocking other threads.

**Better approach:** Use SQLite's row-level locking capabilities more effectively:

```python
# IMPROVED (Shorter transaction, retry on conflict)
max_retries = 3
for attempt in range(max_retries):
    try:
        with self.pool.transaction() as conn:
            # Use IMMEDIATE to acquire lock early
            conn.execute("BEGIN IMMEDIATE")

            cursor = conn.execute("SELECT ...")
            if cursor.fetchone() is None:
                return None

            conn.execute("UPDATE ...")
            # Transaction ends quickly
            break
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower() and attempt < max_retries - 1:
            time.sleep(0.01 * (attempt + 1))  # Exponential backoff
            continue
        raise
```

### Medium-term Fix: Use IMMEDIATE Isolation

Change to IMMEDIATE transaction isolation to acquire locks upfront:

```python
@dataclass
class DatabaseConfig:
    isolation_level: Optional[str] = "IMMEDIATE"  # Acquire locks immediately
```

This prevents the "upgrade" scenario that causes conflicts.

### Long-term Solution: Consider a Different Persistence Layer

For high-concurrency scenarios, consider:
1. **PostgreSQL** with proper MVCC (Multi-Version Concurrency Control)
2. **Redis** for distributed locking with short TTLs
3. **SQLite with connection pooling** and connection limits
4. **Application-level locking** with threading primitives

---

## Files Involved

### Database Configuration
- **File:** `src/actifix/persistence/database.py`
- **Lines:** 171-179 (DatabaseConfig class)
- **Lines:** 322-338 (transaction() context manager)
- **Lines:** 217-253 (_get_connection() method)

### Ticket Locking
- **File:** `src/actifix/persistence/ticket_repo.py`
- **Lines:** 309-372 (acquire_lock() method)
- **Lines:** 374-394 (release_lock() method)
- **Lines:** 472-568 (get_and_lock_next_ticket() method)

### Test Files
- **File:** `test_threading_barrier_debug.py` - Reproduces the issue
- **File:** `test_threading_barrier_diagnostic.py` - Detailed diagnostics
- **File:** `test/test_ticket_repo.py` - Existing unit tests

---

## Test Reproducibility

### To Reproduce the Issue

```bash
python3 test_threading_barrier_debug.py
```

Expected output:
```
ANALYSIS: 3/3 threads completed, 2/3 locks acquired
FAILURE: Not all threads completed or acquired locks!
```

### To Run Diagnostics

```bash
python3 test_threading_barrier_diagnostic.py
```

This shows exactly where the "database is locked" errors occur.

---

## Next Steps

1. **Verify the issue isn't masked:** Run the existing test suite
   ```bash
   pytest test/test_ticket_repo.py -v
   ```

2. **Understand test timing:** The issue may not appear under low load
   - Existing tests might have longer delays between operations
   - Or use `get_and_lock_next_ticket()` which has different behavior

3. **Implement the short-term fix:** Add retry logic with exponential backoff

4. **Monitor production:** Check for "database is locked" errors in real usage

5. **Plan migration:** If high concurrency is critical, plan migration to a better persistence layer

---

## Conclusion

The threading issue is caused by SQLite's DEFERRED transaction isolation level combined with concurrent UPDATE operations on the same database. When multiple threads try to modify tickets simultaneously, they contend for the database-level write lock, causing subsequent transactions to fail with "database is locked" errors.

This is not a bug in the connection pool or thread-safety mechanism—those work correctly. Rather, it's a fundamental limitation of SQLite's locking model when used for high-concurrency scenarios with many simultaneous writers.

The recommended solution is to reduce transaction scope, use IMMEDIATE isolation to acquire locks upfront, or migrate to a persistence layer better suited for concurrent write operations.
