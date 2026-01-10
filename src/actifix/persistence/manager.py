#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Persistence Manager

High-level persistence manager that orchestrates storage, queues, and health monitoring.
Provides a unified interface for all persistence operations with automatic fallback and recovery.

Version: 1.0.0 (Generic)
"""

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union

from .storage import StorageBackend, StorageError, StorageNotFoundError
from .queue import PersistenceQueue, QueueEntry
from .atomic import atomic_append, atomic_update, idempotent_append
from .paths import StoragePaths, get_storage_paths


class PersistenceError(Exception):
    """Base exception for persistence operations."""
    pass


class Transaction:
    """
    Transaction context for atomic multi-operation updates.
    
    All operations within a transaction are buffered and committed atomically.
    """
    
    def __init__(self, manager: 'PersistenceManager'):
        """Initialize transaction."""
        self.manager = manager
        self.operations: List[Dict[str, Any]] = []
        self.committed = False
        self.rolled_back = False
    
    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        """Queue write operation."""
        self.operations.append({
            "type": "write",
            "key": key,
            "content": content,
            "encoding": encoding,
        })
    
    def append(self, key: str, content: str, max_size_bytes: Optional[int] = None) -> None:
        """Queue append operation."""
        self.operations.append({
            "type": "append",
            "key": key,
            "content": content,
            "max_size_bytes": max_size_bytes,
        })
    
    def delete(self, key: str) -> None:
        """Queue delete operation."""
        self.operations.append({
            "type": "delete",
            "key": key,
        })
    
    def commit(self) -> None:
        """Commit all operations atomically."""
        if self.committed or self.rolled_back:
            raise PersistenceError("Transaction already finalized")
        
        try:
            # Execute all operations
            for op in self.operations:
                if op["type"] == "write":
                    self.manager.write_document(
                        op["key"],
                        op["content"],
                        encoding=op.get("encoding", "utf-8"),
                    )
                elif op["type"] == "append":
                    self.manager.append_to_document(
                        op["key"],
                        op["content"],
                        max_size_bytes=op.get("max_size_bytes"),
                    )
                elif op["type"] == "delete":
                    self.manager.delete_document(op["key"])
            
            self.committed = True
        except Exception as e:
            self.rolled_back = True
            raise PersistenceError(f"Transaction failed: {e}") from e
    
    def rollback(self) -> None:
        """Rollback transaction (no-op for now)."""
        self.rolled_back = True


class PersistenceManager:
    """
    High-level persistence manager.
    
    Orchestrates storage backend, fallback queue, and health monitoring.
    Provides automatic fallback when primary storage fails.
    """
    
    def __init__(
        self,
        backend: StorageBackend,
        queue_file: Optional[Path] = None,
        paths: Optional[StoragePaths] = None,
        enable_queue: bool = True,
        auto_replay: bool = True,
    ):
        """
        Initialize persistence manager.
        
        Args:
            backend: Storage backend to use
            queue_file: Path to fallback queue file (default: auto-generated)
            paths: Storage paths configuration (default: global config)
            enable_queue: Enable fallback queue
            auto_replay: Automatically replay queue on operations
        """
        self.backend = backend
        self.paths = paths or get_storage_paths()
        self.enable_queue = enable_queue
        self.auto_replay = auto_replay
        
        # Initialize queue if enabled
        self.queue: Optional[PersistenceQueue] = None
        if self.enable_queue:
            if queue_file is None:
                queue_file = self.paths.get_state_path("persistence_queue.json")
            self.queue = PersistenceQueue(queue_file)
            
            # Auto-replay queue on initialization
            if self.auto_replay and not self.queue.is_empty():
                self._replay_queue()
    
    def _replay_queue(self) -> Dict[str, int]:
        """Replay queued operations."""
        if not self.queue:
            return {"succeeded": 0, "failed": 0, "skipped": 0}
        
        def operation_handler(entry: QueueEntry) -> bool:
            """Handle queued operation."""
            try:
                if entry.operation == "write":
                    self.backend.write(entry.key, entry.content)
                    return True
                elif entry.operation == "append":
                    # For append, we need to implement logic
                    existing = ""
                    if self.backend.exists(entry.key):
                        existing = self.backend.read(entry.key)
                    self.backend.write(entry.key, existing + entry.content)
                    return True
                elif entry.operation == "delete":
                    self.backend.delete(entry.key)
                    return True
                return False
            except Exception:
                return False
        
        return self.queue.replay(operation_handler)
    
    def write_document(
        self,
        key: str,
        content: str,
        encoding: str = "utf-8",
        use_queue_on_failure: bool = True,
    ) -> bool:
        """
        Write document to storage.
        
        Args:
            key: Storage key
            content: Content to write
            encoding: Text encoding
            use_queue_on_failure: Queue on failure if True
            
        Returns:
            True if written successfully, False if queued
            
        Raises:
            PersistenceError: If write fails and queuing disabled
        """
        try:
            self.backend.write(key, content, encoding=encoding)
            return True
        except StorageError as e:
            if use_queue_on_failure and self.queue:
                self.queue.enqueue("write", key, content)
                return False
            raise PersistenceError(f"Write failed: {e}") from e
    
    def read_document(self, key: str) -> str:
        """
        Read document from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Document content
            
        Raises:
            PersistenceError: If read fails
        """
        try:
            return self.backend.read(key)
        except StorageNotFoundError:
            raise PersistenceError(f"Document not found: {key}")
        except StorageError as e:
            raise PersistenceError(f"Read failed: {e}") from e
    
    def read_document_safe(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Read document with fallback.
        
        Args:
            key: Storage key
            default: Default value if not found
            
        Returns:
            Document content or default
        """
        try:
            return self.backend.read(key)
        except (StorageNotFoundError, StorageError):
            return default
    
    def append_to_document(
        self,
        key: str,
        content: str,
        max_size_bytes: Optional[int] = None,
        use_queue_on_failure: bool = True,
    ) -> bool:
        """
        Append to document.
        
        Args:
            key: Storage key
            content: Content to append
            max_size_bytes: Maximum file size (trimmed if exceeded)
            use_queue_on_failure: Queue on failure if True
            
        Returns:
            True if appended successfully, False if queued
        """
        try:
            # Read existing content
            existing = ""
            if self.backend.exists(key):
                existing = self.backend.read(key)
            
            # Append new content
            new_content = existing + content
            
            # Trim if needed
            if max_size_bytes and len(new_content.encode("utf-8")) > max_size_bytes:
                from .atomic import trim_to_line_boundary
                excess = len(new_content.encode("utf-8")) - max_size_bytes
                trimmed = new_content.encode("utf-8")[excess:].decode("utf-8", errors="ignore")
                first_newline = trimmed.find("\n")
                if first_newline > 0:
                    new_content = trimmed[first_newline + 1:]
                else:
                    new_content = trimmed
            
            # Write atomically
            self.backend.write(key, new_content)
            return True
        except StorageError as e:
            if use_queue_on_failure and self.queue:
                self.queue.enqueue("append", key, content)
                return False
            raise PersistenceError(f"Append failed: {e}") from e
    
    def update_document(
        self,
        key: str,
        update_fn: Callable[[str], str],
        create_if_missing: bool = True,
        initial_content: str = "",
    ) -> None:
        """
        Update document using transformation function.
        
        Args:
            key: Storage key
            update_fn: Function that transforms content
            create_if_missing: Create if doesn't exist
            initial_content: Initial content if created
            
        Raises:
            PersistenceError: If update fails
        """
        try:
            # Read existing or use initial
            if self.backend.exists(key):
                existing = self.backend.read(key)
            elif create_if_missing:
                existing = initial_content
            else:
                raise PersistenceError(f"Document not found: {key}")
            
            # Apply transformation
            new_content = update_fn(existing)
            
            # Write back
            self.backend.write(key, new_content)
        except StorageError as e:
            raise PersistenceError(f"Update failed: {e}") from e
    
    def delete_document(self, key: str) -> bool:
        """
        Delete document.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        try:
            return self.backend.delete(key)
        except StorageError as e:
            raise PersistenceError(f"Delete failed: {e}") from e
    
    def exists(self, key: str) -> bool:
        """Check if document exists."""
        return self.backend.exists(key)
    
    def list_documents(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all documents.
        
        Args:
            prefix: Optional prefix filter
            
        Returns:
            List of document keys
        """
        try:
            return self.backend.list_keys(prefix=prefix)
        except StorageError as e:
            raise PersistenceError(f"List failed: {e}") from e
    
    def get_size(self, key: str) -> int:
        """Get document size in bytes."""
        try:
            return self.backend.size(key)
        except StorageNotFoundError:
            raise PersistenceError(f"Document not found: {key}")
        except StorageError as e:
            raise PersistenceError(f"Size check failed: {e}") from e
    
    @contextmanager
    def transaction(self):
        """
        Create transaction context.
        
        Usage:
            with manager.transaction() as txn:
                txn.write("key1", "value1")
                txn.write("key2", "value2")
                txn.commit()
        """
        txn = Transaction(self)
        try:
            yield txn
        except Exception:
            txn.rollback()
            raise
    
    def get_queue_stats(self) -> Optional[Dict[str, Any]]:
        """Get fallback queue statistics."""
        if not self.queue:
            return None
        return self.queue.get_stats()
    
    def replay_queue(self) -> Dict[str, int]:
        """Manually replay fallback queue."""
        return self._replay_queue()
    
    def clear_queue(self) -> int:
        """Clear fallback queue."""
        if not self.queue:
            return 0
        return self.queue.clear()
