"""
Actifix Log Utilities - Atomic writes and safe file operations.

Provides durable, atomic file operations to prevent corruption.
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write content to file atomically using temp+rename pattern.
    
    This ensures that the file is never in a partial/corrupt state.
    Uses fsync for durability.
    
    Args:
        path: Target file path.
        content: Content to write.
        encoding: Text encoding (default: utf-8).
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
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
            
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
    corrupt log entries or ticket blocks.
    
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


def append_with_guard(
    path: Path,
    content: str,
    max_size_bytes: int = 10 * 1024 * 1024,  # 10MB default
    encoding: str = "utf-8",
) -> None:
    """
    Append content to file with size limit enforcement.
    
    If file exceeds max size after append, trims from the beginning
    at line boundaries.
    
    Args:
        path: Target file path.
        content: Content to append.
        max_size_bytes: Maximum file size in bytes.
        encoding: Text encoding.
    """
    path = Path(path)
    
    # Read existing content
    existing = ""
    if path.exists():
        existing = path.read_text(encoding=encoding)
    
    # Append new content
    new_content = existing + content
    
    # Trim if needed
    if len(new_content.encode(encoding)) > max_size_bytes:
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


def idempotent_append(
    path: Path,
    content: str,
    entry_key: str,
    encoding: str = "utf-8",
) -> bool:
    """
    Append content only if entry_key not already present.
    
    Prevents duplicate log entries.
    
    Args:
        path: Target file path.
        content: Content to append.
        entry_key: Unique key to check for duplicates.
        encoding: Text encoding.
    
    Returns:
        True if content was appended, False if duplicate.
    """
    path = Path(path)
    
    existing = ""
    if path.exists():
        existing = path.read_text(encoding=encoding)
    
    if entry_key in existing:
        return False
    
    atomic_write(path, existing + content, encoding)
    return True


def log_event(
    path: Path,
    event_type: str,
    message: str,
    ticket_id: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """
    Log a structured event to AFLog.
    
    Format: TIMESTAMP | EVENT_TYPE | TICKET_ID | MESSAGE | EXTRA
    
    Args:
        path: AFLog file path.
        event_type: Type of event (e.g., TICKET_CREATED, DISPATCH_STARTED).
        message: Human-readable message.
        ticket_id: Optional ticket ID.
        extra: Optional extra data.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    ticket_str = ticket_id or "-"
    extra_str = str(extra) if extra else "-"
    
    line = f"{timestamp} | {event_type} | {ticket_str} | {message} | {extra_str}\n"
    
    append_with_guard(path, line)