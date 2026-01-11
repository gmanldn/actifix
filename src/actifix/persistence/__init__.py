#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generic Persistence Layer Framework

A production-ready persistence layer extracted from sophisticated error tracking systems.
Provides atomic operations, fallback queues, health monitoring, and multiple storage backends.

Key Features:
- Atomic file operations with fsync for durability
- Fallback queues for reliability when primary storage fails
- Storage health monitoring and corruption detection
- Multiple storage backends (file, memory)
- Transaction support with rollback
- Configurable paths and limits
- Thread-safe operations

Usage:
    from actifix.persistence import PersistenceManager, FileStorageBackend
    
    manager = PersistenceManager(
        backend=FileStorageBackend(base_dir="/path/to/data")
    )
    
    # Write document
    manager.write_document("config.json", {"key": "value"})
    
    # Read document
    data = manager.read_document("config.json")
    
    # Append to document
    manager.append_to_document("log.txt", "New log entry\n")

Version: 1.0.0 (Generic)
"""

from .atomic import (
    atomic_write,
    atomic_write_bytes,
    atomic_append,
    atomic_update,
    trim_to_line_boundary,
)

from .storage import (
    StorageBackend,
    FileStorageBackend,
    MemoryStorageBackend,
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
)

from .queue import (
    PersistenceQueue,
    QueueEntry,
    QueueError,
)

from .paths import (
    StoragePaths,
    configure_storage_paths,
    get_storage_paths,
)

from .manager import (
    PersistenceManager,
    Transaction,
)

from .health import (
    HealthStatus,
    check_storage_health,
    detect_corruption,
)

from .database import (
    DatabasePool,
    DatabaseConfig,
    DatabaseError,
    DatabaseConnectionError,
    DatabaseSchemaError,
    get_database_pool,
    reset_database_pool,
)

from .ticket_repo import (
    TicketRepository,
    TicketFilter,
    TicketLock,
    get_ticket_repository,
    reset_ticket_repository,
)

__version__ = "1.0.0"

__all__ = [
    # Atomic operations
    "atomic_write",
    "atomic_write_bytes",
    "atomic_append",
    "atomic_update",
    "trim_to_line_boundary",
    
    # Storage backends
    "StorageBackend",
    "FileStorageBackend",
    "MemoryStorageBackend",
    "StorageError",
    "StorageNotFoundError",
    "StoragePermissionError",
    
    # Queue management
    "PersistenceQueue",
    "QueueEntry",
    "QueueError",
    
    # Path configuration
    "StoragePaths",
    "configure_storage_paths",
    "get_storage_paths",
    
    # Manager
    "PersistenceManager",
    "Transaction",
    
    # Health monitoring
    "HealthStatus",
    "check_storage_health",
    "detect_corruption",
    
    # Database
    "DatabasePool",
    "DatabaseConfig",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseSchemaError",
    "get_database_pool",
    "reset_database_pool",
    
    # Ticket Repository
    "TicketRepository",
    "TicketFilter",
    "TicketLock",
    "get_ticket_repository",
    "reset_ticket_repository",
]
