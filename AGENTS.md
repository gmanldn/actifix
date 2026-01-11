# Coding Agent Instructions

This file provides essential context and rules for all coding agents working with the Actifix codebase.

---

# PART 1: MANDATORY REQUIREMENTS

All Changes Must Start via Raise_AF
actifix.raise_af.record_error

## 1. Every Completed Task MUST Be Committed and Pushed

**CRITICAL: Always make a branch, do the work in the ticket, commit, merge to develop, then delete the branch at all times**

**CRITICAL: All work must be committed to the `develop` branch and pushed before a task is considered complete.**

```bash
# Standard commit workflow (REQUIRED after every task completion)
git status
git add -A
git commit -m "type(scope): description"
git push origin develop
```

**Commit message convention:**

- `feat(scope):` - New features
- `fix(scope):` - Bug fixes
- `refactor(scope):` - Code refactoring
- `test(scope):` - Test additions/changes
- `docs(scope):` - Documentation changes
- `chore(scope):` - Maintenance tasks
- `perf(scope):` - Performance improvements

## 2. Full Regression and Function Tests Required

**CRITICAL: Every task must include running and passing the full test suite.**

```bash
# REQUIRED before committing any changes
python test.py                    # Full test suite with architecture validation
python test.py --coverage         # Must maintain 95%+ coverage
```

**Test requirements:**

- All tests must pass (0 failures allowed)
- Coverage must remain at or above 95%
- No regressions in existing functionality
- New code must have comprehensive test coverage
- **EVERYTHING must be tested** - No exceptions

## 3. NO Implementation Plan Documents - Use TODO.md Only

**CRITICAL: NEVER create standalone planning documents.**

**FORBIDDEN files:**

- `IMPLEMENTATION_PLAN.md`
- `PLAN.md`
- `ROADMAP.md`
- `DESIGN.md`
- Any `*_PLAN.md` or `*_ROADMAP.md` files

## 4. Version Increment, Branch, Commit, and Push After EVERY Change

**CRITICAL: After EVERY commit, you MUST complete the full workflow:**

1. **Increment version** in pyproject.toml
2. **Create/use a feature branch** for the work
3. **Commit with a descriptive message** following conventions
4. **Push immediately** - no local-only commits

## 5. Instruction File Stewardship

**CRITICAL: `AGENTS.md` is the canonical instruction file and must be kept accurate.**

---

# PART 2: SYSTEM ARCHITECTURE OVERVIEW

## Core Architectural Philosophy

The Actifix system is built around **five non-negotiable quality principles**:

| Principle | Description | Enforcement |
|-----------|-------------|-------------|
| **Determinism** | No silent skips, no hidden state | Test validation, strict error handling |
| **Auditability** | Every action leaves a durable trail | Logging, tickets, correlation IDs |
| **Enforcement Over Convention** | Rules are executable, not advisory | Tests fail on violations |
| **Durability and Safety** | Crashes and restarts are first-class concerns | Atomic writes, recovery |
| **Continuity Over Time** | Decisions persist across sessions | ADRs, structured tickets |

## System Layers (Bottom to Top)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                            │
│  actifix-frontend/  │  src/actifix/api.py  │  src/actifix/main.py   │
├─────────────────────────────────────────────────────────────────────┤
│                        APPLICATION LAYER                             │
│  src/actifix/raise_af.py  │  src/actifix/do_af.py  │  health.py     │
├─────────────────────────────────────────────────────────────────────┤
│                        DOMAIN LAYER                                  │
│  src/actifix/quarantine.py  │  src/actifix/config.py                │
├─────────────────────────────────────────────────────────────────────┤
│                        INFRASTRUCTURE LAYER                          │
│  src/actifix/persistence/*  │  src/actifix/log_utils.py             │
├─────────────────────────────────────────────────────────────────────┤
│                        BOOTSTRAP LAYER                               │
│  src/actifix/bootstrap.py  │  src/actifix/state_paths.py            │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph (Allowed Dependencies)

```
bootstrap.py ─────────────────────────────────────────────────────────┐
    │                                                                  │
    ▼                                                                  │
state_paths.py ◄─────────────────────────────────────────────────────┤
    │                                                                  │
    ▼                                                                  │
config.py ◄──────────────────────────────────────────────────────────┤
    │                                                                  │
    ▼                                                                  │
log_utils.py ◄───────────────────────────────────────────────────────┤
    │                                                                  │
    ├──────────────────┬──────────────────┬──────────────────┐        │
    ▼                  ▼                  ▼                  ▼        │
persistence/       quarantine.py     raise_af.py        health.py    │
    │                  │                  │                  │        │
    │                  │                  ▼                  │        │
    │                  │              do_af.py ◄────────────┤        │
    │                  │                  │                  │        │
    └──────────────────┴──────────────────┴──────────────────┘        │
                                          │                           │
                                          ▼                           │
                                       api.py ◄──────────────────────┘
                                          │
                                          ▼
                                       main.py
```

**RULE: No upward dependencies. Lower layers MUST NOT import from higher layers.**

---

# PART 3: DETAILED MODULE INTERFACE SPECIFICATIONS

## 3.1 Bootstrap Layer

### `src/actifix/state_paths.py` - Path Management

**Purpose:** Centralized management of all filesystem paths used by the system.

**Primary Export:** `ActifixPaths` dataclass

```python
@dataclass
class ActifixPaths:
    project_root: Path      # Root of the project (where pyproject.toml lives)
    base_dir: Path          # Base directory for actifix data (actifix/)
    state_dir: Path         # State storage directory (.actifix/)
    logs_dir: Path          # Log files directory (logs/)
    list_file: Path         # ACTIFIX-LIST.md path
    recent_file: Path       # ACTIFIX.md path (last 20 errors)
    log_file: Path          # AFLog.txt path
    quarantine_dir: Path    # Quarantine directory
```

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `get_actifix_paths(project_root, base_dir, state_dir, logs_dir)` | Optional paths | `ActifixPaths` | Creates singleton | None |
| `ensure_actifix_dirs(paths)` | `ActifixPaths` | None | Creates directories | `PermissionError` |
| `init_actifix_files(paths)` | Optional `ActifixPaths` | `ActifixPaths` | Creates files if missing | `IOError` |
| `reset_actifix_paths()` | None | None | Clears singleton | None |
| `get_project_root()` | None | `Path` | None | `RuntimeError` if not init |
| `get_logs_dir()` | None | `Path` | None | `RuntimeError` if not init |

**Critical Rules:**
1. **ALWAYS** call `get_actifix_paths()` before accessing any path
2. **NEVER** construct paths manually - use `ActifixPaths` members
3. **NEVER** assume paths exist - call `ensure_actifix_dirs()` first
4. The singleton is **thread-safe** but **not process-safe**

**Expected Usage Pattern:**
```python
from actifix.state_paths import get_actifix_paths, ensure_actifix_dirs

paths = get_actifix_paths()  # Uses cached singleton
ensure_actifix_dirs(paths)   # Idempotent - safe to call multiple times

# Access paths via dataclass members
list_file = paths.list_file
log_dir = paths.logs_dir
```

### `src/actifix/bootstrap.py` - System Initialization

**Purpose:** Single canonical entrypoint for system initialization.

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `bootstrap(project_root)` | Optional `Path` | `ActifixPaths` | Full init, exception handler | `RuntimeError` on failure |
| `shutdown()` | None | None | Cleanup, unhook exceptions | None |
| `enable_actifix_capture()` | None | None | Enable error capture | None |
| `disable_actifix_capture()` | None | None | Disable error capture | None |
| `ActifixContext` | Optional `Path` | Context manager | Full lifecycle | Re-raises exceptions |

**Bootstrap Sequence (MUST be followed):**
```
1. resolve project root
2. initialize paths (state_paths.get_actifix_paths)
3. ensure directories exist (state_paths.ensure_actifix_dirs)
4. initialize files (state_paths.init_actifix_files)
5. install exception handler
6. return ActifixPaths
```

**Critical Rules:**
1. **ALWAYS** use `bootstrap()` or `ActifixContext` to start the system
2. **NEVER** call individual init functions directly from application code
3. **ALWAYS** call `shutdown()` or use context manager for cleanup
4. The exception handler captures **all uncaught exceptions** to tickets

**Expected Usage Pattern:**
```python
# Option 1: Context manager (preferred)
from actifix.bootstrap import ActifixContext

with ActifixContext() as paths:
    # System fully initialized
    # Exceptions auto-captured to tickets
    run_application()
# Automatic cleanup on exit

# Option 2: Manual control
from actifix.bootstrap import bootstrap, shutdown

paths = bootstrap()
try:
    run_application()
finally:
    shutdown()
```

### `src/actifix/config.py` - Configuration Management

**Purpose:** Centralized configuration with validation and environment support.

**Primary Export:** `ActifixConfig` dataclass

```python
@dataclass
class ActifixConfig:
    debug: bool                     # Enable debug mode
    log_level: str                  # Logging level (DEBUG, INFO, etc.)
    max_recent_errors: int          # Max errors in ACTIFIX.md
    sla_hours: Dict[str, int]       # SLA by priority {"P0": 1, "P1": 4, ...}
    api_host: str                   # API server host
    api_port: int                   # API server port
    enable_dock_icon: bool          # macOS dock icon
    correlation_id_prefix: str      # Prefix for correlation IDs
```

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `load_config(project_root, env_prefix)` | Optional params | `ActifixConfig` | Reads env vars | None (uses defaults) |
| `validate_config(config)` | `ActifixConfig` | `list[str]` | None | None |
| `get_config()` | None | `ActifixConfig` | None | None (returns default) |
| `set_config(config)` | `ActifixConfig` | None | Sets global | None |
| `reset_config()` | None | None | Clears global | None |

**Environment Variables (all optional):**
```
ACTIFIX_DEBUG=true|false
ACTIFIX_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
ACTIFIX_MAX_RECENT=20
ACTIFIX_API_HOST=0.0.0.0
ACTIFIX_API_PORT=5001
ACTIFIX_DOCK_ICON=true|false
```

**Critical Rules:**
1. **NEVER** access environment variables directly - use `load_config()`
2. **ALWAYS** validate config before using: `errors = validate_config(config)`
3. Config is **immutable** - create new instance for changes
4. Defaults are **safe** - system works without any env vars

---

## 3.2 Infrastructure Layer

### `src/actifix/log_utils.py` - Logging Utilities

**Purpose:** Atomic logging operations with durability guarantees.

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `atomic_write(path, content, encoding)` | Path, str, str | None | Atomic file write | `IOError` |
| `atomic_write_bytes(path, content)` | Path, bytes | None | Atomic file write | `IOError` |
| `append_with_guard(path, content, max_bytes, encoding)` | Path, str, int, str | bool | Append with size limit | `IOError` |
| `idempotent_append(path, content, guard_id, encoding)` | Path, str, str, str | bool | Append if guard missing | `IOError` |
| `log_event(path, event_type, data, timestamp)` | Path, str, dict, datetime | None | Structured logging | `IOError` |

**Atomicity Guarantee:**
```
atomic_write implementation:
1. Write to temporary file (same directory)
2. Flush and fsync
3. Atomic rename to target
4. If any step fails, no partial write occurs
```

**Critical Rules:**
1. **ALWAYS** use `atomic_write` for any file that could be read concurrently
2. **NEVER** use standard `open().write()` for state files
3. `idempotent_append` uses guard pattern - safe to retry on failure
4. `max_bytes` in `append_with_guard` is **enforced** - content truncated at line boundary

**Expected Usage Pattern:**
```python
from actifix.log_utils import atomic_write, idempotent_append

# Safe write (will not corrupt on crash)
atomic_write(path, "content")

# Idempotent append (safe to retry)
success = idempotent_append(
    path=log_file,
    content="new entry\n",
    guard_id="unique-entry-id"  # Won't append if this ID exists
)
```

### `src/actifix/persistence/` - Persistence Subsystem

The persistence layer provides **durable, atomic, recoverable storage**.

#### `persistence/storage.py` - Storage Backends

**Purpose:** Pluggable storage with consistent interface.

**Abstract Interface:** `StorageBackend`

```python
class StorageBackend(ABC):
    def read(self, key: str) -> str: ...
    def read_bytes(self, key: str) -> bytes: ...
    def write(self, key: str, content: str, encoding: str = "utf-8") -> None: ...
    def write_bytes(self, key: str, content: bytes) -> None: ...
    def exists(self, key: str) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def list_keys(self, prefix: Optional[str] = None) -> List[str]: ...
    def size(self, key: str) -> int: ...
```

**Implementations:**

| Class | Use Case | Persistence | Thread-Safe |
|-------|----------|-------------|-------------|
| `FileStorageBackend` | Production | Yes (disk) | Yes (atomic ops) |
| `MemoryStorageBackend` | Testing | No (RAM) | No |

**Custom Exceptions:**
```python
StorageError           # Base exception for all storage errors
StorageNotFoundError   # Key does not exist
StoragePermissionError # Permission denied
```

**Critical Rules:**
1. **ALWAYS** catch `StorageNotFoundError` when reading
2. **NEVER** assume a key exists - check with `exists()` first
3. `FileStorageBackend` uses atomic writes internally
4. Keys can contain `/` for hierarchical organization

**Expected Usage Pattern:**
```python
from actifix.persistence.storage import FileStorageBackend, StorageNotFoundError

storage = FileStorageBackend("/path/to/data")

# Write (atomic)
storage.write("tickets/001.json", json_content)

# Read with error handling
try:
    content = storage.read("tickets/001.json")
except StorageNotFoundError:
    content = None

# List with prefix
ticket_keys = storage.list_keys(prefix="tickets/")
```

#### `persistence/atomic.py` - Atomic Operations

**Purpose:** Low-level atomic file operations.

**Interface Contract:**

| Function | Input | Output | Guarantee |
|----------|-------|--------|-----------|
| `atomic_write(path, content, encoding)` | Path, str, str | None | All-or-nothing |
| `atomic_append(path, content, max_size_bytes)` | Path, str, Optional[int] | None | Atomic, size-limited |
| `atomic_update(path, transform_fn, encoding)` | Path, Callable, str | str | Read-modify-write atomic |
| `safe_read(path, default, encoding)` | Path, Optional[str], str | str | Returns default on error |
| `safe_read_bytes(path, default)` | Path, Optional[bytes] | bytes | Returns default on error |

**Critical Rules:**
1. `atomic_update` holds a lock during transform - keep transform fast
2. `max_size_bytes` truncates at line boundary (no partial lines)
3. `safe_read` **never raises** - always returns string or default

#### `persistence/queue.py` - Operation Queue

**Purpose:** Durable queue for write operations with replay capability.

**Primary Export:** `PersistenceQueue`

```python
class PersistenceQueue:
    def enqueue(self, operation: str, key: str, content: str) -> str: ...
    def dequeue(self, entry_id: str) -> Optional[QueueEntry]: ...
    def peek(self, count: int = 1) -> List[QueueEntry]: ...
    def replay(self, handler: Callable[[QueueEntry], bool]) -> Dict[str, int]: ...
    def clear(self) -> int: ...
    def size(self) -> int: ...
    def is_empty(self) -> bool: ...
    def get_stats(self) -> Dict[str, Any]: ...
```

**QueueEntry Structure:**
```python
@dataclass
class QueueEntry:
    entry_id: str       # Unique identifier
    operation: str      # "write", "append", "delete"
    key: str           # Storage key
    content: str       # Content (may be empty for delete)
    timestamp: str     # ISO timestamp
    retries: int       # Number of replay attempts
```

**Replay Contract:**
```python
def handler(entry: QueueEntry) -> bool:
    """
    Return True if operation succeeded (entry will be removed).
    Return False to keep entry for retry.
    Raise exception to keep entry and stop replay.
    """
```

**Critical Rules:**
1. Queue persists to disk - survives crashes
2. `replay` processes entries in FIFO order
3. Failed entries are kept for retry (with incremented `retries`)
4. Old entries are **automatically pruned** after configurable age

#### `persistence/manager.py` - High-Level Persistence

**Purpose:** Transactional document management with queue integration.

**Primary Export:** `PersistenceManager`

```python
class PersistenceManager:
    def write_document(self, key: str, content: str, queue: bool = True) -> None: ...
    def read_document(self, key: str) -> str: ...
    def read_document_safe(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def append_to_document(self, key: str, content: str, max_size: Optional[int] = None) -> None: ...
    def update_document(self, key: str, transform: Callable[[str], str]) -> str: ...
    def delete_document(self, key: str) -> bool: ...
    def exists(self, key: str) -> bool: ...
    def list_documents(self, prefix: Optional[str] = None) -> List[str]: ...
    def transaction(self) -> ContextManager[Transaction]: ...
    def replay_queue(self) -> Dict[str, int]: ...
```

**Transaction Support:**
```python
with manager.transaction() as txn:
    txn.write("key1", "value1")
    txn.append("key2", "more content")
    txn.delete("key3")
    # All operations commit atomically
    # On exception: all operations roll back
```

**Critical Rules:**
1. Use `queue=True` (default) for durability - operations survive crashes
2. Use `queue=False` for performance when durability not needed
3. Transactions are **all-or-nothing** - partial commits never occur
4. Call `replay_queue()` at startup to recover pending operations

#### `persistence/health.py` - Storage Health

**Purpose:** Validate storage integrity and detect corruption.

**Interface Contract:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `check_storage_health(backend, test_key)` | StorageBackend, str | HealthStatus | Basic read/write test |
| `detect_corruption(backend, sample_keys)` | StorageBackend, List[str] | Dict | Check for unreadable data |
| `compute_hash(backend, key)` | StorageBackend, str | Optional[str] | SHA256 of content |
| `verify_integrity(backend, key, expected_hash)` | StorageBackend, str, str | bool | Hash comparison |

**HealthStatus Fields:**
```python
@dataclass
class HealthStatus:
    healthy: bool
    writable: bool
    readable: bool
    errors: List[str]
    checked_at: datetime
```

**Critical Rules:**
1. Run health check at startup: `status = check_storage_health(storage)`
2. If `not status.healthy`, **do not proceed** - investigate errors
3. Use `verify_integrity` for critical data after recovery

---

## 3.3 Domain Layer

### `src/actifix/quarantine.py` - Error Isolation

**Purpose:** Isolate corrupted or problematic data to prevent system-wide failures.

**Interface Contract:**

| Function | Input | Output | Side Effects |
|----------|-------|--------|--------------|
| `quarantine_content(content, reason, source, paths)` | str, str, str, Optional[ActifixPaths] | str | Creates quarantine file |
| `quarantine_file(file_path, reason, paths)` | Path, str, Optional[ActifixPaths] | str | Moves file to quarantine |
| `list_quarantine(paths)` | Optional[ActifixPaths] | List[QuarantineEntry] | None |
| `remove_quarantine(quarantine_id, paths)` | str, Optional[ActifixPaths] | bool | Deletes quarantine entry |
| `get_quarantine_count(paths)` | Optional[ActifixPaths] | int | None |
| `validate_ticket_block(block)` | str | tuple[bool, str] | None (validation only) |
| `repair_list_file(paths, dry_run)` | Optional[ActifixPaths], bool | Dict | Repairs ACTIFIX-LIST.md |

**QuarantineEntry Structure:**
```python
@dataclass
class QuarantineEntry:
    quarantine_id: str    # e.g., "Q-20260110-abc123"
    timestamp: datetime
    reason: str
    source: str           # Original source file/location
    content_path: Path    # Path to quarantined content
```

**Critical Rules:**
1. **NEVER** delete corrupted data - quarantine it first
2. Quarantine IDs are **immutable** - use for audit trail
3. `repair_list_file` should be run when list file corruption detected
4. Always log quarantine operations to audit trail

**Expected Usage Pattern:**
```python
from actifix.quarantine import quarantine_content, validate_ticket_block

# Validate before processing
valid, error = validate_ticket_block(block)
if not valid:
    # Quarantine bad content
    qid = quarantine_content(
        content=block,
        reason=f"Invalid ticket block: {error}",
        source="ACTIFIX-LIST.md"
    )
    logger.warning(f"Quarantined invalid content: {qid}")
else:
    # Process valid content
    process_ticket(block)
```

---

## 3.4 Application Layer

### `src/actifix/raise_af.py` - Error Capture and Ticket Creation

**Purpose:** The ONLY entry point for recording errors. All errors flow through this module.

**Primary Exports:**

```python
class TicketPriority(str, Enum):
    P0 = "P0"  # Critical - system down, data loss risk
    P1 = "P1"  # High - major feature broken
    P2 = "P2"  # Medium - feature degraded
    P3 = "P3"  # Low - minor issue
    P4 = "P4"  # Trivial - cosmetic/enhancement

@dataclass
class ActifixEntry:
    entry_id: str           # Unique entry ID (e.g., "AF-20260110-abc123")
    timestamp: str          # ISO 8601 timestamp
    source: str             # Source file/module
    error_type: str         # Exception class name or error category
    message: str            # Human-readable error message
    stack_trace: str        # Full stack trace
    file_context: Dict      # Surrounding code context
    system_state: Dict      # Memory, CPU, disk state
    priority: TicketPriority
    duplicate_guard: str    # Hash for deduplication
    correlation_id: str     # For request tracing
    ai_notes: str          # AI remediation hints
```

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `record_error(message, source, correlation_id, error_type, priority, extra_context)` | str, str, Optional[str], str, Optional[TicketPriority], Optional[Dict] | Optional[str] | Creates ticket, logs | None (fails silently) |
| `generate_entry_id()` | None | str | None | None |
| `generate_ticket_id()` | None | str | None | None |
| `generate_duplicate_guard(source, message, error_type)` | str, str, str | str | None | None |
| `check_duplicate_guard(guard, base_dir)` | str, Path | bool | None | None |
| `classify_priority(error_type, message, source)` | str, str, str | TicketPriority | None | None |
| `capture_stack_trace()` | None | str | None | None |
| `capture_file_context(source, max_lines)` | str, int | Dict | None | None |
| `capture_system_state()` | None | Dict | None | None |
| `redact_secrets_from_text(text)` | str | str | None | None |

**Duplicate Guard System:**
```python
# Duplicate guard is a hash of: source + message + error_type
# If a guard already exists in ACTIFIX-LIST.md OR Completed section:
#   - The error is NOT recorded again
#   - This prevents infinite loops of the same error
```

**Priority Classification Rules:**
```python
# P0 - Critical:
#   - "critical", "fatal", "emergency" in message
#   - SystemExit, KeyboardInterrupt exceptions
#   - Data corruption indicators

# P1 - High:
#   - Database errors, authentication failures
#   - Core functionality broken

# P2 - Medium:
#   - Standard exceptions (ValueError, TypeError, etc.)
#   - Default priority

# P3 - Low:
#   - Warnings promoted to errors
#   - Non-critical integrations

# P4 - Trivial:
#   - Cosmetic issues, deprecation warnings
```

**Critical Rules:**
1. **ALL errors MUST flow through `record_error()`** - no exceptions
2. `record_error()` **NEVER raises** - it logs failures internally
3. Secrets are **automatically redacted** from all captured context
4. Duplicate guards prevent the same error from creating multiple tickets
5. The fallback queue ensures errors are recorded even if main storage fails

**Fallback Queue Mechanism:**
```python
# If writing to ACTIFIX-LIST.md fails:
1. Entry is queued to .actifix/fallback_queue.json
2. On next successful operation, replay_fallback_queue() is called
3. Queued entries are written to main storage
4. This ensures NO error is ever lost
```

**Expected Usage Pattern:**
```python
from actifix.raise_af import record_error, TicketPriority

# Basic error recording
record_error(
    message="Database connection failed",
    source="db/connection.py"
)

# With explicit priority and correlation
record_error(
    message="Payment processing failed",
    source="payments/stripe.py",
    correlation_id="req-abc123",
    error_type="PaymentError",
    priority=TicketPriority.P1,
    extra_context={"customer_id": "cust_xxx", "amount": 99.99}
)

# From exception handler
try:
    risky_operation()
except Exception as e:
    record_error(
        message=str(e),
        source=__file__,
        error_type=type(e).__name__
    )
```

### `src/actifix/do_af.py` - Ticket Processing and Remediation

**Purpose:** Process tickets, coordinate fixes, and track completion.

**Primary Exports:**

```python
@dataclass
class TicketInfo:
    ticket_id: str          # e.g., "AF-20260110-001"
    entry_id: str           # Original entry ID
    priority: str           # P0-P4
    source: str             # Source file
    message: str            # Error message
    created: str            # ISO timestamp
    status: str             # "open" or "completed"
    duplicate_guard: str    # For dedup checking
    raw_block: str          # Original markdown block

class StatefulTicketManager:
    """Cached ticket management with TTL-based invalidation."""
    def get_open_tickets(self) -> list[TicketInfo]: ...
    def get_completed_tickets(self) -> list[TicketInfo]: ...
    def get_stats(self) -> dict: ...
    def invalidate_cache(self) -> None: ...
```

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `get_open_tickets(paths, use_cache)` | Optional[ActifixPaths], bool | list[TicketInfo] | None | None |
| `get_completed_tickets(paths, use_cache)` | Optional[ActifixPaths], bool | list[TicketInfo] | None | None |
| `get_ticket_stats(paths, use_cache)` | Optional[ActifixPaths], bool | dict | None | None |
| `mark_ticket_complete(ticket_id, resolution, paths)` | str, str, Optional[ActifixPaths] | bool | Moves ticket | None |
| `process_next_ticket(processor_fn, paths)` | Callable, Optional[ActifixPaths] | Optional[str] | Processes ticket | None |
| `process_tickets(processor_fn, max_tickets, paths)` | Callable, int, Optional[ActifixPaths] | dict | Batch process | None |
| `parse_ticket_block(block)` | str | Optional[TicketInfo] | None | None |
| `get_ticket_manager(paths, cache_ttl)` | Optional[ActifixPaths], int | StatefulTicketManager | Creates singleton | None |

**Ticket Processing Flow:**
```
1. get_open_tickets() returns tickets sorted by priority (P0 first)
2. process_next_ticket() picks highest priority ticket
3. processor_fn(ticket) is called - returns resolution string
4. If successful, mark_ticket_complete() moves ticket to Completed section
5. AFLog.txt records the completion event
```

**Processor Function Contract:**
```python
def my_processor(ticket: TicketInfo) -> str:
    """
    Process a ticket and return resolution description.
    
    Args:
        ticket: The ticket to process
        
    Returns:
        Resolution string (e.g., "Fixed null check in line 42")
        
    Raises:
        Any exception - ticket remains open, error is logged
    """
    # Analyze the error
    # Apply fix
    # Run tests
    return "Applied fix: added null check"
```

**Concurrency and Locking:**
```python
# File-level locking prevents concurrent ticket modifications
# Lock is acquired via _ticket_lock() context manager
# Lock timeout: 10 seconds (configurable)
# On timeout: operation fails gracefully, no corruption
```

**Critical Rules:**
1. **ALWAYS** process tickets by priority order (P0 before P1, etc.)
2. **NEVER** mark a ticket complete without validation
3. Cache invalidation is **automatic** when list file changes
4. The ticket manager is a **singleton** - use `get_ticket_manager()`
5. Locking ensures **no concurrent modifications** to ticket list

**Expected Usage Pattern:**
```python
from actifix.do_af import (
    get_open_tickets, 
    mark_ticket_complete,
    process_tickets,
    get_ticket_stats
)

# Get current stats
stats = get_ticket_stats()
print(f"Open: {stats['open']}, Completed: {stats['completed']}")

# Process tickets with custom handler
def auto_fix(ticket):
    if "null" in ticket.message.lower():
        return "Added null safety check"
    raise ValueError("Cannot auto-fix this ticket")

results = process_tickets(
    processor_fn=auto_fix,
    max_tickets=5
)
print(f"Processed: {results['processed']}, Failed: {results['failed']}")

# Manual completion
mark_ticket_complete(
    ticket_id="AF-20260110-001",
    resolution="Fixed manually by adding input validation"
)
```

### `src/actifix/health.py` - System Health Monitoring

**Purpose:** Monitor system health, detect SLA breaches, and report status.

**Primary Export:**

```python
@dataclass
class ActifixHealthCheck:
    status: str             # "OK", "WARNING", "ERROR", "SLA_BREACH"
    open_tickets: int       # Count of open tickets
    completed_tickets: int  # Count of completed tickets
    p0_count: int          # Critical tickets
    p1_count: int          # High priority tickets
    sla_breaches: list     # Tickets breaching SLA
    storage_health: bool   # Storage backend healthy
    last_error: Optional[str]
    checked_at: datetime
```

**Interface Contract:**

| Function | Input | Output | Side Effects | Exceptions |
|----------|-------|--------|--------------|------------|
| `get_health(paths)` | Optional[ActifixPaths] | ActifixHealthCheck | None | None |
| `check_sla_breaches(paths)` | Optional[ActifixPaths] | list[dict] | None | None |
| `run_health_check(paths, print_report)` | Optional[ActifixPaths], bool | ActifixHealthCheck | Prints if requested | None |
| `format_health_report(health)` | ActifixHealthCheck | str | None | None |

**SLA Thresholds (Default):**
```python
SLA_HOURS = {
    "P0": 1,    # 1 hour - Critical
    "P1": 4,    # 4 hours - High
    "P2": 24,   # 24 hours - Medium
    "P3": 72,   # 72 hours - Low
    "P4": 168,  # 1 week - Trivial
}
```

**Health Status Logic:**
```python
def determine_status(health):
    if health.sla_breaches:
        return "SLA_BREACH"
    if health.p0_count > 0:
        return "ERROR"
    if health.p1_count > 0 or health.open_tickets > 10:
        return "WARNING"
    return "OK"
```

**Critical Rules:**
1. Health checks are **non-blocking** - never raises exceptions
2. SLA breaches are calculated from ticket `created` timestamp
3. Run health check **at startup** and **periodically** (recommended: every 5 min)
4. `status == "SLA_BREACH"` requires immediate attention

**Expected Usage Pattern:**
```python
from actifix.health import get_health, run_health_check, format_health_report

# Quick status check
health = get_health()
if health.status != "OK":
    print(f"⚠️  System health: {health.status}")
    print(f"   P0 tickets: {health.p0_count}")
    print(f"   SLA breaches: {len(health.sla_breaches)}")

# Full report
health = run_health_check(print_report=True)

# Custom reporting
report = format_health_report(health)
send_to_monitoring_system(report)
```

---

## 3.5 Presentation Layer

### `src/actifix/api.py` - REST API Server

**Purpose:** HTTP API for frontend and external integrations.

**Interface Contract:**

| Endpoint | Method | Response | Purpose |
|----------|--------|----------|---------|
| `/api/ping` | GET | `{"status": "ok"}` | Health check |
| `/api/health` | GET | `ActifixHealthCheck` | Full health status |
| `/api/version` | GET | Version info | Git commit, version |
| `/api/stats` | GET | Ticket statistics | Open/completed counts |
| `/api/tickets` | GET | List of tickets | All open and completed |
| `/api/logs` | GET | Recent log entries | Last N log lines |
| `/api/system` | GET | System resources | CPU, memory, disk |
| `/api/modules` | GET | Module catalog | Architecture info |

**Response Format (all endpoints):**
```python
{
    "success": bool,
    "data": {...},        # Actual response data
    "error": str | None,  # Error message if failed
    "timestamp": str      # ISO timestamp
}
```

**API Server Functions:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `create_app(project_root)` | Optional[Path] | Flask app | Create configured app |
| `run_api_server(host, port, debug, project_root)` | str, int, bool, Optional[Path] | None | Start server |

**Critical Rules:**
1. **ALWAYS** return JSON with consistent structure
2. **NEVER** expose internal paths or sensitive data in responses
3. **ALWAYS** include CORS headers for frontend access
4. API errors return HTTP 200 with `success: false` (not 500)
5. System resources (CPU/memory) must **never return null**

**Expected Usage Pattern:**
```python
from actifix.api import create_app, run_api_server

# Create app for testing
app = create_app()
with app.test_client() as client:
    response = client.get('/api/health')
    assert response.status_code == 200

# Run production server
run_api_server(host="0.0.0.0", port=5001)
```

### `src/actifix/main.py` - CLI Interface

**Purpose:** Command-line interface for all actifix operations.

**CLI Commands:**

| Command | Arguments | Purpose |
|---------|-----------|---------|
| `actifix init` | `--project-root` | Initialize actifix in project |
| `actifix health` | `--json` | Show health status |
| `actifix record` | `--message`, `--source`, `--priority` | Record an error manually |
| `actifix process` | `--max-tickets` | Process pending tickets |
| `actifix stats` | `--json` | Show ticket statistics |
| `actifix quarantine` | `list`, `remove` | Manage quarantine |
| `actifix test` | None | Run self-tests |

**Exit Codes:**
```python
EXIT_SUCCESS = 0    # Command completed successfully
EXIT_ERROR = 1      # Command failed
EXIT_USAGE = 2      # Invalid usage/arguments
```

**Critical Rules:**
1. **ALWAYS** exit with appropriate code
2. **NEVER** suppress errors - log and exit with code 1
3. `--json` flag outputs machine-readable JSON
4. Commands are **idempotent** where possible

---

# PART 4: DATA CONTRACTS AND FILE FORMATS

## 4.1 ACTIFIX-LIST.md Format

**Location:** `actifix/ACTIFIX-LIST.md`

**Structure:**
```markdown
# ACTIFIX-LIST

## Open Tickets

### [AF-YYYYMMDD-XXXXXX] Priority: PX
- **Source:** path/to/file.py
- **Error Type:** ExceptionType
- **Message:** Human readable error message
- **Created:** 2026-01-10T12:00:00Z
- **Duplicate Guard:** hash_value
- **Correlation ID:** corr-id-value

<details>
<summary>Stack Trace</summary>

```
Full stack trace here
```

</details>

<details>
<summary>AI Notes</summary>

Suggested remediation steps...

</details>

---

## Completed Items

### [AF-YYYYMMDD-XXXXXX] Priority: PX ✅
- **Resolved:** 2026-01-10T14:00:00Z
- **Resolution:** Description of fix applied

(original ticket content preserved below)
```

**Parsing Contract:**
```python
# Block delimiter: "---" on its own line
# Ticket ID pattern: r'\[AF-\d{8}-[a-f0-9]+\]'
# Priority pattern: r'Priority: P[0-4]'
# Required fields: Source, Message, Created, Duplicate Guard
```

## 4.2 ACTIFIX.md Format (Recent Errors)

**Location:** `actifix/ACTIFIX.md`

**Structure:**
```markdown
# Recent Errors (Last 20)

## [AF-YYYYMMDD-XXXXXX] 2026-01-10T12:00:00Z
**Source:** path/to/file.py
**Message:** Error message

---
```

**Rolling Window:**
- Maximum 20 entries
- LIFO order (newest first)
- Truncated when limit exceeded

## 4.3 AFLog.txt Format

**Location:** `actifix/AFLog.txt`

**Structure:**
```
[2026-01-10T12:00:00Z] TICKET_CREATED | AF-20260110-abc123 | P2 | source.py | message
[2026-01-10T12:30:00Z] TICKET_COMPLETED | AF-20260110-abc123 | Resolution text
[2026-01-10T12:31:00Z] HEALTH_CHECK | OK | open=5 completed=42
[2026-01-10T12:32:00Z] QUARANTINE_CREATED | Q-20260110-def456 | reason
```

**Event Types:**
- `TICKET_CREATED` - New ticket recorded
- `TICKET_COMPLETED` - Ticket marked complete
- `HEALTH_CHECK` - Periodic health check
- `QUARANTINE_CREATED` - Content quarantined
- `ERROR` - Internal error (meta)

## 4.4 Quarantine File Format

**Location:** `actifix/quarantine/Q-YYYYMMDD-XXXXXX.json`

**Structure:**
```json
{
  "quarantine_id": "Q-20260110-abc123",
  "timestamp": "2026-01-10T12:00:00Z",
  "reason": "Invalid ticket block: missing required field",
  "source": "ACTIFIX-LIST.md",
  "content": "Original content that was quarantined"
}
```

---

# PART 5: ERROR FLOW AND LIFECYCLE

## 5.1 Error Capture Flow

```
Exception Occurs
       │
       ▼
bootstrap.py (exception handler)
       │
       ▼
raise_af.record_error()
       │
       ├──► check_duplicate_guard() ──► Already exists? ──► SKIP
       │
       ▼
generate_entry_id()
       │
       ▼
capture_stack_trace()
capture_file_context()
capture_system_state()
       │
       ▼
classify_priority()
       │
       ▼
redact_secrets_from_text()
       │
       ▼
_append_ticket() ──► FAIL? ──► _queue_to_fallback()
       │
       ▼
_append_recent()
       │
       ▼
log_event(AFLog.txt)
       │
       ▼
Return entry_id
```

## 5.2 Ticket Lifecycle

```
CREATED ──► OPEN ──► PROCESSING ──► COMPLETED
   │          │          │              │
   │          │          │              ▼
   │          │          │         (in Completed section)
   │          │          │
   │          │          └──► FAILED (remains OPEN)
   │          │
   │          └──► STALE (SLA breach)
   │
   └──► DUPLICATE (not created)
```

## 5.3 Recovery Flow (Startup)

```
bootstrap()
    │
    ▼
replay_fallback_queue()
    │
    ▼
check_storage_health()
    │
    ├──► UNHEALTHY ──► Log warning, continue with degraded mode
    │
    ▼
run_health_check()
    │
    ├──► SLA_BREACH ──► Alert (log prominently)
    │
    ▼
System ready
```

---

# PART 6: TESTING FRAMEWORK

## 6.1 Test Categories

| Category | Location | Purpose | Run Command |
|----------|----------|---------|-------------|
| Unit | `test/test_*.py` | Module isolation | `pytest test/` |
| Integration | `test/test_comprehensive.py` | Cross-module | `pytest -k comprehensive` |
| Architecture | `test/test_architecture_validation.py` | Dependency rules | `pytest -k architecture` |
| System | `src/actifix/testing/system.py` | End-to-end | `python test.py` |

## 6.2 Test Requirements

**Coverage Requirements:**
```python
MINIMUM_COVERAGE = 95  # Percent
CRITICAL_PATHS = [
    "raise_af.record_error",
    "do_af.mark_ticket_complete",
    "persistence.atomic_write",
]
# Critical paths require 100% coverage
```

**Test Isolation:**
```python
# Every test MUST:
1. Use isolated temporary directories
2. Reset all singletons (reset_actifix_paths(), reset_config())
3. Not depend on external state
4. Clean up after execution
```

## 6.3 Test Utilities

**`src/actifix/testing/__init__.py` exports:**

```python
def assert_true(condition: bool, message: str) -> None: ...
def assert_equals(actual, expected, message: str = "") -> None: ...
def assert_raises(exception_type, callable, *args, **kwargs) -> None: ...
```

**`src/actifix/testing/system.py` exports:**

```python
def build_system_tests(paths: ActifixPaths) -> list[tuple]: ...
# Returns: [(name, func, description, tags), ...]
```

## 6.4 Running Tests

```bash
# Full suite (REQUIRED before commit)
python test.py

# With coverage
python test.py --coverage

# Quick mode (skips slow tests)
python test.py --quick

# Specific pattern
pytest test/ -k "raise_af"

# Architecture validation only
pytest test/test_architecture_validation.py -v
```

---

# PART 7: COMMON PATTERNS AND ANTI-PATTERNS

## 7.1 Correct Patterns ✅

**Error Recording:**
```python
# ✅ CORRECT: Use record_error for all errors
from actifix.raise_af import record_error

try:
    dangerous_operation()
except Exception as e:
    record_error(message=str(e), source=__file__)
    raise  # Re-raise after recording
```

**Path Access:**
```python
# ✅ CORRECT: Use ActifixPaths
from actifix.state_paths import get_actifix_paths

paths = get_actifix_paths()
list_file = paths.list_file
```

**File Writing:**
```python
# ✅ CORRECT: Use atomic operations
from actifix.log_utils import atomic_write

atomic_write(path, content)
```

## 7.2 Anti-Patterns ❌

**Manual Error Handling:**
```python
# ❌ WRONG: Silently catching errors
try:
    operation()
except Exception:
    pass  # Error lost forever!
```

**Manual Path Construction:**
```python
# ❌ WRONG: Hardcoding paths
log_file = Path("actifix/ACTIFIX-LIST.md")  # May not exist!
```

**Non-Atomic Writes:**
```python
# ❌ WRONG: Can corrupt on crash
with open(path, "w") as f:
    f.write(content)
```

**Bypassing Duplicate Guards:**
```python
# ❌ WRONG: Creates infinite loops
entry = ActifixEntry(...)
_append_ticket(entry)  # Skips duplicate check!
```

---

# PART 8: QUICK REFERENCE

## 8.1 Import Cheat Sheet

```python
# Bootstrap
from actifix.bootstrap import bootstrap, shutdown, ActifixContext

# Paths
from actifix.state_paths import get_actifix_paths, ensure_actifix_dirs

# Config
from actifix.config import load_config, get_config

# Error Recording (MOST IMPORTANT)
from actifix.raise_af import record_error, TicketPriority

# Ticket Processing
from actifix.do_af import get_open_tickets, mark_ticket_complete, get_ticket_stats

# Health
from actifix.health import get_health, run_health_check

# Quarantine
from actifix.quarantine import quarantine_content, validate_ticket_block

# Persistence
from actifix.persistence.storage import FileStorageBackend
from actifix.persistence.atomic import atomic_write, safe_read
from actifix.persistence.manager import PersistenceManager

# Logging
from actifix.log_utils import atomic_write, idempotent_append
```

## 8.2 Common Operations

```python
# Initialize system
with ActifixContext() as paths:
    # System ready

# Record an error
record_error("Something failed", source=__file__)

# Check health
health = get_health()
if health.status != "OK":
    print(f"Warning: {health.status}")

# Process tickets
stats = get_ticket_stats()
print(f"Open: {stats['open']}")

# Mark complete
mark_ticket_complete("AF-20260110-abc123", "Fixed by adding null check")
```

## 8.3 File Locations

| File | Path | Purpose |
|------|------|---------|
| Ticket List | `actifix/ACTIFIX-LIST.md` | All tickets |
| Recent Errors | `actifix/ACTIFIX.md` | Last 20 errors |
| Audit Log | `actifix/AFLog.txt` | Event history |
| Quarantine | `actifix/quarantine/` | Isolated content |
| State | `.actifix/` | Internal state |
| Logs | `logs/` | Application logs |

---

**END OF AGENTS.md**

*This document must be kept up to date.*
