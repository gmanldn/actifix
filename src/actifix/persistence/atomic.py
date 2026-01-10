#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atomic File Operations

Provides atomic file operations with fsync for durability.
Ensures files are never left in a corrupted or partial state.

All operations use the temp-write-then-rename pattern for atomicity,
and fsync for durability guarantees.

Version: 1.0.0 (Generic)
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Callable


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write content to file atomically using temp+rename pattern.
    
    This ensures that the file is never in a partial/corrupt state.
    Uses fsync for durability.
    
    Args:
        path: Target file path.
        content: Content to write.
        encoding: Text encoding (default: utf-8).
        
    Raises:
        OSError: If write fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file in same directory (for same-filesystem rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )
    
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.replace(tmp_path, path)
        
        # Sync directory for durability
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, AttributeError):
            # Directory sync not supported on all platforms
            pass
            
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """
    Write bytes to file atomically.
    
    Args:
        path: Target file path.
        content: Bytes content to write.
        
    Raises:
        OSError: If write fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )
    
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(tmp_path, path)
        
        # Sync directory for durability
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, AttributeError):
            pass
            
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def trim_to_line_boundary(content: str, max_bytes: int) -> str:
    """
    Trim content to a maximum size at a line boundary.
    
    Ensures we never split in the middle of a line, which could
    corrupt log entries or structured documents.
    
    Args:
        content: Content to trim.
        max_bytes: Maximum size in bytes.
    
    Returns:
        Trimmed content ending at a line boundary.
    """
    encoded = content.encode("utf-8")
    if len(encoded) <= max_bytes:
        return content
    
    # Truncate and find last newline
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    last_newline = truncated.rfind("\n")
    
    if last_newline > 0:
        return truncated[:last_newline + 1]
    return truncated


def atomic_append(
    path: Path,
    content: str,
    max_size_bytes: Optional[int] = None,
    encoding: str = "utf-8",
) -> None:
    """
    Append content to file atomically with optional size limit.
    
    If file exceeds max size after append, trims from the beginning
    at line boundaries to maintain the most recent content.
    
    Args:
        path: Target file path.
        content: Content to append.
        max_size_bytes: Maximum file size in bytes (None = unlimited).
        encoding: Text encoding.
        
    Raises:
        OSError: If operation fails.
    """
    path = Path(path)
    
    # Read existing content
    existing = ""
    if path.exists():
        existing = path.read_text(encoding=encoding)
    
    # Append new content
    new_content = existing + content
    
    # Trim if needed
    if max_size_bytes and len(new_content.encode(encoding)) > max_size_bytes:
        # Keep the newer content (end of file)
        excess = len(new_content.encode(encoding)) - max_size_bytes
        # Find line boundary after excess
        trimmed = new_content.encode(encoding)[excess:].decode(encoding, errors="ignore")
        first_newline = trimmed.find("\n")
        if first_newline > 0:
            new_content = trimmed[first_newline + 1:]
        else:
            new_content = trimmed
    
    atomic_write(path, new_content, encoding)


def atomic_update(
    path: Path,
    update_fn: Callable[[str], str],
    encoding: str = "utf-8",
    create_if_missing: bool = True,
    initial_content: str = "",
) -> None:
    """
    Update file content atomically using a transformation function.
    
    Reads current content, applies transformation, writes atomically.
    Useful for structured updates like replacing sections.
    
    Args:
        path: Target file path.
        update_fn: Function that takes current content and returns new content.
        encoding: Text encoding.
        create_if_missing: Create file if it doesn't exist.
        initial_content: Initial content if file doesn't exist.
        
    Raises:
        OSError: If operation fails.
        FileNotFoundError: If file doesn't exist and create_if_missing=False.
    """
    path = Path(path)
    
    # Read existing content
    if path.exists():
        existing = path.read_text(encoding=encoding)
    elif create_if_missing:
        existing = initial_content
    else:
        raise FileNotFoundError(f"File not found: {path}")
    
    # Apply transformation
    new_content = update_fn(existing)
    
    # Write atomically
    atomic_write(path, new_content, encoding)


def idempotent_append(
    path: Path,
    content: str,
    entry_key: str,
    encoding: str = "utf-8",
) -> bool:
    """
    Append content only if entry_key not already present.
    
    Prevents duplicate entries in logs or lists.
    
    Args:
        path: Target file path.
        content: Content to append.
        entry_key: Unique key to check for duplicates.
        encoding: Text encoding.
    
    Returns:
        True if content was appended, False if duplicate.
        
    Raises:
        OSError: If operation fails.
    """
    path = Path(path)
    
    existing = ""
    if path.exists():
        existing = path.read_text(encoding=encoding)
    
    if entry_key in existing:
        return False
    
    atomic_write(path, existing + content, encoding)
    return True


def safe_read(
    path: Path,
    encoding: str = "utf-8",
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Safely read file with fallback.
    
    Args:
        path: File path to read.
        encoding: Text encoding.
        default: Default value if file doesn't exist or read fails.
    
    Returns:
        File content or default value.
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except (FileNotFoundError, OSError):
        return default


def safe_read_bytes(
    path: Path,
    default: Optional[bytes] = None,
) -> Optional[bytes]:
    """
    Safely read binary file with fallback.
    
    Args:
        path: File path to read.
        default: Default value if file doesn't exist or read fails.
    
    Returns:
        File content or default value.
    """
    try:
        return Path(path).read_bytes()
    except (FileNotFoundError, OSError):
        return default
