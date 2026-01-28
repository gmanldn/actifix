"""
Actifix Log Utilities - Atomic writes and safe file operations.

Provides durable, atomic file operations to prevent corruption.
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_ROTATION_THRESHOLD_BYTES = int(
    os.getenv("ACTIFIX_LOG_ROTATION_THRESHOLD_BYTES", str(8 * 1024 * 1024))
)
LOG_ROTATION_KEEP_FILES = int(os.getenv("ACTIFIX_LOG_ROTATION_KEEP_FILES", "3"))


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


def _rotate_log_file(path: Path, threshold: int, keep: int) -> None:
    """Rotate the log file when it exceeds the configured threshold."""
    if keep <= 0:
        return
    path = Path(path)
    if not path.exists():
        return

    try:
        if path.stat().st_size < threshold:
            return
    except OSError:
        return

    try:
        for idx in range(keep - 1, 0, -1):
            src = path.with_name(f"{path.name}.{idx}")
            dst = path.with_name(f"{path.name}.{idx + 1}")
            if dst.exists():
                dst.unlink()
            if src.exists():
                src.replace(dst)

        rotated = path.with_name(f"{path.name}.1")
        if rotated.exists():
            rotated.unlink()
        path.replace(rotated)
        path.touch()
    except OSError:
        # Rotation failure should not block logging
        return


def append_with_guard(
    path: Path,
    content: str,
    max_size_bytes: Optional[int] = None,
    encoding: str = "utf-8",
) -> None:
    """
    Append content to file with size limit enforcement.

    If file exceeds max size after append, trims from the beginning
    at line boundaries.

    Args:
        path: Target file path.
        content: Content to append.
        max_size_bytes: Maximum file size in bytes. Defaults to config.max_log_size_bytes.
        encoding: Text encoding.
    """
    path = Path(path)

    # Use config default if not specified
    if max_size_bytes is None:
        from .config import get_config
        max_size_bytes = get_config().max_log_size_bytes

    _rotate_log_file(path, LOG_ROTATION_THRESHOLD_BYTES, LOG_ROTATION_KEEP_FILES)
    
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
    event_type: str | Path,
    message: Optional[str] = None,
    *legacy_message,
    ticket_id: Optional[str] = None,
    extra: Optional[dict] = None,
    source: Optional[str] = None,
    level: str = 'INFO',
    correlation_id: Optional[str] = None,
    # DEPRECATED: path parameter for backward compatibility
    path: Optional[Path] = None,
) -> None:
    """
    Log a structured event to the database event_log table.
    
    MIGRATION NOTE: Uses database storage; file logging is deprecated.
    The 'path' parameter is ignored for backward compatibility.
    
    Args:
        event_type: Type of event (e.g., TICKET_CREATED, DISPATCH_STARTED). Legacy
            callers may still pass the AF Log path first (signature:
            `log_event(path, event_type, message, ...)`) and this helper will
            auto-shift the arguments for you.
        message: Human-readable message.
        ticket_id: Optional ticket ID.
        extra: Optional extra data dictionary.
        source: Optional source module/function.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        correlation_id: Optional correlation ID for tracing.
        path: DEPRECATED - ignored (for backward compatibility).
    """
    try:
        import json

        # Support the legacy signature that passed the AF log path first.
        if isinstance(event_type, (Path, os.PathLike)):
            legacy_path = Path(event_type)
            if message is None or not legacy_message:
                raise TypeError("log_event requires an event_type and message")
            legacy_payload = legacy_message[0]
            if len(legacy_message) > 1:
                raise TypeError("Unexpected extra positional arguments to log_event")
            event_type = message
            message = legacy_payload
            if path is None:
                path = legacy_path

        if message is None:
            raise TypeError("log_event requires an event_type and message")

        # Convert extra dict to JSON string
        extra_json = None
        if extra:
            try:
                extra_json = json.dumps(extra, default=str)
            except Exception:
                extra_json = str(extra)

        # Non-blocking background logging to DB event repository
        # Use synchronous logging in tests or when ACTIFIX_SYNC_LOGGING is set
        sync_mode = os.environ.get("ACTIFIX_SYNC_LOGGING") == "1"

        def _background_db_log():
            try:
                from .persistence.event_repo import get_event_repository
                repo = get_event_repository()
                repo.log_event(
                    event_type=event_type,
                    message=message,
                    ticket_id=ticket_id,
                    correlation_id=correlation_id,
                    extra_json=extra_json,
                    source=source,
                    level=level,
                )
            except Exception:
                pass

        if sync_mode:
            # Synchronous logging for tests - ensures events are persisted before returning
            _background_db_log()
        else:
            # Asynchronous logging for production - non-blocking
            try:
                executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="actifix_log")
                executor.submit(_background_db_log)
                executor.shutdown(wait=False)
            except Exception:
                pass


    except Exception:
        # Silently fail to avoid recursive logging errors
        pass
