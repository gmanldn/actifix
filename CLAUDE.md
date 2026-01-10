# Coding Agent Instructions (AGENTS/CLAUDE/GPT)

This file provides essential context and rules for all coding agents working with the Actifix codebase.
It is synchronized across `AGENTS.md`, `CLAUDE.md`, and `GPT.md`.

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

## 5. Agent Instruction Files Must Stay in Sync

**CRITICAL: `AGENTS.md`, `CLAUDE.md`, and `GPT.md` must always have identical content.**

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
