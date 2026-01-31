#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Backend for Actifix Tickets

SQLite-based storage with ACID compliance, row-level locking, and indexing.
Provides thread-safe connection pooling and automatic schema migrations.

Version: 1.0.0
"""

import atexit
import base64
import contextlib
import os
import json
import sqlite3
import sys
import threading
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Union

from ..log_utils import log_event

# Schema version for migrations
SCHEMA_VERSION = 7


class DatabaseSecurityError(Exception):
    """Raised when database path violates security requirements."""
    pass


DANGEROUS_PATH_PATTERNS = (
    # Unix/Linux
    "/tmp",
    "/var/tmp",
    "/dev/shm",  # Shared memory
    "/mnt",      # Mounted filesystems
    "/media",    # Removable media
    "/proc",
    "/sys",
    "/root/.trash",
    "/root/trash",
    # macOS equivalents (after resolve())
    "/private/tmp",
    "/private/var/tmp",
    # Trash directories
    "/.trash",
    "/trash",
    # Windows
    "c:\\temp",
    "c:\\users\\public",
    "c:\\windows\\temp",
    "%temp%",
    "%tmp%",
)


def _validate_database_path_directory(resolved_db_path: Path) -> None:
    """
    Validate the directory portion of the database path against shared locations.
    """
    path_str = str(resolved_db_path).lower()

    for pattern in DANGEROUS_PATH_PATTERNS:
        pattern_lower = pattern.lower()
        if (path_str.startswith(pattern_lower) or
            f"/{pattern_lower}/" in path_str or
            f"\\{pattern_lower}\\" in path_str):
            raise DatabaseSecurityError(
                f"Database path '{resolved_db_path}' is in a shared or public directory. "
                "Please use a private user directory (e.g., ~/.actifix or ./data)."
            )


def _validate_database_file_permissions(resolved_db_path: Path) -> None:
    """
    Ensure the database file is not world-readable or world-writable.
    """
    import os
    if os.name == 'nt':
        # On Windows, ACLs handle permissions; skip Unix mode check
        return
    try:
        if resolved_db_path.exists():
            stat_info = resolved_db_path.stat()
            if stat_info.st_mode & 0o004:
                raise DatabaseSecurityError(
                    f"Database file '{resolved_db_path}' is world-readable. "
                    "Restrict file permissions with 'chmod 600'."
                )
            if stat_info.st_mode & 0o002:
                raise DatabaseSecurityError(
                    f"Database file '{resolved_db_path}' is world-writable. "
                    "Restrict file permissions with 'chmod 600'."
                )
    except (OSError, PermissionError):
        # Permission checks may fail on exotic filesystems; tolerate them.
        pass


def _validate_database_path(db_path: Path) -> None:
    """
    Validate database path isn't in shared or public directories and has secure permissions.
    """
    resolved = db_path.resolve()
    _validate_database_path_directory(resolved)
    _validate_database_file_permissions(resolved)


def _ensure_database_file_secure(db_path: Path) -> None:
    """Create/security-fix the database file before opening it."""
    resolved = db_path.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.touch(exist_ok=True)

    try:
        os.chmod(resolved, 0o600)
    except OSError:
        # Unable to adjust permissions; validation will flag this later.
        pass

# Database schema with indexing and locking support
SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tickets table with comprehensive indexing
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,              -- ACT-YYYYMMDD-XXXXX
    priority TEXT NOT NULL,           -- P0-P4
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT NOT NULL,
    run_label TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    duplicate_guard TEXT UNIQUE,      -- Prevents duplicates at DB level
    status TEXT DEFAULT 'Open',       -- Open, In Progress, Completed
    owner TEXT,                       -- Who's working on it
    locked_by TEXT,                   -- Lock holder (for concurrency)
    locked_at TIMESTAMP,              -- Lock timestamp
    lease_expires TIMESTAMP,          -- Lease-based locking with expiry
    branch TEXT,                      -- Git branch for work
    stack_trace TEXT,
    file_context TEXT,                -- JSON serialized
    system_state TEXT,                -- JSON serialized
    ai_remediation_notes TEXT,
    correlation_id TEXT,
    completion_summary TEXT,
    completion_notes TEXT NOT NULL DEFAULT '',         -- What was done to fix
    test_steps TEXT NOT NULL DEFAULT '',               -- How testing was performed
    test_results TEXT NOT NULL DEFAULT '',             -- Test outcomes/evidence
    test_documentation_url TEXT,                       -- Optional: Link to test artifacts
    completion_verified_by TEXT,                       -- Optional: Who verified
    completion_verified_at TIMESTAMP,                  -- Optional: When verified
    github_issue_url TEXT,
    github_issue_number INTEGER,
    github_sync_state TEXT DEFAULT 'pending',
    github_sync_message TEXT,
    format_version TEXT DEFAULT '1.0',

    -- Checklist fields
    documented BOOLEAN DEFAULT 0,
    functioning BOOLEAN DEFAULT 0,
    tested BOOLEAN DEFAULT 0,
    completed BOOLEAN DEFAULT 0,

    -- Soft delete support (prevents permanent data loss)
    deleted BOOLEAN DEFAULT 0,
    deleted_at TIMESTAMP,

    CHECK (priority IN ('P0', 'P1', 'P2', 'P3', 'P4')),
    CHECK (status IN ('Open', 'In Progress', 'Completed'))
);

-- Event log table (replaces AFLog.txt)
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,           -- TICKET_CREATED, DISPATCH_STARTED, etc.
    message TEXT NOT NULL,
    ticket_id TEXT,                      -- FK to tickets.id (nullable)
    correlation_id TEXT,                 -- For tracing across operations
    extra_json TEXT,                     -- JSON serialized extra data
    source TEXT,                         -- Source file/function
    level TEXT DEFAULT 'INFO',           -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE SET NULL
);

-- Fallback queue table (replaces actifix_fallback_queue.json)
CREATE TABLE IF NOT EXISTS fallback_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,             -- The ticket ID being queued
    operation TEXT NOT NULL,            -- "create_ticket", "update", etc.
    payload_json TEXT NOT NULL,         -- Serialized ActifixEntry
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_retry TIMESTAMP,
    status TEXT DEFAULT 'pending',      -- pending, processing, failed, completed
    error_message TEXT,
    
    UNIQUE(entry_id, operation)         -- Prevent duplicate queue entries
);

-- Quarantine table (replaces quarantine/*.md files)
CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT UNIQUE NOT NULL,      -- quarantine_YYYYMMDD_HHMMSS_ffffff
    original_source TEXT NOT NULL,      -- File path, ticket ID, etc.
    reason TEXT NOT NULL,
    content TEXT NOT NULL,              -- The quarantined content
    original_content_hash TEXT,         -- SHA256 for integrity
    quarantined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recovered_at TIMESTAMP,             -- NULL if not recovered
    recovery_notes TEXT,
    status TEXT DEFAULT 'quarantined'   -- quarantined, recovered, deleted
);

-- Database audit log (tracks all ticket changes)
CREATE TABLE IF NOT EXISTS database_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,                  -- tickets, event_log, etc.
    operation TEXT NOT NULL,                   -- INSERT, UPDATE, DELETE
    record_id TEXT,                            -- ticket_id or record identifier
    user_context TEXT,                         -- User who made the change
    old_values TEXT,                           -- JSON of previous values
    new_values TEXT,                           -- JSON of new values
    change_description TEXT,                   -- Human-readable description
    ip_address TEXT,                           -- IP address if web-based
    session_id TEXT,                           -- Session identifier

    CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- Views for rollup/history (replaces ACTIFIX.md and ACTIFIX-LOG.md)
CREATE VIEW IF NOT EXISTS v_recent_tickets AS
SELECT 
    id,
    priority,
    error_type,
    message,
    source,
    created_at,
    status
FROM tickets
ORDER BY created_at DESC
LIMIT 20;

CREATE VIEW IF NOT EXISTS v_ticket_history AS
SELECT 
    id,
    priority,
    error_type,
    message,
    source,
    created_at,
    updated_at,
    completion_summary,
    status
FROM tickets
WHERE status = 'Completed'
ORDER BY updated_at DESC;

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_duplicate_guard ON tickets(duplicate_guard);
CREATE INDEX IF NOT EXISTS idx_tickets_locked ON tickets(locked_by, locked_at);
CREATE INDEX IF NOT EXISTS idx_tickets_lease ON tickets(lease_expires);
CREATE INDEX IF NOT EXISTS idx_tickets_owner ON tickets(owner);
CREATE INDEX IF NOT EXISTS idx_tickets_correlation ON tickets(correlation_id);

-- Event log indexes
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_event_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_ticket_id ON event_log(ticket_id);
CREATE INDEX IF NOT EXISTS idx_event_log_correlation_id ON event_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_event_log_level ON event_log(level);

-- Fallback queue indexes
CREATE INDEX IF NOT EXISTS idx_fallback_queue_status ON fallback_queue(status);
CREATE INDEX IF NOT EXISTS idx_fallback_queue_created ON fallback_queue(created_at);

-- Quarantine indexes
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine(status);
CREATE INDEX IF NOT EXISTS idx_quarantine_source ON quarantine(original_source);
CREATE INDEX IF NOT EXISTS idx_quarantine_date ON quarantine(quarantined_at DESC);

-- Database audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON database_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_table ON database_audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON database_audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_record_id ON database_audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON database_audit_log(user_context);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON database_audit_log(table_name, record_id);

-- Agent voice table (for review/audit of agent activity)
CREATE TABLE IF NOT EXISTS agent_voice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agent_id TEXT NOT NULL,
    run_label TEXT,
    level TEXT DEFAULT 'INFO',
    thought TEXT NOT NULL,
    extra_json TEXT,
    correlation_id TEXT,

    CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

CREATE INDEX IF NOT EXISTS idx_agent_voice_created ON agent_voice(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_voice_agent ON agent_voice(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_voice_run_label ON agent_voice(run_label);
CREATE INDEX IF NOT EXISTS idx_agent_voice_level ON agent_voice(level);
"""


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    db_path: Path
    enable_wal: bool = True  # Write-Ahead Logging for concurrency
    timeout: float = 30.0  # Connection timeout in seconds
    check_same_thread: bool = False  # Allow multi-threaded access
    isolation_level: Optional[str] = "DEFERRED"  # Transaction isolation
    

class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Database connection failed."""
    pass


class DatabaseSchemaError(DatabaseError):
    """Schema migration or validation failed."""
    pass


class DatabasePool:
    """
    Thread-safe connection pool for SQLite.
    
    Each thread gets its own connection to avoid threading issues.
    Connections are kept in thread-local storage.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database pool.
        
        Args:
            config: Database configuration.
        """
        self.config = config
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialized = False
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create connection for current thread."""
        # Fast path: if connection exists and schema is initialized, return immediately
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            return self._local.connection

        # Slow path: need to create connection and potentially initialize schema
        try:
            # Ensure database directory exists
            self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create database file with secure permissions BEFORE SQLite creates it
            # This prevents the window where the file exists with world-readable permissions
            if not self.config.db_path.exists():
                # Touch the file and immediately set secure permissions
                self.config.db_path.touch(mode=0o600, exist_ok=True)
            else:
                # File exists - ensure it has secure permissions
                try:
                    os.chmod(self.config.db_path, 0o600)
                except OSError:
                    pass

            conn = sqlite3.connect(
                str(self.config.db_path),
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread,
                isolation_level=self.config.isolation_level,
            )

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Enable WAL mode for better concurrency
            if self.config.enable_wal:
                conn.execute("PRAGMA journal_mode = WAL")

            # Row factory for dict-like access
            conn.row_factory = sqlite3.Row

            # Initialize schema if this is first connection
            # Acquire lock to prevent race condition where multiple threads
            # try to initialize schema simultaneously
            # IMPORTANT: Do this BEFORE assigning connection to prevent other threads
            # from getting an incompletely initialized connection
            with self._lock:
                # Double-check pattern: check again inside lock
                if not self._initialized:
                    self._initialize_schema(conn)
                    self._initialized = True

            # Only assign connection AFTER schema is fully initialized
            # This prevents race condition where fast path returns connection
            # before schema initialization completes
            self._local.connection = conn

        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

        return self._local.connection
    
    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize or migrate database schema."""
        try:
            # Check current schema version
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            has_version_table = cursor.fetchone() is not None
            
            if not has_version_table:
                # Fresh database - create schema
                conn.executescript(SCHEMA_SQL)
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
                conn.commit()
            else:
                # Check if migration needed
                cursor = conn.execute("SELECT MAX(version) as version FROM schema_version")
                row = cursor.fetchone()
                current_version = row['version'] if row else 0
                
                if current_version < SCHEMA_VERSION:
                    # Run migrations
                    self._migrate_schema(conn, current_version, SCHEMA_VERSION)
        
        except sqlite3.Error as e:
            raise DatabaseSchemaError(f"Schema initialization failed: {e}") from e
    
    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        """
        Run schema migrations.

        Args:
            conn: Database connection.
            from_version: Current schema version.
            to_version: Target schema version.
        """
        # Migration from v1 to v2: Add event_log, fallback_queue, quarantine tables
        if from_version == 1 and to_version >= 2:
            # Execute the full schema (CREATE IF NOT EXISTS protects existing tables)
            conn.executescript(SCHEMA_SQL)

        # Migration from v2 to v3: Add completion quality fields
        if from_version == 2 and to_version >= 3:
            try:
                # Check if columns already exist (in case migration was partially applied)
                cursor = conn.execute("PRAGMA table_info(tickets)")
                column_names = {row[1] for row in cursor.fetchall()}

                # Add missing columns
                if 'completion_notes' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN completion_notes TEXT NOT NULL DEFAULT ''"
                    )

                if 'test_steps' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN test_steps TEXT NOT NULL DEFAULT ''"
                    )

                if 'test_results' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN test_results TEXT NOT NULL DEFAULT ''"
                    )

                if 'test_documentation_url' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN test_documentation_url TEXT"
                    )

                if 'completion_verified_by' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN completion_verified_by TEXT"
                    )

                if 'completion_verified_at' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN completion_verified_at TIMESTAMP"
                    )

                conn.commit()
            except sqlite3.Error as e:
                # Non-fatal: columns may already exist
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    log_event(
                        "DATABASE_ROLLBACK_FAILED",
                        f"Failed to rollback migration v2->v3: {rollback_error}",
                        extra={"migration": "v2_to_v3", "error": str(rollback_error)},
                    )
                    print(f"WARNING: Database migration rollback failed: {rollback_error}", file=sys.stderr)

        # Migration from v3 to v4: Add soft delete support
        if from_version <= 3 and to_version >= 4:
            try:
                cursor = conn.execute("PRAGMA table_info(tickets)")
                column_names = {row[1] for row in cursor.fetchall()}

                if 'deleted' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN deleted BOOLEAN DEFAULT 0"
                    )

                if 'deleted_at' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN deleted_at TIMESTAMP"
                    )

                # Create index for soft delete queries
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tickets_deleted ON tickets(deleted)"
                )

                conn.commit()
            except sqlite3.Error as e:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    log_event(
                        "DATABASE_ROLLBACK_FAILED",
                        f"Failed to rollback migration v3->v4: {rollback_error}",
                        extra={"migration": "v3_to_v4", "error": str(rollback_error)},
                    )
                    print(f"WARNING: Database migration rollback failed: {rollback_error}", file=sys.stderr)

        # Migration from v5 to v6: Add agent_voice table
        if from_version <= 5 and to_version >= 6:
            # Execute the full schema (CREATE IF NOT EXISTS protects existing tables)
            conn.executescript(SCHEMA_SQL)

        # Migration from v6 to v7: Add GitHub sync metadata
        if from_version <= 6 and to_version >= 7:
            try:
                cursor = conn.execute("PRAGMA table_info(tickets)")
                column_names = {row[1] for row in cursor.fetchall()}

                if 'github_issue_url' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN github_issue_url TEXT"
                    )
                if 'github_issue_number' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN github_issue_number INTEGER"
                    )
                if 'github_sync_state' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN github_sync_state TEXT DEFAULT 'pending'"
                    )
                if 'github_sync_message' not in column_names:
                    conn.execute(
                        "ALTER TABLE tickets ADD COLUMN github_sync_message TEXT"
                    )

                conn.commit()
            except sqlite3.Error as e:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    log_event(
                        "DATABASE_ROLLBACK_FAILED",
                        f"Failed to rollback migration v6->v7: {rollback_error}",
                        extra={"migration": "v6_to_v7", "error": str(rollback_error)},
                    )
                    print(f"WARNING: Database migration rollback failed: {rollback_error}", file=sys.stderr)
        # Migration from v4 to v5: Add database audit log table
        if from_version <= 4 and to_version >= 5:
            try:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='database_audit_log'")
                if cursor.fetchone() is None:
                    # Create audit log table
                    conn.execute("""
                        CREATE TABLE database_audit_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            table_name TEXT NOT NULL,
                            operation TEXT NOT NULL,
                            record_id TEXT,
                            user_context TEXT,
                            old_values TEXT,
                            new_values TEXT,
                            change_description TEXT,
                            ip_address TEXT,
                            session_id TEXT,
                            CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
                        )
                    """)

                    # Create indexes for audit log
                    indexes = [
                        "CREATE INDEX idx_audit_log_timestamp ON database_audit_log(timestamp DESC)",
                        "CREATE INDEX idx_audit_log_table ON database_audit_log(table_name)",
                        "CREATE INDEX idx_audit_log_operation ON database_audit_log(operation)",
                        "CREATE INDEX idx_audit_log_record_id ON database_audit_log(record_id)",
                        "CREATE INDEX idx_audit_log_user ON database_audit_log(user_context)",
                        "CREATE INDEX idx_audit_log_table_record ON database_audit_log(table_name, record_id)",
                    ]

                    for idx in indexes:
                        try:
                            conn.execute(idx)
                        except sqlite3.Error:
                            # Index may already exist, continue
                            pass

                conn.commit()
            except sqlite3.Error as e:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    log_event(
                        "DATABASE_ROLLBACK_FAILED",
                        f"Failed to rollback migration v4->v5: {rollback_error}",
                        extra={"migration": "v4_to_v5", "error": str(rollback_error)},
                    )
                    print(f"WARNING: Database migration rollback failed: {rollback_error}", file=sys.stderr)

        # Update version tracking
        conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (to_version,)
        )
        conn.commit()
    
    @contextlib.contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database connections.
        
        Yields:
            Database connection.
        """
        conn = self._get_connection()
        try:
            yield conn
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}") from e
    
    @contextlib.contextmanager
    def transaction(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """
        Context manager for transactions.

        Automatically commits on success, rolls back on error.

        Args:
            immediate: If True, use BEGIN IMMEDIATE to acquire write locks upfront.
                      Prevents lock upgrade conflicts in concurrent scenarios.

        Yields:
            Database connection.
        """
        conn = self._get_connection()
        try:
            begin_stmt = "BEGIN IMMEDIATE" if immediate else "BEGIN"
            conn.execute(begin_stmt)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """
        Get database connection pool health metrics.

        Returns:
            Dict with pool statistics and health indicators.
        """
        metrics = {
            "initialized": self._initialized,
            "has_connection": hasattr(self._local, 'connection') and self._local.connection is not None,
            "db_path": str(self.config.db_path),
            "wal_enabled": self.config.enable_wal,
        }

        # Add database file size if it exists
        if self.config.db_path.exists():
            metrics["db_size_bytes"] = self.config.db_path.stat().st_size
            metrics["db_size_mb"] = round(metrics["db_size_bytes"] / (1024 * 1024), 2)

        # Test connection health
        try:
            with self.connection() as conn:
                cursor = conn.execute("SELECT 1")
                if cursor.fetchone():
                    metrics["connection_healthy"] = True
                else:
                    metrics["connection_healthy"] = False
        except Exception as e:
            metrics["connection_healthy"] = False
            metrics["connection_error"] = str(e)

        # Get WAL stats if WAL mode is enabled
        if self.config.enable_wal and metrics["has_connection"]:
            try:
                with self.connection() as conn:
                    cursor = conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                    result = cursor.fetchone()
                    if result:
                        busy, log_frames, checkpointed = result
                        metrics["wal_checkpoint"] = {
                            "busy": busy,
                            "log_frames": log_frames,
                            "checkpointed": checkpointed,
                        }
            except Exception:
                pass

        return metrics

    def close(self) -> None:
        """Close connection for current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                # Checkpoint WAL and sync to disk before closing to prevent data loss
                if self.config.enable_wal:
                    try:
                        # RESTART checkpoint: blocks until all frames in WAL are transferred to database
                        # This ensures data is properly persisted before connection closes
                        self._local.connection.execute("PRAGMA wal_checkpoint(RESTART)")
                        # Explicit commit to ensure all transactions are flushed
                        self._local.connection.commit()
                    except sqlite3.Error:
                        # Non-fatal: continue with close even if checkpoint fails
                        pass

                # Perform explicit fsync on the database file itself
                # This ensures data is physically written to disk, preventing data loss
                # in case of power failure or OS crash after the checkpoint
                try:
                    db_fd = os.open(str(self.config.db_path), os.O_RDONLY)
                    try:
                        os.fsync(db_fd)
                    finally:
                        os.close(db_fd)
                except (OSError, IOError):
                    # Non-fatal: database may not exist or be accessible
                    pass

                self._local.connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._local.connection = None
    
    def close_all(self) -> None:
        """Close all connections (call on shutdown)."""
        # Note: Can't access other threads' local storage
        # Just close current thread's connection
        self.close()


# Global database pool instance
_global_pool: Optional[DatabasePool] = None
_pool_lock = threading.Lock()


def get_database_pool(db_path: Optional[Path] = None) -> DatabasePool:
    """
    Get or create global database pool.
    
    Args:
        db_path: Optional database path override.
    
    Returns:
        Database pool instance.
    """
    global _global_pool
    
    if db_path is None:
        # Use env override or project root / data directory for database
        from pathlib import Path as _Path
        env_db_path = os.environ.get("ACTIFIX_DB_PATH")
        db_path = Path(env_db_path).expanduser() if env_db_path else (_Path.cwd() / "data" / "actifix.db")

    resolved_db_path = db_path.resolve()
    _validate_database_path_directory(resolved_db_path)
    _ensure_database_file_secure(resolved_db_path)
    _validate_database_file_permissions(resolved_db_path)

    with _pool_lock:
        if _global_pool is None or _global_pool.config.db_path != resolved_db_path:
            config = DatabaseConfig(db_path=resolved_db_path)
            _global_pool = DatabasePool(config)
        
        return _global_pool


def get_database_connection(paths: Optional[object] = None) -> sqlite3.Connection:
    """
    Backward-compatible helper to get a raw database connection.

    Accepts an optional paths object with a project_root attribute. Uses
    ACTIFIX_DB_PATH when set, otherwise falls back to <project_root>/data/actifix.db.
    """
    env_db_path = os.environ.get("ACTIFIX_DB_PATH")
    if env_db_path:
        db_path = Path(env_db_path).expanduser()
    elif paths is not None and hasattr(paths, "project_root"):
        db_path = Path(getattr(paths, "project_root")) / "data" / "actifix.db"
    else:
        db_path = Path.cwd() / "data" / "actifix.db"

    pool = get_database_pool(db_path=db_path)
    return pool._get_connection()


def reset_database_pool() -> None:
    """Reset global database pool (for testing)."""
    global _global_pool
    
    with _pool_lock:
        if _global_pool:
            _global_pool.close_all()
            _global_pool = None


# Ensure pool closes when the interpreter exits
atexit.register(reset_database_pool)

# Utility functions for serialization

def serialize_json_field(obj: Any) -> Optional[str]:
    """Serialize object to JSON string for storage."""
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, default=str)


def deserialize_json_field(json_str: Optional[str]) -> Any:
    """Deserialize JSON string from storage."""
    if json_str is None:
        return None
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def serialize_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO format string."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def deserialize_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Deserialize timestamp string to datetime."""
    if ts_str is None:
        return None
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def log_database_audit(
    pool: Optional[DatabasePool] = None,
    table_name: str = "",
    operation: str = "",
    record_id: Optional[str] = None,
    user_context: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    change_description: Optional[str] = None,
    ip_address: Optional[str] = None,
    session_id: Optional[str] = None,
) -> bool:
    """
    Log a database change to the audit log table.

    Args:
        pool: Database pool (uses global pool if None).
        table_name: Table that was modified (tickets, event_log, etc.).
        operation: Operation performed (INSERT, UPDATE, DELETE).
        record_id: ID of the record that was modified.
        user_context: User who made the change.
        old_values: Previous values as dict (will be JSON serialized).
        new_values: New values as dict (will be JSON serialized).
        change_description: Human-readable description of the change.
        ip_address: IP address of the requester (if applicable).
        session_id: Session identifier (if applicable).

    Returns:
        True if logged successfully, False otherwise.
    """
    if pool is None:
        pool = get_database_pool()

    try:
        with pool.transaction() as conn:
            conn.execute(
                """
                INSERT INTO database_audit_log (
                    table_name, operation, record_id, user_context,
                    old_values, new_values, change_description,
                    ip_address, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    table_name,
                    operation,
                    record_id,
                    user_context,
                    serialize_json_field(old_values),
                    serialize_json_field(new_values),
                    change_description,
                    ip_address,
                    session_id,
                )
            )
        return True
    except Exception as e:
        # Log audit failure but don't raise to avoid disrupting main operations
        log_event(
            "DATABASE_AUDIT_FAILED",
            f"Failed to log database audit: {e}",
            extra={
                "table": table_name,
                "operation": operation,
                "record_id": record_id,
                "error": str(e),
            },
        )
        print(f"Failed to log database audit: {e}", file=sys.stderr)
        return False


def run_vacuum(pool: Optional[DatabasePool] = None) -> bool:
    """
    Run VACUUM command to reclaim space and defragment the database.

    Args:
        pool: Database pool (uses global pool if None).

    Returns:
        True if vacuum succeeded, False otherwise.
    """
    if pool is None:
        pool = get_database_pool()

    try:
        log_event(
            "DATABASE_VACUUM_STARTED",
            "Starting database VACUUM operation",
            source="persistence.database.run_vacuum",
        )
        start_time = datetime.now(timezone.utc)

        with pool.connection() as conn:
            conn.execute("VACUUM")

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_event(
            "DATABASE_VACUUM_COMPLETED",
            f"Database VACUUM completed in {duration_ms:.0f}ms",
            extra={"duration_ms": round(duration_ms, 2)},
            source="persistence.database.run_vacuum",
        )
        return True
    except Exception as e:
        log_event(
            "DATABASE_VACUUM_FAILED",
            f"Database VACUUM failed: {e}",
            extra={"error": str(e)},
            source="persistence.database.run_vacuum",
        )
        print(f"Failed to run database VACUUM: {e}", file=sys.stderr)
        return False


def run_analyze(pool: Optional[DatabasePool] = None) -> bool:
    """
    Run ANALYZE command to update query planner statistics.

    Args:
        pool: Database pool (uses global pool if None).

    Returns:
        True if analyze succeeded, False otherwise.
    """
    if pool is None:
        pool = get_database_pool()

    try:
        log_event(
            "DATABASE_ANALYZE_STARTED",
            "Starting database ANALYZE operation",
            source="persistence.database.run_analyze",
        )
        start_time = datetime.now(timezone.utc)

        with pool.connection() as conn:
            conn.execute("ANALYZE")

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_event(
            "DATABASE_ANALYZE_COMPLETED",
            f"Database ANALYZE completed in {duration_ms:.0f}ms",
            extra={"duration_ms": round(duration_ms, 2)},
            source="persistence.database.run_analyze",
        )
        return True
    except Exception as e:
        log_event(
            "DATABASE_ANALYZE_FAILED",
            f"Database ANALYZE failed: {e}",
            extra={"error": str(e)},
            source="persistence.database.run_analyze",
        )
        print(f"Failed to run database ANALYZE: {e}", file=sys.stderr)
        return False


def run_maintenance(pool: Optional[DatabasePool] = None, vacuum: bool = True, analyze: bool = True) -> dict:
    """
    Run database maintenance operations (VACUUM and/or ANALYZE).

    Args:
        pool: Database pool (uses global pool if None).
        vacuum: Whether to run VACUUM.
        analyze: Whether to run ANALYZE.

    Returns:
        Dict with results: {"vacuum": bool, "analyze": bool, "success": bool}
    """
    results = {"vacuum": None, "analyze": None, "success": True}

    if vacuum:
        results["vacuum"] = run_vacuum(pool)
        if not results["vacuum"]:
            results["success"] = False

    if analyze:
        results["analyze"] = run_analyze(pool)
        if not results["analyze"]:
            results["success"] = False

    return results


def get_database_size_info(pool: Optional[DatabasePool] = None) -> dict:
    """
    Get database size information and growth metrics.

    Args:
        pool: Database pool (uses global pool if None).

    Returns:
        Dict with size info: {
            "size_bytes": int,
            "size_mb": float,
            "page_count": int,
            "page_size": int,
            "table_sizes": dict
        }
    """
    if pool is None:
        pool = get_database_pool()

    try:
        with pool.connection() as conn:
            # Get overall database size
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            size_bytes = page_count * page_size
            size_mb = size_bytes / (1024 * 1024)

            # Get per-table sizes
            table_sizes = {}
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    table_sizes[table] = row_count
                except sqlite3.Error:
                    # Table might not be accessible
                    table_sizes[table] = None

            return {
                "size_bytes": size_bytes,
                "size_mb": round(size_mb, 2),
                "page_count": page_count,
                "page_size": page_size,
                "table_sizes": table_sizes,
            }
    except Exception as e:
        log_event(
            "DATABASE_SIZE_CHECK_FAILED",
            f"Failed to get database size: {e}",
            extra={"error": str(e)},
            source="persistence.database.get_database_size_info",
        )
        return {
            "size_bytes": 0,
            "size_mb": 0.0,
            "page_count": 0,
            "page_size": 0,
            "table_sizes": {},
        }


def check_database_growth(
    pool: Optional[DatabasePool] = None,
    warn_threshold_mb: float = 100.0,
    error_threshold_mb: float = 500.0
) -> dict:
    """
    Check database size and alert on unbounded growth.

    Args:
        pool: Database pool (uses global pool if None).
        warn_threshold_mb: Size in MB to trigger warning.
        error_threshold_mb: Size in MB to trigger error.

    Returns:
        Dict with: {"size_mb": float, "status": str, "alert": bool, "message": str}
    """
    size_info = get_database_size_info(pool)
    size_mb = size_info["size_mb"]

    status = "ok"
    alert = False
    message = f"Database size: {size_mb}MB"

    if size_mb >= error_threshold_mb:
        status = "error"
        alert = True
        message = f"Database size critical: {size_mb}MB (threshold: {error_threshold_mb}MB)"
        log_event(
            "DATABASE_SIZE_CRITICAL",
            message,
            extra={
                "size_mb": size_mb,
                "threshold_mb": error_threshold_mb,
                "table_sizes": size_info["table_sizes"],
            },
            source="persistence.database.check_database_growth",
        )
    elif size_mb >= warn_threshold_mb:
        status = "warning"
        alert = True
        message = f"Database size warning: {size_mb}MB (threshold: {warn_threshold_mb}MB)"
        log_event(
            "DATABASE_SIZE_WARNING",
            message,
            extra={
                "size_mb": size_mb,
                "threshold_mb": warn_threshold_mb,
                "table_sizes": size_info["table_sizes"],
            },
            source="persistence.database.check_database_growth",
        )

    return {
        "size_mb": size_mb,
        "status": status,
        "alert": alert,
        "message": message,
        "table_sizes": size_info["table_sizes"],
    }


# Required indexes for optimal query performance
REQUIRED_INDEXES = {
    "tickets": [
        ("idx_tickets_status", "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)"),
        ("idx_tickets_priority", "CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)"),
        ("idx_tickets_created", "CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at DESC)"),
        ("idx_tickets_status_priority", "CREATE INDEX IF NOT EXISTS idx_tickets_status_priority ON tickets(status, priority)"),
        ("idx_tickets_duplicate_guard", "CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_duplicate_guard ON tickets(duplicate_guard) WHERE duplicate_guard IS NOT NULL"),
    ],
    "event_log": [
        ("idx_event_log_timestamp", "CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp DESC)"),
        ("idx_event_log_type", "CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type)"),
        ("idx_event_log_ticket", "CREATE INDEX IF NOT EXISTS idx_event_log_ticket ON event_log(ticket_id) WHERE ticket_id IS NOT NULL"),
        ("idx_event_log_correlation", "CREATE INDEX IF NOT EXISTS idx_event_log_correlation ON event_log(correlation_id) WHERE correlation_id IS NOT NULL"),
    ],
    "agent_voice": [
        ("idx_agent_voice_timestamp", "CREATE INDEX IF NOT EXISTS idx_agent_voice_timestamp ON agent_voice(timestamp DESC)"),
        ("idx_agent_voice_agent", "CREATE INDEX IF NOT EXISTS idx_agent_voice_agent ON agent_voice(agent_id)"),
        ("idx_agent_voice_level", "CREATE INDEX IF NOT EXISTS idx_agent_voice_level ON agent_voice(level)"),
    ],
}


def verify_and_create_indexes(pool: Optional[DatabasePool] = None) -> dict:
    """
    Verify required indexes exist and create missing ones on startup.

    Args:
        pool: Database pool (uses global pool if None).

    Returns:
        Dict with: {"verified": int, "created": int, "failed": list}
    """
    if pool is None:
        pool = get_database_pool()

    verified = 0
    created = 0
    failed = []

    try:
        with pool.connection() as conn:
            # Get existing indexes
            cursor = conn.execute("""
                SELECT name, tbl_name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            existing = {row[0]: row[1] for row in cursor.fetchall()}

            # Check and create required indexes
            for table, indexes in REQUIRED_INDEXES.items():
                for idx_name, create_sql in indexes:
                    if idx_name in existing:
                        verified += 1
                    else:
                        try:
                            conn.execute(create_sql)
                            created += 1
                            log_event(
                                "INDEX_CREATED",
                                f"Created missing index: {idx_name} on {table}",
                                extra={"index": idx_name, "table": table},
                                source="persistence.database.verify_and_create_indexes",
                            )
                        except sqlite3.Error as e:
                            failed.append(f"{idx_name}: {e}")
                            log_event(
                                "INDEX_CREATE_FAILED",
                                f"Failed to create index {idx_name}: {e}",
                                extra={"index": idx_name, "table": table, "error": str(e)},
                                source="persistence.database.verify_and_create_indexes",
                            )

            conn.commit()

            if created > 0:
                log_event(
                    "INDEX_VERIFICATION_COMPLETE",
                    f"Index verification: {verified} verified, {created} created, {len(failed)} failed",
                    extra={"verified": verified, "created": created, "failed_count": len(failed)},
                    source="persistence.database.verify_and_create_indexes",
                )

    except Exception as e:
        log_event(
            "INDEX_VERIFICATION_ERROR",
            f"Index verification failed: {e}",
            extra={"error": str(e)},
            source="persistence.database.verify_and_create_indexes",
        )
        failed.append(f"verification_error: {e}")

    return {
        "verified": verified,
        "created": created,
        "failed": failed,
    }


def compact_json_encode(data: Union[dict, list, str], compress: bool = True) -> str:
    """
    Compact JSON encoding for large context fields.

    Removes whitespace and optionally compresses with zlib for storage efficiency.

    Args:
        data: Data to encode (dict, list, or already-encoded JSON string).
        compress: Whether to apply zlib compression (for data >1KB).

    Returns:
        Compact JSON string, optionally prefixed with 'z:' if compressed.
    """
    # Handle already-encoded JSON strings
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            compact_json = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        except json.JSONDecodeError:
            # Not valid JSON, return as-is
            return data
    else:
        compact_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    # Only compress if beneficial (>1KB and compression enabled)
    if compress and len(compact_json) > 1024:
        try:
            compressed = zlib.compress(compact_json.encode('utf-8'), level=6)
            # Only use compression if it actually saves space
            if len(compressed) < len(compact_json):
                encoded = base64.b64encode(compressed).decode('ascii')
                return f"z:{encoded}"
        except Exception:
            pass  # Fall through to uncompressed

    return compact_json


def compact_json_decode(encoded: str) -> Union[dict, list, str]:
    """
    Decode compact JSON, decompressing if needed.

    Args:
        encoded: Encoded string (may be prefixed with 'z:' if compressed).

    Returns:
        Decoded data (dict, list, or original string if not JSON).
    """
    if not encoded:
        return encoded

    # Handle compressed format
    if encoded.startswith("z:"):
        try:
            compressed = base64.b64decode(encoded[2:])
            decompressed = zlib.decompress(compressed).decode('utf-8')
            return json.loads(decompressed)
        except Exception:
            return encoded  # Return as-is if decompression fails

    # Handle regular compact JSON
    try:
        return json.loads(encoded)
    except json.JSONDecodeError:
        return encoded  # Not JSON, return as-is


def journal_state_change(
    table_name: str,
    operation: str,
    record_id: str,
    old_state: Optional[dict] = None,
    new_state: Optional[dict] = None,
    description: str = "",
    user_context: Optional[str] = None,
    pool: Optional[DatabasePool] = None,
) -> bool:
    """
    Journal critical state changes for auditability.

    Args:
        table_name: Table where change occurred.
        operation: Operation type (INSERT, UPDATE, DELETE).
        record_id: ID of affected record.
        old_state: Previous state (for UPDATE/DELETE).
        new_state: New state (for INSERT/UPDATE).
        description: Human-readable change description.
        user_context: User/agent making change.
        pool: Database pool (uses global pool if None).

    Returns:
        True if journaled successfully.
    """
    if pool is None:
        pool = get_database_pool()

    try:
        # Use compact encoding for state dicts
        old_values_json = compact_json_encode(old_state) if old_state else None
        new_values_json = compact_json_encode(new_state) if new_state else None

        with pool.transaction() as conn:
            conn.execute(
                """
                INSERT INTO database_audit_log (
                    table_name, operation, record_id, user_context,
                    old_values, new_values, change_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    table_name,
                    operation,
                    record_id,
                    user_context or "system",
                    old_values_json,
                    new_values_json,
                    description,
                )
            )

        log_event(
            "STATE_CHANGE_JOURNALED",
            f"Journaled {operation} on {table_name}: {record_id}",
            extra={
                "table": table_name,
                "operation": operation,
                "record_id": record_id,
                "description": description,
            },
            source="persistence.database.journal_state_change",
        )
        return True

    except Exception as e:
        log_event(
            "STATE_JOURNAL_FAILED",
            f"Failed to journal state change: {e}",
            extra={
                "table": table_name,
                "operation": operation,
                "record_id": record_id,
                "error": str(e),
            },
            source="persistence.database.journal_state_change",
        )
        return False


def get_state_change_history(
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    operation: Optional[str] = None,
    limit: int = 100,
    pool: Optional[DatabasePool] = None,
) -> List[Dict[str, Any]]:
    """
    Get state change history from audit log.

    Args:
        table_name: Filter by table (optional).
        record_id: Filter by record ID (optional).
        operation: Filter by operation type (optional).
        limit: Maximum records to return.
        pool: Database pool (uses global pool if None).

    Returns:
        List of audit log entries.
    """
    if pool is None:
        pool = get_database_pool()

    query = "SELECT * FROM database_audit_log WHERE 1=1"
    params = []

    if table_name:
        query += " AND table_name = ?"
        params.append(table_name)

    if record_id:
        query += " AND record_id = ?"
        params.append(record_id)

    if operation:
        query += " AND operation = ?"
        params.append(operation)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    try:
        with pool.connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []
