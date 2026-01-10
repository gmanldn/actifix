#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Persistence Queue Management

Provides fallback queues for reliability when primary storage fails.
Queues can be replayed when storage becomes available again.

Key Features:
- Atomic queue operations
- Deduplication support
- Automatic replay on recovery
- Queue size limits
- Entry expiration

Version: 1.0.0 (Generic)
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

from .atomic import atomic_write, safe_read


class QueueError(Exception):
    """Base exception for queue operations."""
    pass


@dataclass
class QueueEntry:
    """Entry in the persistence queue."""
    
    entry_id: str
    operation: str  # "write", "append", "update", "delete"
    key: str
    content: Any
    created_at: datetime
    retry_count: int = 0
    last_retry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'last_retry': self.last_retry.isoformat() if self.last_retry else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueEntry':
        """Create from dictionary."""
        return cls(
            entry_id=data['entry_id'],
            operation=data['operation'],
            key=data['key'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']),
            retry_count=data.get('retry_count', 0),
            last_retry=datetime.fromisoformat(data['last_retry']) if data.get('last_retry') else None,
            metadata=data.get('metadata', {}),
        )


class PersistenceQueue:
    """
    Persistence queue for reliability.
    
    When primary storage fails, operations are queued for later replay.
    """
    
    def __init__(
        self,
        queue_file: Path,
        max_entries: int = 1000,
        max_age_hours: float = 24.0,
        deduplication: bool = True,
    ):
        """
        Initialize persistence queue.
        
        Args:
            queue_file: Path to queue file (JSON)
            max_entries: Maximum entries in queue
            max_age_hours: Maximum age of entries (auto-pruned)
            deduplication: Enable deduplication based on key
        """
        self.queue_file = Path(queue_file)
        self.max_entries = max_entries
        self.max_age_hours = max_age_hours
        self.deduplication = deduplication
        self._entries: List[QueueEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load queue from disk."""
        content = safe_read(self.queue_file, default="[]")
        try:
            data = json.loads(content)
            self._entries = [QueueEntry.from_dict(e) for e in data]
            self._prune_old_entries()
        except (json.JSONDecodeError, KeyError, ValueError):
            # Queue file corrupted, start fresh
            self._entries = []
    
    def _save(self) -> None:
        """Save queue to disk atomically."""
        data = [e.to_dict() for e in self._entries]
        content = json.dumps(data, indent=2, default=str)
        atomic_write(self.queue_file, content)
    
    def _prune_old_entries(self) -> None:
        """Remove entries older than max_age_hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        self._entries = [
            e for e in self._entries
            if e.created_at > cutoff
        ]
    
    def _generate_entry_id(self, operation: str, key: str) -> str:
        """Generate unique entry ID."""
        data = f"{operation}:{key}:{datetime.now(timezone.utc).isoformat()}"
        hash_suffix = hashlib.sha256(data.encode()).hexdigest()[:8]
        return f"QE-{hash_suffix.upper()}"
    
    def enqueue(
        self,
        operation: str,
        key: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add entry to queue.
        
        Args:
            operation: Operation type ("write", "append", "update", "delete")
            key: Storage key
            content: Content to persist
            metadata: Optional metadata
            
        Returns:
            Entry ID
            
        Raises:
            QueueError: If queue is full or invalid operation
        """
        if operation not in {"write", "append", "update", "delete"}:
            raise QueueError(f"Invalid operation: {operation}")
        
        # Check for duplicates
        if self.deduplication:
            for entry in self._entries:
                if entry.key == key and entry.operation == operation:
                    # Update existing entry instead of adding duplicate
                    entry.content = content
                    entry.metadata = metadata or {}
                    entry.last_retry = datetime.now(timezone.utc)
                    self._save()
                    return entry.entry_id
        
        # Check queue size limit
        if len(self._entries) >= self.max_entries:
            # Remove oldest entry
            self._entries.pop(0)
        
        # Create new entry
        entry = QueueEntry(
            entry_id=self._generate_entry_id(operation, key),
            operation=operation,
            key=key,
            content=content,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        
        self._entries.append(entry)
        self._save()
        
        return entry.entry_id
    
    def dequeue(self, entry_id: str) -> Optional[QueueEntry]:
        """
        Remove and return entry by ID.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            QueueEntry if found, None otherwise
        """
        for i, entry in enumerate(self._entries):
            if entry.entry_id == entry_id:
                self._entries.pop(i)
                self._save()
                return entry
        return None
    
    def peek(self, count: int = 1) -> List[QueueEntry]:
        """
        Get entries without removing them.
        
        Args:
            count: Number of entries to peek
            
        Returns:
            List of entries (oldest first)
        """
        return self._entries[:count]
    
    def replay(
        self,
        operation_handler: Callable[[QueueEntry], bool],
        max_retries: int = 3,
    ) -> Dict[str, int]:
        """
        Replay all queued operations.
        
        Args:
            operation_handler: Function that processes an entry and returns True on success
            max_retries: Maximum retry attempts per entry
            
        Returns:
            Dict with replay statistics (succeeded, failed, skipped)
        """
        stats = {"succeeded": 0, "failed": 0, "skipped": 0}
        failed_entries = []
        
        for entry in list(self._entries):
            # Skip entries that exceeded retry limit
            if entry.retry_count >= max_retries:
                stats["skipped"] += 1
                failed_entries.append(entry)
                continue
            
            # Attempt operation
            try:
                success = operation_handler(entry)
                if success:
                    stats["succeeded"] += 1
                else:
                    # Update retry count
                    entry.retry_count += 1
                    entry.last_retry = datetime.now(timezone.utc)
                    stats["failed"] += 1
                    failed_entries.append(entry)
            except Exception:
                # Update retry count
                entry.retry_count += 1
                entry.last_retry = datetime.now(timezone.utc)
                stats["failed"] += 1
                failed_entries.append(entry)
        
        # Update queue with only failed entries
        self._entries = failed_entries
        self._save()
        
        return stats
    
    def clear(self) -> int:
        """
        Clear all entries from queue.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._entries)
        self._entries.clear()
        self._save()
        return count
    
    def size(self) -> int:
        """Get number of entries in queue."""
        return len(self._entries)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._entries) == 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dict with queue stats
        """
        if not self._entries:
            return {
                "size": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "operations": {},
                "avg_retry_count": 0.0,
            }
        
        # Count operations
        ops = {}
        total_retries = 0
        for entry in self._entries:
            ops[entry.operation] = ops.get(entry.operation, 0) + 1
            total_retries += entry.retry_count
        
        return {
            "size": len(self._entries),
            "oldest_entry": self._entries[0].created_at.isoformat(),
            "newest_entry": self._entries[-1].created_at.isoformat(),
            "operations": ops,
            "avg_retry_count": total_retries / len(self._entries),
        }
