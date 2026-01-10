#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Storage Backends

Abstract storage interface and concrete implementations for different storage types.
Provides a consistent API for reading, writing, and managing persistent data.

Supported Backends:
- FileStorageBackend: File-based storage with atomic operations
- MemoryStorageBackend: In-memory storage for testing

Version: 1.0.0 (Generic)
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .atomic import atomic_write, atomic_write_bytes, safe_read, safe_read_bytes


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when requested resource not found."""
    pass


class StoragePermissionError(StorageError):
    """Raised when permission denied."""
    pass


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    
    Implementations must provide thread-safe operations.
    """
    
    @abstractmethod
    def read(self, key: str) -> str:
        """
        Read text content by key.
        
        Args:
            key: Storage key (e.g., file path, document ID)
            
        Returns:
            Content as string
            
        Raises:
            StorageNotFoundError: If key not found
            StorageError: On other errors
        """
        pass
    
    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        """
        Read binary content by key.
        
        Args:
            key: Storage key
            
        Returns:
            Content as bytes
            
        Raises:
            StorageNotFoundError: If key not found
            StorageError: On other errors
        """
        pass
    
    @abstractmethod
    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        """
        Write text content.
        
        Args:
            key: Storage key
            content: Content to write
            encoding: Text encoding
            
        Raises:
            StoragePermissionError: If write not allowed
            StorageError: On other errors
        """
        pass
    
    @abstractmethod
    def write_bytes(self, key: str, content: bytes) -> None:
        """
        Write binary content.
        
        Args:
            key: Storage key
            content: Content to write
            
        Raises:
            StoragePermissionError: If write not allowed
            StorageError: On other errors
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete content by key.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StoragePermissionError: If delete not allowed
            StorageError: On other errors
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys, optionally filtered by prefix.
        
        Args:
            prefix: Optional key prefix to filter by
            
        Returns:
            List of keys
        """
        pass
    
    @abstractmethod
    def size(self, key: str) -> int:
        """
        Get size of content in bytes.
        
        Args:
            key: Storage key
            
        Returns:
            Size in bytes
            
        Raises:
            StorageNotFoundError: If key not found
        """
        pass


class FileStorageBackend(StorageBackend):
    """
    File-based storage backend with atomic operations.
    
    Uses atomic writes to ensure data integrity.
    Keys are treated as relative file paths from base_dir.
    """
    
    def __init__(self, base_dir: Union[str, Path], encoding: str = "utf-8"):
        """
        Initialize file storage backend.
        
        Args:
            base_dir: Base directory for storage
            encoding: Default text encoding
        """
        self.base_dir = Path(base_dir)
        self.encoding = encoding
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str) -> Path:
        """Get absolute path for key."""
        # Normalize key to prevent directory traversal
        key = key.lstrip("/").replace("..", "")
        return self.base_dir / key
    
    def read(self, key: str) -> str:
        """Read text content."""
        path = self._get_path(key)
        if not path.exists():
            raise StorageNotFoundError(f"Key not found: {key}")
        
        try:
            return path.read_text(encoding=self.encoding)
        except PermissionError as e:
            raise StoragePermissionError(f"Permission denied: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to read {key}: {e}") from e
    
    def read_bytes(self, key: str) -> bytes:
        """Read binary content."""
        path = self._get_path(key)
        if not path.exists():
            raise StorageNotFoundError(f"Key not found: {key}")
        
        try:
            return path.read_bytes()
        except PermissionError as e:
            raise StoragePermissionError(f"Permission denied: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to read {key}: {e}") from e
    
    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        """Write text content atomically."""
        path = self._get_path(key)
        try:
            atomic_write(path, content, encoding=encoding or self.encoding)
        except PermissionError as e:
            raise StoragePermissionError(f"Permission denied: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to write {key}: {e}") from e
    
    def write_bytes(self, key: str, content: bytes) -> None:
        """Write binary content atomically."""
        path = self._get_path(key)
        try:
            atomic_write_bytes(path, content)
        except PermissionError as e:
            raise StoragePermissionError(f"Permission denied: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to write {key}: {e}") from e
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self._get_path(key).exists()
    
    def delete(self, key: str) -> bool:
        """Delete file."""
        path = self._get_path(key)
        if not path.exists():
            return False
        
        try:
            path.unlink()
            return True
        except PermissionError as e:
            raise StoragePermissionError(f"Permission denied: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to delete {key}: {e}") from e
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all files, optionally filtered by prefix."""
        keys = []
        
        try:
            for path in self.base_dir.rglob("*"):
                if path.is_file():
                    # Get relative path from base_dir
                    rel_path = path.relative_to(self.base_dir)
                    key = str(rel_path)
                    
                    if prefix is None or key.startswith(prefix):
                        keys.append(key)
        except Exception as e:
            raise StorageError(f"Failed to list keys: {e}") from e
        
        return sorted(keys)
    
    def size(self, key: str) -> int:
        """Get file size."""
        path = self._get_path(key)
        if not path.exists():
            raise StorageNotFoundError(f"Key not found: {key}")
        
        try:
            return path.stat().st_size
        except Exception as e:
            raise StorageError(f"Failed to get size of {key}: {e}") from e


class MemoryStorageBackend(StorageBackend):
    """
    In-memory storage backend for testing.
    
    Data is stored in memory and lost on restart.
    Thread-safe for single-threaded tests (use locks for multi-threaded).
    """
    
    def __init__(self):
        """Initialize memory storage."""
        self._data: Dict[str, bytes] = {}
    
    def read(self, key: str) -> str:
        """Read text content."""
        if key not in self._data:
            raise StorageNotFoundError(f"Key not found: {key}")
        return self._data[key].decode("utf-8")
    
    def read_bytes(self, key: str) -> bytes:
        """Read binary content."""
        if key not in self._data:
            raise StorageNotFoundError(f"Key not found: {key}")
        return self._data[key]
    
    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        """Write text content."""
        self._data[key] = content.encode(encoding)
    
    def write_bytes(self, key: str, content: bytes) -> None:
        """Write binary content."""
        self._data[key] = content
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data
    
    def delete(self, key: str) -> bool:
        """Delete content."""
        if key not in self._data:
            return False
        del self._data[key]
        return True
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys."""
        if prefix is None:
            return sorted(self._data.keys())
        return sorted(k for k in self._data.keys() if k.startswith(prefix))
    
    def size(self, key: str) -> int:
        """Get content size."""
        if key not in self._data:
            raise StorageNotFoundError(f"Key not found: {key}")
        return len(self._data[key])
    
    def clear(self) -> None:
        """Clear all data (useful for testing)."""
        self._data.clear()


class JSONStorageMixin:
    """
    Mixin to add JSON serialization support to any storage backend.
    
    Usage:
        class MyBackend(JSONStorageMixin, FileStorageBackend):
            pass
    """
    
    def read_json(self, key: str) -> Any:
        """
        Read and deserialize JSON content.
        
        Args:
            key: Storage key
            
        Returns:
            Deserialized Python object
        """
        content = self.read(key)  # type: ignore
        return json.loads(content)
    
    def write_json(self, key: str, obj: Any, indent: Optional[int] = 2) -> None:
        """
        Serialize and write JSON content.
        
        Args:
            key: Storage key
            obj: Python object to serialize
            indent: JSON indentation (None for compact)
        """
        content = json.dumps(obj, indent=indent, default=str)
        self.write(key, content)  # type: ignore
