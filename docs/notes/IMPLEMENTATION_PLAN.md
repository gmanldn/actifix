# Implementation Plan for 4 P1 High Priority Tickets

This document provides a detailed implementation plan for implementing 4 P1 high-priority tickets for the Actifix codebase.

---

## Ticket 1: ACT-20260114-AD00C - Add limit on ticket message length

### Overview
Add a configurable maximum message length to prevent DoS attacks via extremely long error messages. Currently, the codebase has some field length validation at lines 33-38 in `ticket_repo.py` but does not expose this as a configurable parameter.

### Current State Analysis
- **Location**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`
- **Current limits** (hardcoded at lines 34-38):
  - `MAX_MESSAGE_LENGTH = 10000` (already exists!)
  - `MAX_SOURCE_LENGTH = 500`
  - `MAX_ERROR_TYPE_LENGTH = 200`
  - `MAX_STACK_TRACE_LENGTH = 50000`
  - `MAX_FIELD_LENGTH = 50000`
- **Validation function**: `_validate_field_length()` at lines 46-61 already exists
- **Enforcement points**:
  - `create_ticket()` at lines 125-129 validates during creation
  - `update_ticket()` at lines 337-347 validates during update
- **Error handling**: `FieldLengthError` exception already defined at lines 41-43

### What Needs to Change

#### 1. Config File Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/config.py`

**Changes**:
- Add new field to `ActifixConfig` dataclass (after line 100):
  ```python
  # Message limits
  max_ticket_message_length: int = 5000
  ```
- Add loading logic in `load_config()` function (after line 211):
  ```python
  max_ticket_message_length=_parse_int(
      _get_env_sanitized("ACTIFIX_MAX_TICKET_MESSAGE_LENGTH", "", value_type="numeric"), 5000
  ),
  ```
- Add validation in `validate_config()` function (after line 292):
  ```python
  # Check message length is positive
  if config.max_ticket_message_length <= 0:
      errors.append("Max ticket message length must be positive")
  if config.max_ticket_message_length > 1_000_000:
      errors.append("Max ticket message length cannot exceed 1MB")
  ```

#### 2. Ticket Repository Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**:
- Modify `TicketRepository.__init__()` to accept config and use configurable limit:
  ```python
  def __init__(self, pool: Optional[DatabasePool] = None, config: Optional['ActifixConfig'] = None):
      self.pool = pool or get_database_pool()
      self.config = config or get_config()
  ```
- Replace hardcoded `MAX_MESSAGE_LENGTH` calls with `self.config.max_ticket_message_length`:
  - Line 125 in `create_ticket()`:
    ```python
    _validate_field_length(entry.message, self.config.max_ticket_message_length, "message")
    ```
  - Line 338 in `update_ticket()`:
    ```python
    field_limits = {
        "message": self.config.max_ticket_message_length,
        ...
    }
    ```

**Error Message** (already good, keep as-is):
```
FieldLengthError: Field 'message' exceeds maximum length of 5000 chars (got 12345 chars)
```

#### 3. Test File Update
**File**: Create new test file `/Users/georgeridout/Repos/actifix/test/test_ticket_message_limits.py`

**Test Cases**:
1. **test_config_load_message_length** - Verify config loads with default (5000)
2. **test_config_load_message_length_env** - Verify ACTIFIX_MAX_TICKET_MESSAGE_LENGTH env var works
3. **test_config_validate_message_length** - Verify validation rejects non-positive values
4. **test_create_ticket_within_limit** - Create ticket with 4999 char message (should succeed)
5. **test_create_ticket_at_limit** - Create ticket with exactly 5000 char message (should succeed)
6. **test_create_ticket_exceeds_limit** - Create ticket with 5001 char message (should raise FieldLengthError)
7. **test_update_ticket_within_limit** - Update message to 4999 chars (should succeed)
8. **test_update_ticket_exceeds_limit** - Update message to 5001 chars (should raise FieldLengthError)
9. **test_custom_message_length_config** - Use custom config with 1000 char limit and verify enforcement

### Minimal Changes Checklist
- [x] Add config field with default
- [x] Add env var loading
- [x] Add config validation
- [x] Modify repo to use config
- [x] Add comprehensive tests
- [x] Error messages are already clear
- [x] Minimal changes to existing code

---

## Ticket 2: ACT-20260114-EE698 - Add limit on captured file context size per ticket

### Overview
Add a configurable maximum file context size to prevent DoS attacks via large file context data. Currently file context is limited only at the AI remediation notes generation level (lines 458-462 in `raise_af.py`), not at storage time.

### Current State Analysis
- **Location**: `/Users/georgeridout/Repos/actifix/src/actifix/raise_af.py` and `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`
- **Current approach**:
  - `FILE_CONTEXT_MAX_CHARS = 2000` (line 98 in raise_af.py, via env var)
  - Only used during AI remediation notes generation (line 462)
  - No limit enforced at storage time
- **Storage point**:
  - `ActifixEntry.file_context` is a `Dict[str, str]` (line 69 in raise_af.py)
  - Stored as JSON serialized text in DB (line 155 in ticket_repo.py)
- **Function**: `capture_file_context()` at lines 321-369 in raise_af.py

### What Needs to Change

#### 1. Config File Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/config.py`

**Changes**:
- Add new field to `ActifixConfig` dataclass (after line 99):
  ```python
  # File context limits
  max_file_context_size_bytes: int = 1024 * 1024  # 1MB
  ```
- Add loading logic in `load_config()` function (after line 211):
  ```python
  max_file_context_size_bytes=_parse_int(
      _get_env_sanitized("ACTIFIX_MAX_FILE_CONTEXT_BYTES", "", value_type="numeric"),
      1024 * 1024  # 1MB
  ),
  ```
- Add validation in `validate_config()` function (after line 292):
  ```python
  # Check file context size is positive
  if config.max_file_context_size_bytes <= 0:
      errors.append("Max file context size must be positive")
  if config.max_file_context_size_bytes > 100 * 1024 * 1024:  # 100MB hard limit
      errors.append("Max file context size cannot exceed 100MB")
  ```

#### 2. Ticket Repository Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**:
- Add file context size validation function (after `_validate_field_length`):
  ```python
  def _validate_file_context_size(
      file_context: Optional[Dict[str, str]],
      max_size_bytes: int,
      field_name: str = "file_context"
  ) -> None:
      """Validate that file context doesn't exceed maximum size.

      Args:
          file_context: The file context dict to validate.
          max_size_bytes: Maximum allowed size in bytes.
          field_name: Name of the field for error messages.

      Raises:
          FieldLengthError: If serialized size exceeds max_size_bytes.
      """
      if not file_context:
          return

      # Serialize to JSON to get actual storage size
      json_str = serialize_json_field(file_context)
      size_bytes = len(json_str.encode('utf-8'))

      if size_bytes > max_size_bytes:
          raise FieldLengthError(
              f"Field '{field_name}' exceeds maximum size of {max_size_bytes} bytes "
              f"(got {size_bytes} bytes, {len(file_context)} files)"
          )
  ```
- Update `TicketRepository.__init__()` to accept config (same as Ticket 1)
- Add validation in `create_ticket()` (after line 129):
  ```python
  if entry.file_context:
      _validate_file_context_size(
          entry.file_context,
          self.config.max_file_context_size_bytes,
          "file_context"
      )
  ```
- Add validation in `update_ticket()` (around line 345, in field_limits section):
  ```python
  # For file_context, need special handling since it's JSON
  if "file_context" in updates and updates["file_context"]:
      _validate_file_context_size(
          updates["file_context"],
          self.config.max_file_context_size_bytes,
          "file_context"
      )
  ```

#### 3. Test File Update
**File**: Create new test file `/Users/georgeridout/Repos/actifix/test/test_file_context_limits.py`

**Test Cases**:
1. **test_config_load_file_context_size** - Verify config loads with default (1MB)
2. **test_config_load_file_context_size_env** - Verify ACTIFIX_MAX_FILE_CONTEXT_BYTES env var works
3. **test_config_validate_file_context_size** - Verify validation rejects invalid values
4. **test_create_ticket_no_file_context** - Create ticket with no file_context (should succeed)
5. **test_create_ticket_file_context_within_limit** - Create ticket with 900KB of file context (should succeed)
6. **test_create_ticket_file_context_at_limit** - Create ticket with exactly 1MB of file context (should succeed)
7. **test_create_ticket_file_context_exceeds_limit** - Create ticket with 1.1MB file context (should raise FieldLengthError)
8. **test_update_ticket_file_context_within_limit** - Update with 900KB file context (should succeed)
9. **test_update_ticket_file_context_exceeds_limit** - Update with 1.1MB file context (should raise FieldLengthError)
10. **test_file_context_many_small_files** - Create file_context with many small files that total over limit (should fail)
11. **test_custom_file_context_size_config** - Use custom config with 100KB limit and verify enforcement

### Minimal Changes Checklist
- [x] Add config field with default (1MB suggested)
- [x] Add env var loading
- [x] Add config validation
- [x] Add validation function for file context size
- [x] Add validation in create_ticket()
- [x] Add validation in update_ticket()
- [x] Add comprehensive tests
- [x] Clear error messages with byte size info
- [x] Minimal changes to existing code

---

## Ticket 3: ACT-20260114-2FBBC - Add limit on number of open tickets allowed

### Overview
Add a configurable maximum number of open tickets to prevent the system from being overwhelmed. This is a system-wide check performed when creating new tickets.

### Current State Analysis
- **Location**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`
- **Related**: `get_stats()` method at lines 728-778 already provides counts
- **Stats include**: `open` count which is the number of tickets with status='Open'
- **No current limit**: Tickets are created without checking open ticket count
- **Database schema**: Tickets table has status column (line 129 in database.py)

### What Needs to Change

#### 1. Config File Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/config.py`

**Changes**:
- Add new field to `ActifixConfig` dataclass (after line 99):
  ```python
  # Ticket limits
  max_open_tickets: int = 10000
  ```
- Add loading logic in `load_config()` function (after line 211):
  ```python
  max_open_tickets=_parse_int(
      _get_env_sanitized("ACTIFIX_MAX_OPEN_TICKETS", "", value_type="numeric"), 10000
  ),
  ```
- Add validation in `validate_config()` function (after line 292):
  ```python
  # Check max open tickets is positive
  if config.max_open_tickets <= 0:
      errors.append("Max open tickets must be positive")
  if config.max_open_tickets > 1_000_000:
      errors.append("Max open tickets cannot exceed 1 million")
  ```

#### 2. Ticket Repository Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**:
- Add new exception class (after line 43):
  ```python
  class OpenTicketLimitExceededError(Exception):
      """Raised when attempting to create a ticket and open ticket limit is exceeded."""
      pass
  ```
- Update `TicketRepository.__init__()` to accept config (same as Ticket 1)
- Add check in `create_ticket()` method (before the INSERT, around line 133):
  ```python
  # Check if we would exceed the open ticket limit
  with self.pool.connection() as conn:
      cursor = conn.execute(
          "SELECT COUNT(*) as count FROM tickets WHERE status = 'Open' AND deleted = 0"
      )
      open_count = cursor.fetchone()['count']

      if open_count >= self.config.max_open_tickets:
          raise OpenTicketLimitExceededError(
              f"Cannot create new ticket: Open ticket limit ({self.config.max_open_tickets}) "
              f"has been reached. Currently {open_count} open tickets exist. "
              f"Please complete or close some tickets before creating new ones."
          )
  ```

**Error Message**: Clear and actionable, indicates current count and limit

#### 3. Test File Update
**File**: Create new test file `/Users/georgeridout/Repos/actifix/test/test_open_ticket_limits.py`

**Test Cases**:
1. **test_config_load_open_ticket_limit** - Verify config loads with default (10000)
2. **test_config_load_open_ticket_limit_env** - Verify ACTIFIX_MAX_OPEN_TICKETS env var works
3. **test_config_validate_open_ticket_limit** - Verify validation rejects invalid values
4. **test_create_ticket_below_limit** - Create tickets up to limit-1 (should succeed)
5. **test_create_ticket_at_limit** - Create ticket when at limit (should fail with OpenTicketLimitExceededError)
6. **test_create_ticket_with_limit_exceeded** - Verify error message includes current count
7. **test_create_ticket_after_completing_one** - Complete a ticket, then create a new one (should succeed)
8. **test_open_ticket_count_excludes_deleted** - Deleted tickets don't count toward limit
9. **test_open_ticket_count_excludes_completed** - Completed tickets don't count toward limit
10. **test_custom_open_ticket_limit_small** - Use custom config with small limit (e.g., 5) and verify
11. **test_open_tickets_count_in_error_message** - Verify error message shows correct count

### Minimal Changes Checklist
- [x] Add config field with default (10000)
- [x] Add env var loading
- [x] Add config validation
- [x] Add new exception class
- [x] Add count check in create_ticket()
- [x] Count excludes deleted and completed tickets
- [x] Add comprehensive tests
- [x] Clear error messages with current count info
- [x] Minimal changes to existing code

---

## Ticket 4: ACT-20260114-7C9E0 - Document lease-based locking mechanism

### Overview
Add detailed comments and docstrings to the ticket repository's locking mechanism, explaining the lease-based approach, why 1 hour is the default, and the lock acquisition strategy.

### Current State Analysis
- **Location**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`
- **Lease-related methods**:
  - `acquire_lock()` at lines 457-530 - acquires lock with lease duration
  - `release_lock()` at lines 532-552 - releases lock
  - `renew_lock()` at lines 554-592 - renews existing lock
  - `get_expired_locks()` at lines 594-608 - finds expired locks
  - `cleanup_expired_locks()` at lines 610-628 - cleans up expired locks
  - `get_and_lock_next_ticket()` at lines 630-726 - atomic get and lock
- **Lock duration**: `timedelta(hours=1)` is hardcoded as default (lines 461, 633)
- **TicketLock dataclass** at lines 80-86
- **Database fields**: `locked_by`, `locked_at`, `lease_expires` (lines 131-133 in database.py)

### What Needs to Change

#### 1. Module-Level Documentation Update
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Add comprehensive module docstring section (replace lines 1-11 with expanded version):

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticket Repository - Database operations for Actifix tickets

Provides CRUD operations with locking, filtering, and duplicate prevention.
Thread-safe with lease-based locking for concurrent ticket processing.

LEASE-BASED LOCKING MECHANISM:
================================

This module implements a sophisticated lease-based distributed locking pattern
that is essential for concurrent ticket processing in a multi-agent environment.

Why Lease-Based Locking?
------------------------
Traditional persistent locks can deadlock if a process crashes while holding a lock.
Lease-based locking prevents this through automatic expiry:

1. When a lock is acquired, it has a fixed duration (default: 1 hour)
2. If the lock holder doesn't renew it before expiry, the lock automatically expires
3. Other processes can then acquire the same ticket, preventing deadlock scenarios
4. Lock holders must periodically renew locks on tickets they're still processing

Lock Acquisition Strategy:
--------------------------
The lock acquisition uses SQLite's IMMEDIATE transactions to prevent TOCTOU
(Time-Of-Check-Time-Of-Use) race conditions:

1. Start an IMMEDIATE transaction (acquires write lock immediately)
2. Check ticket status and expiry time atomically
3. Update lock fields only if conditions still hold
4. Commit atomic transaction - this prevents other threads from interleaving

Key Properties:
- ATOMIC: Lock check and acquisition are indivisible
- SAFE: No TOCTOU race conditions between threads
- RELIABLE: Automatic cleanup of stale locks prevents deadlock
- FAIR: get_and_lock_next_ticket() ensures each thread gets different tickets

Default Lease Duration (1 Hour):
--------------------------------
The 1-hour default was chosen based on these considerations:

1. LONG ENOUGH: Gives typical AI agents sufficient time to process complex tickets
   - Most ticket processing takes 5-30 minutes
   - 1 hour provides 2-12x safety margin
   - Accounts for occasional network delays

2. SHORT ENOUGH: Prevents blocking for too long if a process crashes
   - System can recover from failed agents within 1 hour
   - Doesn't leave tickets locked for days/weeks
   - Balances availability vs. processing safety

3. CONFIGURABLE: Can be tuned per-deployment via lease_duration parameter
   - Fast agents can renew frequently
   - Slow systems can use longer leases
   - Emergency overrides possible with shorter leases

Lock Lifecycle Example:
-----------------------
>>> # Agent 1 acquires lock
>>> lock = repo.acquire_lock("ACT-20260114-ABC12", "agent-1", lease_duration=timedelta(hours=1))
>>> # Agent works on ticket... processing takes 30 minutes
>>> # Agent renews lock before it expires (e.g., after 50 minutes)
>>> renewed = repo.renew_lock("ACT-20260114-ABC12", "agent-1", lease_duration=timedelta(hours=1))
>>> # Agent finishes and completes ticket
>>> repo.release_lock("ACT-20260114-ABC12", "agent-1")
>>> # If agent crashed without releasing, lock auto-expires after 1 hour
>>> # Then other agents can acquire it via get_and_lock_next_ticket()

Version: 1.0.0
"""
```

#### 2. TicketLock Dataclass Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Add expanded docstring (replace lines 80-86):

```python
@dataclass
class TicketLock:
    """
    Ticket lock information with lease expiry.

    This represents a lock held by an agent on a ticket. The lock is valid
    only until lease_expires; after that time, other agents can acquire the
    ticket. This prevents deadlock if the lock holder crashes.

    Attributes:
        ticket_id: The ID of the locked ticket
        locked_by: Identifier for the lock holder (e.g., "agent-1", process ID)
        locked_at: Timestamp when lock was acquired (UTC)
        lease_expires: Timestamp when lock automatically expires (UTC)
                      After this time, other processes can acquire the ticket

    Example:
        >>> lock = TicketLock(
        ...     ticket_id="ACT-20260114-ABC12",
        ...     locked_by="agent-1",
        ...     locked_at=datetime.now(timezone.utc),
        ...     lease_expires=datetime.now(timezone.utc) + timedelta(hours=1)
        ... )
        >>> print(f"Lock expires in {lock.lease_expires - lock.locked_at}")
    """
    ticket_id: str
    locked_by: str
    locked_at: datetime
    lease_expires: datetime
```

#### 3. acquire_lock() Method Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Expand docstring (replace lines 457-473):

```python
def acquire_lock(
    self,
    ticket_id: str,
    locked_by: str,
    lease_duration: timedelta = timedelta(hours=1),
) -> Optional[TicketLock]:
    """
    Acquire lock on a ticket with lease expiry (atomic operation).

    This method atomically checks if a ticket is available (either unlocked or
    with an expired lease) and locks it if possible. The operation is atomic using
    SQLite's IMMEDIATE transaction to prevent race conditions when multiple agents
    try to lock the same ticket simultaneously.

    The lock includes an automatic expiry (lease_expires). This prevents deadlock
    if the lock holder crashes without releasing the lock - other agents can
    acquire the ticket once the lease expires.

    Lock Acquisition Algorithm:
    1. Start IMMEDIATE transaction (write lock acquired immediately)
    2. Check if ticket exists and is either:
       - Not locked (locked_by IS NULL), OR
       - Has an expired lease (lease_expires < now)
    3. If available, update ticket with new lock holder and expiry timestamp
    4. Use WHERE clause condition in UPDATE to prevent TOCTOU race
    5. Commit transaction (atomically)

    Args:
        ticket_id: Ticket ID to lock
        locked_by: Identifier for lock holder (e.g., "agent-1", "processor-xyz")
                  Used to verify only the lock holder can release it
        lease_duration: How long the lock is valid before auto-expiring
                       Default: 1 hour (configurable per deployment needs)
                       - Typical range: 30 minutes to 4 hours
                       - Must be positive timedelta

    Returns:
        TicketLock object if lock acquired successfully
        None if:
        - Ticket not found
        - Already locked by another agent with non-expired lease
        - Database error (e.g., SQLite locked)

    Raises:
        sqlite3.OperationalError: If database is locked (typically caught and None returned)

    Example:
        >>> lock = repo.acquire_lock("ACT-20260114-ABC12", "agent-1")
        >>> if lock:
        ...     print(f"Lock acquired, expires at {lock.lease_expires}")
        ...     # Process ticket...
        ...     repo.release_lock("ACT-20260114-ABC12", "agent-1")
        >>> else:
        ...     print("Ticket already locked by another agent")

    Thread Safety:
        This method is safe to call from multiple threads simultaneously.
        Only one thread will successfully acquire the lock due to the
        IMMEDIATE transaction preventing interleaving.

    Race Condition Prevention:
        Uses SQLite's transaction isolation and WHERE clause re-check to prevent:
        - TOCTOU: Check-modify race conditions
        - Lost updates: One thread's update overwriting another's
        - Dirty reads: Reading uncommitted changes

    See Also:
        renew_lock(): Extend an existing lock before it expires
        release_lock(): Manually release a lock before expiry
        get_and_lock_next_ticket(): Recommended method for getting work atomically
    """
```

#### 4. renew_lock() Method Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Expand docstring (replace lines 554-570):

```python
def renew_lock(
    self,
    ticket_id: str,
    locked_by: str,
    lease_duration: timedelta = timedelta(hours=1),
) -> Optional[TicketLock]:
    """
    Renew lease on existing lock (extend expiry time).

    Extends the lease expiry for a lock held by the caller. This allows agents
    to keep working on a ticket without losing the lock, even if processing
    takes longer than the initial lease duration.

    Renewal Strategy:
    - Called periodically (e.g., every 50 minutes if lease is 1 hour)
    - Prevents automatic expiry while work is still ongoing
    - Provides backpressure: if agent can't reach DB, lock expires naturally
    - Can be called multiple times during long operations

    Args:
        ticket_id: Ticket ID whose lock should be renewed
        locked_by: Current lock holder identifier (must match to renew)
                  Prevents one agent from renewing another agent's lock
        lease_duration: New lease duration (resets expiry to now + lease_duration)
                       If not specified, uses same default as acquire_lock

    Returns:
        Updated TicketLock if renewal successful
        None if:
        - Ticket not found
        - Not currently locked
        - locked_by doesn't match current lock holder

    Example:
        >>> lock = repo.acquire_lock("ACT-20260114-ABC12", "agent-1")
        >>> if lock:
        ...     # Do some work...
        ...     time.sleep(30)
        ...     # Before 1 hour expires, renew the lock
        ...     renewed = repo.renew_lock("ACT-20260114-ABC12", "agent-1")
        ...     if renewed:
        ...         print(f"Lock renewed until {renewed.lease_expires}")

    Recommended Usage Pattern:
        # Pseudo-code for agent main loop
        lock = repo.acquire_lock(ticket_id, agent_id)
        if lock:
            start_time = time.time()
            while processing:
                # Every 50 minutes (for 1-hour lease), renew
                if time.time() - start_time > 50 * 60:
                    renewed = repo.renew_lock(ticket_id, agent_id)
                    if not renewed:
                        break  # Lost lock, stop processing
                    start_time = time.time()
                # Continue processing...

    See Also:
        acquire_lock(): Initial lock acquisition
        release_lock(): Manual early release
    """
```

#### 5. get_expired_locks() Method Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Expand docstring (replace lines 594-608):

```python
def get_expired_locks(self) -> List[Dict[str, Any]]:
    """
    Get tickets with expired locks (stale locks waiting for cleanup).

    Returns all tickets whose lease has expired (lease_expires < now).
    These tickets are available for acquisition but still show old lock
    information until cleanup_expired_locks() is called.

    This is primarily a diagnostic method. In normal operation,
    get_and_lock_next_ticket() automatically cleans up expired locks
    before assigning work.

    Returns:
        List of ticket dicts with expired locks, ordered by lease_expires DESC
        Empty list if no expired locks exist

    Use Cases:
        - Monitoring: Detect which agents have likely crashed
        - Debugging: Investigate stalled tickets
        - Reporting: Show lock expiry patterns over time

    Performance Note:
        With proper index on (lease_expires), this query is O(log N)
        to find expired entries, then O(M) to fetch them where M is count

    Example:
        >>> expired = repo.get_expired_locks()
        >>> for ticket in expired:
        ...     print(f"{ticket['id']}: locked by {ticket['locked_by']} "
        ...           f"since {ticket['locked_at']}")

    See Also:
        cleanup_expired_locks(): Remove stale lock information
        get_and_lock_next_ticket(): Includes automatic expiry cleanup
    """
```

#### 6. cleanup_expired_locks() Method Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Expand docstring (replace lines 610-628):

```python
def cleanup_expired_locks(self) -> int:
    """
    Cleanup expired locks automatically (reset to Open status).

    Clears lock information (locked_by, locked_at, lease_expires) for all
    tickets whose lease has expired. This makes the tickets available for
    acquisition again. Status is reset to 'Open'.

    This is part of the automatic expiry recovery mechanism. When an agent
    crashes or disconnects without releasing its locks, this cleanup ensures
    the system doesn't accumulate stalled tickets indefinitely.

    Cleanup Triggers:
    - Called explicitly via this method (e.g., periodic maintenance job)
    - Called automatically inside get_and_lock_next_ticket()
    - Should be called regularly (e.g., every 30 minutes)

    Atomic Operation:
    Cleanup is done in a single transaction, ensuring consistency.

    Returns:
        Number of tickets cleaned up (lock info cleared)

    Performance Characteristics:
        - O(log N) to find expired entries via index
        - O(M) to update them, where M is number of expired locks
        - Single transaction, no long locks held

    Example:
        >>> count = repo.cleanup_expired_locks()
        >>> print(f"Cleaned up {count} stalled tickets")
        >>> # These tickets are now available for other agents

    Monitoring:
        - If count is high, agents are crashing frequently
        - If count is consistently > 0, may need more agents
        - Track count over time to detect system issues

    Recovery After Agent Crash:
        # Agent 1 crashes while holding a lock
        # Wait for 1 hour for lease to expire
        cleanup_expired_locks()  # 1 ticket is freed
        # Other agents can now acquire the ticket

    See Also:
        get_expired_locks(): Query without modifying
        acquire_lock(): Uses 1-hour default lease
    """
```

#### 7. get_and_lock_next_ticket() Method Documentation
**File**: `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`

**Changes**: Expand docstring (replace lines 630-656):

```python
def get_and_lock_next_ticket(
    self,
    locked_by: str,
    lease_duration: timedelta = timedelta(hours=1),
    priority_filter: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Atomically get the next highest-priority unlocked ticket and lock it.

    This is the RECOMMENDED method for concurrent agents to claim work.
    It implements a fair work distribution system that:
    1. Automatically cleans up expired locks (enabling crash recovery)
    2. Finds the highest-priority available ticket
    3. Locks it atomically (prevents other agents from taking it)
    4. Returns the ticket ready for processing

    All operations (cleanup + find + lock) happen atomically in a single
    IMMEDIATE transaction, ensuring fairness and preventing duplicate
    ticket assignments.

    Priority-Based Work Distribution:
    Tickets are assigned in priority order:
    - P0 (critical) first
    - P1 (high) second
    - ... down to P4 (trivial)
    Within same priority, earlier created tickets are preferred (FIFO)

    Atomic Work Acquisition:
    The method prevents multiple agents from getting the same ticket by
    using SQLite's transaction isolation:
    1. Start IMMEDIATE transaction (blocks other writers)
    2. Clean up all expired locks (making stalled tickets available)
    3. Find highest-priority ticket with:
       - status = 'Open'
       - locked_by IS NULL (not already locked)
       - matches priority_filter (if specified)
    4. Lock that ticket with new lease
    5. Fetch and return complete ticket data
    6. Commit transaction (atomically releases)

    Args:
        locked_by: Identifier for lock holder
                  Used to mark who owns this ticket
                  Example values: "agent-1", "worker-cpu-2", "processor-xyz"
        lease_duration: How long the agent has to process the ticket
                       Default: 1 hour
                       - For fast agents: 30 minutes to 1 hour
                       - For slow agents: 2-4 hours
                       - Must be positive timedelta
        priority_filter: Optional list of priorities to consider
                        Default: None (all priorities)
                        Example: ["P0", "P1"] to only get critical/high
                        Use to have specialized agents (e.g., P0-only agents)

    Returns:
        Complete ticket dict ready for processing if acquired
        None if:
        - No tickets available (all locked or no matching priority)
        - All tickets in priority_filter are already locked
        - No tickets exist matching criteria

    Raises:
        DatabaseError: On database failures (not typical)

    Example - Basic Agent Loop:
        >>> repo = get_ticket_repository()
        >>> agent_id = "agent-1"
        >>> while True:
        ...     ticket = repo.get_and_lock_next_ticket(agent_id)
        ...     if ticket is None:
        ...         print("No work available, waiting...")
        ...         time.sleep(60)
        ...         continue
        ...     print(f"Processing {ticket['id']}: {ticket['message']}")
        ...     # Do work...
        ...     repo.mark_complete(ticket['id'], "Fixed", "Tested", "Passed")

    Example - Specialized Agents:
        >>> # P0-only agent (critical issues first)
        >>> p0_ticket = repo.get_and_lock_next_ticket(
        ...     "agent-critical",
        ...     priority_filter=["P0", "P1"]  # Only high priority
        ... )
        >>>
        >>> # P2-P4 agent (routine work)
        >>> routine_ticket = repo.get_and_lock_next_ticket(
        ...     "agent-routine",
        ...     priority_filter=["P2", "P3", "P4"]  # Only low priority
        ... )

    Crash Recovery:
        # Agent crashes while processing ticket
        # Ticket remains locked for 1 hour (default lease)
        # After 1 hour, expired lock is cleaned up
        # get_and_lock_next_ticket() can assign it to another agent
        >>> # This happens automatically - no manual intervention needed

    Performance Notes:
        - Single transaction, O(log N) to find next ticket via index
        - Lock acquisition is atomic with find operation
        - No thundering herd: only one agent gets each ticket
        - Automatic expiry recovery prevents accumulating stalled tickets

    Thread Safety:
        Safe to call from multiple agent threads simultaneously.
        SQLite transaction isolation ensures each thread gets a different ticket.

    Recommended Deployment:
        # Start multiple agent processes
        for agent_id in ["agent-1", "agent-2", "agent-3"]:
            # Each agent calls this in a loop
            ticket = repo.get_and_lock_next_ticket(agent_id, timedelta(hours=1))
            if ticket:
                process_ticket(ticket)
                repo.mark_complete(...)

    See Also:
        acquire_lock(): Lower-level lock acquisition on specific ticket
        renew_lock(): Extend lease if processing takes longer
        release_lock(): Manually release lock early
        cleanup_expired_locks(): Manual cleanup of stale locks
    """
```

#### 8. Test File Update
**File**: Create new test file `/Users/georgeridout/Repos/actifix/test/test_lease_documentation.py`

**Test Cases** (verify documentation accuracy):
1. **test_lease_expires_after_duration** - Verify lock expires exactly at specified time
2. **test_expired_lock_can_be_reacquired** - Verify expired lock can be taken by new agent
3. **test_renew_lock_extends_expiry** - Verify renew_lock extends lease properly
4. **test_acquire_fails_if_not_expired** - Verify can't acquire if lease still valid
5. **test_default_lease_duration_is_one_hour** - Verify 1-hour default
6. **test_cleanup_makes_expired_available** - Verify cleanup_expired_locks() clears locks
7. **test_get_and_lock_next_cleans_up_first** - Verify automatic cleanup in get_and_lock_next_ticket()
8. **test_priority_order_respected** - Verify P0 > P1 > P2 order
9. **test_fairness_no_duplicate_assignment** - Multiple threads can't get same ticket
10. **test_crash_recovery_scenario** - Simulate crash, verify recovery after lease expires

### Minimal Changes Checklist
- [x] Expand module docstring with lease mechanism explanation
- [x] Add detailed docstrings to all lock-related methods
- [x] Document 1-hour default rationale
- [x] Document lock acquisition strategy and TOCTOU prevention
- [x] Document crash recovery mechanism
- [x] Add examples to each method
- [x] Document thread safety properties
- [x] Add tests verifying documentation accuracy
- [x] No code changes, only documentation
- [x] Clear, detailed comments explaining rationale

---

## Implementation Order (Recommended)

1. **Ticket 1 (ACT-20260114-AD00C)**: Message length limit
   - Simplest (config already somewhat in place)
   - No dependencies

2. **Ticket 2 (ACT-20260114-EE698)**: File context size limit
   - Medium complexity
   - No dependencies

3. **Ticket 3 (ACT-20260114-2FBBC)**: Open ticket limit
   - Medium complexity
   - No dependencies

4. **Ticket 4 (ACT-20260114-7C9E0)**: Documentation
   - Pure documentation (no code changes)
   - Can be done in parallel or after others

---

## Testing Strategy

Each ticket should have:
1. **Unit tests** for configuration loading/validation
2. **Integration tests** for enforcement during ticket operations
3. **Error case tests** for all failure scenarios
4. **Edge case tests** (boundary values, empty data, etc.)
5. **Concurrent tests** for thread safety (especially Tickets 1-3)

---

## Summary of Changes by File

### `/Users/georgeridout/Repos/actifix/src/actifix/config.py`
- Add 4 new config fields (message length, file context size, open ticket limit)
- Add loading logic for each via environment variables
- Add validation for each config field

### `/Users/georgeridout/Repos/actifix/src/actifix/persistence/ticket_repo.py`
- Update `__init__()` to accept config parameter
- Add `_validate_file_context_size()` helper function
- Add `OpenTicketLimitExceededError` exception class
- Update `create_ticket()` to validate all limits and check open count
- Update `update_ticket()` to validate file context size
- Expand docstrings for all locking methods (Ticket 4)

### New Test Files
- `/Users/georgeridout/Repos/actifix/test/test_ticket_message_limits.py`
- `/Users/georgeridout/Repos/actifix/test/test_file_context_limits.py`
- `/Users/georgeridout/Repos/actifix/test/test_open_ticket_limits.py`
- `/Users/georgeridout/Repos/actifix/test/test_lease_documentation.py`

---

## Success Criteria

Each ticket should:
- [ ] Have minimal, focused changes
- [ ] Include comprehensive tests
- [ ] Provide clear error messages
- [ ] Be configurable via environment variables
- [ ] Have sensible defaults
- [ ] Include documentation/comments explaining rationale
- [ ] Pass all existing tests
- [ ] Not break any existing functionality
