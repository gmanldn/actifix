"""
Actifix RaiseAF - Error Recording and Ticket Creation.

Records errors and creates tickets in ACTIFIX-LIST.md.
"""

import hashlib
import os
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .log_utils import atomic_write, log_event, idempotent_append
from .state_paths import get_actifix_paths, init_actifix_files, ActifixPaths


# Priority levels
PRIORITY_P0 = "P0"  # Critical - immediate action required
PRIORITY_P1 = "P1"  # High - fix within hours
PRIORITY_P2 = "P2"  # Medium - fix within days
PRIORITY_P3 = "P3"  # Low - fix when convenient

# Maximum errors in rollup
MAX_ROLLUP_ERRORS = 20


@dataclass
class ActifixEntry:
    """Represents an Actifix ticket entry."""
    
    ticket_id: str
    priority: str
    error_type: str
    message: str
    source: str
    run_name: str
    created: datetime
    duplicate_guard: str
    stack_trace: str = ""
    format_version: str = "1.0"
    correlation_id: Optional[str] = None
    
    # Checklist state
    documented: bool = False
    functioning: bool = False
    tested: bool = False
    completed: bool = False
    summary: str = ""


def generate_ticket_id() -> str:
    """Generate a unique ticket ID in format ACT-YYYYMMDD-XXXXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    # Use random bytes for uniqueness
    random_hex = hashlib.sha256(os.urandom(16)).hexdigest()[:6].upper()
    return f"ACT-{date_str}-{random_hex}"


def generate_duplicate_guard(source: str, message: str) -> str:
    """
    Generate a duplicate guard hash to prevent duplicate tickets.
    
    Args:
        source: Source location of error.
        message: Error message.
    
    Returns:
        Duplicate guard string like 'ACTIFIX-path-to-file-abc123'.
    """
    # Normalize source path
    normalized_source = re.sub(r'[^a-zA-Z0-9_.-]', '-', source)
    
    # Create hash from source and message
    content = f"{source}:{message}"
    hash_suffix = hashlib.sha256(content.encode()).hexdigest()[:8]
    
    return f"ACTIFIX-{normalized_source}-{hash_suffix}"


def _redact_secrets(text: str) -> str:
    """Redact potential secrets from text."""
    patterns = [
        (r'api[_-]?key["\s:=]+["\']?[\w-]+["\']?', 'api_key=***REDACTED***'),
        (r'password["\s:=]+["\']?[^\s"\']+["\']?', 'password=***REDACTED***'),
        (r'token["\s:=]+["\']?[\w-]+["\']?', 'token=***REDACTED***'),
        (r'secret["\s:=]+["\']?[^\s"\']+["\']?', 'secret=***REDACTED***'),
        (r'bearer\s+[\w-]+', 'Bearer ***REDACTED***'),
        (r'sk-[a-zA-Z0-9]+', '***REDACTED_KEY***'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _format_ticket_block(entry: ActifixEntry) -> str:
    """Format a ticket entry as markdown block for ACTIFIX-LIST.md."""
    
    checklist = [
        f"- [{'x' if entry.documented else ' '}] Documented",
        f"- [{'x' if entry.functioning else ' '}] Functioning",
        f"- [{'x' if entry.tested else ' '}] Tested",
        f"- [{'x' if entry.completed else ' '}] Completed",
    ]
    if entry.summary:
        checklist.append(f"- Summary: {entry.summary}")
    
    stack_preview = entry.stack_trace[:500] if entry.stack_trace else "NoneType: None"
    
    block = f"""### {entry.ticket_id} - [{entry.priority}] {entry.error_type}: {entry.message[:80]}

- **Priority**: {entry.priority}
- **Error Type**: {entry.error_type}
- **Source**: `{entry.source}`
- **Run**: {entry.run_name}
- **Created**: {entry.created.isoformat()}
- **Duplicate Guard**: `{entry.duplicate_guard}`

**Checklist:**

{chr(10).join(checklist)}

<details>
<summary>Stack Trace Preview</summary>

```
{stack_preview}
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: {entry.error_type}
Error Message: {entry.message}
Source Location: {entry.source}
Priority: {entry.priority}

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation
2. Identify root cause from stack trace
3. Implement fix following project patterns
4. Write tests with 95%+ coverage
5. Verify all tests pass

</details>

"""
    return block


def _update_rollup(paths: ActifixPaths, entry: ActifixEntry) -> None:
    """Update ACTIFIX.md rollup with new error."""
    rollup_path = paths.rollup_file
    
    # Read existing rollup
    content = ""
    if rollup_path.exists():
        content = rollup_path.read_text()
    
    # Parse existing errors
    lines = []
    if "## Recent Errors" in content:
        section_start = content.find("## Recent Errors")
        section_content = content[section_start:]
        for line in section_content.split("\n"):
            if line.startswith("- "):
                lines.append(line)
    
    # Add new error line
    error_line = (
        f"- {entry.created.isoformat()} | run={entry.run_name} | "
        f"source={entry.source} | type={entry.error_type} | "
        f"id={entry.ticket_id} | {entry.message[:80]}"
    )
    lines.insert(0, error_line)
    
    # Keep only last N errors
    lines = lines[:MAX_ROLLUP_ERRORS]
    
    # Rebuild rollup
    new_content = (
        "# Actifix Error Rollup\n"
        "Tracks the last 20 errors from recent runs. "
        "This file is regenerated by RaiseAF.\n\n"
        "## Recent Errors (last 20)\n"
        + "\n".join(lines) + "\n"
    )
    
    atomic_write(rollup_path, new_content)


def record_error(
    error_type: str,
    message: str,
    source: str,
    priority: str = PRIORITY_P2,
    run_name: str = "manual",
    stack_trace: Optional[str] = None,
    correlation_id: Optional[str] = None,
    paths: Optional[ActifixPaths] = None,
) -> Optional[ActifixEntry]:
    """
    Record an error and create a ticket in ACTIFIX-LIST.md.
    
    Args:
        error_type: Type of error (e.g., 'RuntimeError', 'Enhancement').
        message: Error message or description.
        source: Source location (e.g., 'my_module.py:42').
        priority: Priority level (P0-P3). Default: P2.
        run_name: Name of the run that generated the error.
        stack_trace: Optional stack trace.
        correlation_id: Optional correlation ID for log linking.
        paths: Optional ActifixPaths override.
    
    Returns:
        ActifixEntry if ticket was created, None if duplicate or disabled.
    
    Environment Variables:
        ACTIFIX_CAPTURE_ENABLED: Set to '0' to disable capture.
    """
    # Check if capture is enabled
    if os.environ.get("ACTIFIX_CAPTURE_ENABLED", "1") == "0":
        return None
    
    # Get paths
    if paths is None:
        paths = get_actifix_paths()
    
    # Ensure files exist
    init_actifix_files(paths)
    
    # Redact secrets
    message = _redact_secrets(message)
    if stack_trace:
        stack_trace = _redact_secrets(stack_trace)
    
    # Generate IDs
    ticket_id = generate_ticket_id()
    duplicate_guard = generate_duplicate_guard(source, message)
    
    # Check for duplicate
    if paths.list_file.exists():
        existing = paths.list_file.read_text()
        if duplicate_guard in existing:
            log_event(
                paths.aflog_file,
                "DUPLICATE_SKIPPED",
                f"Duplicate error skipped: {message[:50]}",
                extra={"guard": duplicate_guard}
            )
            return None
    
    # Create entry
    entry = ActifixEntry(
        ticket_id=ticket_id,
        priority=priority,
        error_type=error_type,
        message=message,
        source=source,
        run_name=run_name,
        created=datetime.now(timezone.utc),
        duplicate_guard=duplicate_guard,
        stack_trace=stack_trace or "",
        correlation_id=correlation_id,
    )
    
    # Format ticket block
    ticket_block = _format_ticket_block(entry)
    
    # Read current list
    list_content = paths.list_file.read_text()
    
    # Insert after "## Active Items"
    if "## Active Items" in list_content:
        parts = list_content.split("## Active Items", 1)
        new_content = parts[0] + "## Active Items\n" + ticket_block + parts[1].lstrip("\n")
    else:
        # Fallback: append to end
        new_content = list_content + "\n" + ticket_block
    
    # Write atomically
    atomic_write(paths.list_file, new_content)
    
    # Update rollup
    _update_rollup(paths, entry)
    
    # Log event
    log_event(
        paths.aflog_file,
        "TICKET_CREATED",
        f"Created ticket {ticket_id}: {message[:50]}",
        ticket_id=ticket_id,
        extra={"priority": priority, "source": source}
    )
    
    return entry


def record_exception(
    exc: Exception,
    source: Optional[str] = None,
    priority: str = PRIORITY_P2,
    run_name: str = "exception-handler",
    paths: Optional[ActifixPaths] = None,
) -> Optional[ActifixEntry]:
    """
    Record an exception as an Actifix ticket.
    
    Convenience wrapper around record_error that extracts
    information from an exception.
    
    Args:
        exc: The exception to record.
        source: Override source location.
        priority: Priority level.
        run_name: Run name.
        paths: Optional paths override.
    
    Returns:
        ActifixEntry if created, None otherwise.
    """
    error_type = type(exc).__name__
    message = str(exc)
    stack_trace = traceback.format_exc()
    
    # Extract source from traceback if not provided
    if source is None:
        tb = traceback.extract_tb(exc.__traceback__)
        if tb:
            last_frame = tb[-1]
            source = f"{last_frame.filename}:{last_frame.lineno}"
        else:
            source = "unknown:0"
    
    return record_error(
        error_type=error_type,
        message=message,
        source=source,
        priority=priority,
        run_name=run_name,
        stack_trace=stack_trace,
        paths=paths,
    )
