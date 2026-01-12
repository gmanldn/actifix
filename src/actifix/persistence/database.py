#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Backend for Actifix Tickets

SQLite-based storage with ACID compliance, row-level locking, and indexing.
Provides thread-safe connection pooling and automatic schema migrations.

Version: 1.0.0
"""

import atexit
import contextlib
import os
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator

# Schema version for migrations
SCHEMA_VERSION = 2

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
    format_version TEXT DEFAULT '1.0',
    
    -- Checklist fields
    documented BOOLEAN DEFAULT 0,
    functioning BOOLEAN DEFAULT 0,
    tested BOOLEAN DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    
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
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                # Ensure database directory exists
                self.config.db_path.parent.mkdir(parents=True, exist_ok=True)
                
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
                
                self._local.connection = conn
                
                # Initialize schema if this is first connection
                if not self._initialized:
                    with self._lock:
                        if not self._initialized:
                            self._initialize_schema(conn)
                            self._initialized = True
                
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
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager for transactions.
        
        Automatically commits on success, rolls back on error.
        
        Yields:
            Database connection.
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def close(self) -> None:
        """Close connection for current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
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
    
    with _pool_lock:
        if _global_pool is None or _global_pool.config.db_path != db_path:
            config = DatabaseConfig(db_path=db_path)
            _global_pool = DatabasePool(config)
        
        return _global_pool


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
