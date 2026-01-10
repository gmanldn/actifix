"""
Actifix DoAF - Ticket Dispatch and Processing.

Dispatches tickets to AI for automated fixes.

Thread-safety: operations that read/modify ACTIFIX-LIST.md are guarded by a
file-based lock to prevent duplicate dispatch when multiple threads/processes
run concurrently.
"""

import contextlib
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable, Iterator

from .log_utils import atomic_write, log_event
from .state_paths import get_actifix_paths, ActifixPaths


@dataclass
class TicketInfo:
    """Parsed ticket information."""
    
    ticket_id: str
    priority: str
    error_type: str
    message: str
    source: str
    run_name: str
    created: str
    duplicate_guard: str
    full_block: str
    
    # Checklist state
    documented: bool = False
    functioning: bool = False
    tested: bool = False
    completed: bool = False


def parse_ticket_block(block: str) -> Optional[TicketInfo]:
    """
    Parse a ticket block from ACTIFIX-LIST.md.
    
    Args:
        block: Raw markdown block for a ticket.
    
    Returns:
        TicketInfo if parsed successfully, None otherwise.
    """
    # Extract ticket ID from header
    header_match = re.search(r'##+ (ACT-\d{8}-[A-F0-9]+)', block)
    if not header_match:
        return None
    
    ticket_id = header_match.group(1)
    
    # Extract priority
    priority_match = re.search(r'\[P([0-3])\]', block)
    priority = f"P{priority_match.group(1)}" if priority_match else "P2"
    
    # Extract fields
    def extract_field(pattern: str, default: str = "") -> str:
        match = re.search(pattern, block)
        return match.group(1) if match else default
    
    error_type = extract_field(r'\*\*Error Type\*\*:\s*(.+)')
    source = extract_field(r'\*\*Source\*\*:\s*`([^`]+)`')
    run_name = extract_field(r'\*\*Run\*\*:\s*(.+)')
    created = extract_field(r'\*\*Created\*\*:\s*(.+)')
    duplicate_guard = extract_field(r'\*\*Duplicate Guard\*\*:\s*`([^`]+)`')
    
    # Extract message from header
    msg_match = re.search(r'\[P[0-3]\]\s*\w+:\s*(.+)', block.split('\n')[0])
    message = msg_match.group(1) if msg_match else ""
    
    # Check checklist state
    documented = '[x] Documented' in block
    functioning = '[x] Functioning' in block
    tested = '[x] Tested' in block
    completed = '[x] Completed' in block
    
    return TicketInfo(
        ticket_id=ticket_id,
        priority=priority,
        error_type=error_type,
        message=message,
        source=source,
        run_name=run_name,
        created=created,
        duplicate_guard=duplicate_guard,
        full_block=block,
        documented=documented,
        functioning=functioning,
        tested=tested,
        completed=completed,
    )


def get_open_tickets(paths: Optional[ActifixPaths] = None) -> list[TicketInfo]:
    """
    Get all open (incomplete) tickets from ACTIFIX-LIST.md.
    
    Args:
        paths: Optional paths override.
    
    Returns:
        List of open TicketInfo, sorted by priority (P0 first).
    """
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        return []
    
    content = paths.list_file.read_text()
    
    # Find Active Items section
    if "## Active Items" not in content:
        return []
    
    active_start = content.find("## Active Items")
    active_end = content.find("## Completed Items")
    if active_end == -1:
        active_section = content[active_start:]
    else:
        active_section = content[active_start:active_end]
    
    # Split into ticket blocks (support ## or ### headers)
    blocks = re.split(r'(?=##+ ACT-)', active_section)
    
    tickets = []
    for block in blocks:
        if block.strip() and block.lstrip().startswith('## ACT-'):
            ticket = parse_ticket_block(block)
            if ticket and not ticket.completed:
                tickets.append(ticket)
    
    # Sort by priority (P0 first)
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    tickets.sort(key=lambda t: priority_order.get(t.priority, 4))
    
    return tickets


def mark_ticket_complete(
    ticket_id: str,
    summary: str = "",
    paths: Optional[ActifixPaths] = None,
    use_lock: bool = True,
) -> bool:
    """
    Mark a ticket as complete in ACTIFIX-LIST.md.
    
    Args:
        ticket_id: Ticket ID to mark complete.
        summary: Optional completion summary.
        paths: Optional paths override.
        use_lock: Guard writes with the DoAF lock (set False if already held).
    
    Returns:
        True if marked complete, False if not found.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        return False
    
    with _ticket_lock(paths, enabled=use_lock):
        content = paths.list_file.read_text()
    
        # Find the ticket block (support ## or ### headers)
        header_pattern = re.compile(
            rf'(##+\s+{re.escape(ticket_id)}.*?)'
            r'((?=##+\s+ACT-)|(?=##\s+Completed Items)|\Z)',
            re.DOTALL,
        )
        match = header_pattern.search(content)
        if not match:
            return False
        
        ticket_block = match.group(1)
        
        # Update checkboxes
        new_block = ticket_block
        new_block = re.sub(r'\[[ ]\] Documented', '[x] Documented', new_block)
        new_block = re.sub(r'\[[ ]\] Functioning', '[x] Functioning', new_block)
        new_block = re.sub(r'\[[ ]\] Tested', '[x] Tested', new_block)
        new_block = re.sub(r'\[[ ]\] Completed', '[x] Completed', new_block)
        
        # Add summary if provided
        if summary and "- Summary:" not in new_block:
            new_block = new_block.rstrip() + f"\n- Summary: {summary}\n\n"
        elif summary:
            new_block = re.sub(r'- Summary:.*', f'- Summary: {summary}', new_block)
        
        # Replace in content
        updated = content.replace(ticket_block, new_block, 1)
        
        # Move to Completed section if needed
        if "## Completed Items" in updated:
            # Remove updated block from Active
            updated = updated.replace(new_block, "", 1)
            
            # Add to Completed
            completed_pos = updated.find("## Completed Items")
            insert_pos = completed_pos + len("## Completed Items\n")
            updated = updated[:insert_pos] + new_block + updated[insert_pos:]
        
        atomic_write(paths.list_file, updated)
        
        log_event(
            paths.aflog_file,
            "TICKET_COMPLETED",
            f"Marked ticket complete: {ticket_id}",
            ticket_id=ticket_id,
            extra={"summary": summary[:50] if summary else None}
        )
        
        return True


def process_next_ticket(
    ai_handler: Optional[Callable[[TicketInfo], bool]] = None,
    paths: Optional[ActifixPaths] = None,
) -> Optional[TicketInfo]:
    """
    Process the next open ticket.
    
    Args:
        ai_handler: Optional custom AI handler function.
                   Takes TicketInfo, returns True if fixed.
        paths: Optional paths override.
    
    Returns:
        Processed TicketInfo if any, None otherwise.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    with _ticket_lock(paths):
        tickets = get_open_tickets(paths)
        if not tickets:
            log_event(
                paths.aflog_file,
                "NO_TICKETS",
                "No open tickets to process"
            )
            return None
        
        # Get highest priority ticket
        ticket = tickets[0]
        
        log_event(
            paths.aflog_file,
            "DISPATCH_STARTED",
            f"Processing ticket: {ticket.ticket_id}",
            ticket_id=ticket.ticket_id,
            extra={"priority": ticket.priority}
        )
        
        # If AI handler provided, use it
        if ai_handler:
            try:
                success = ai_handler(ticket)
                if success:
                    mark_ticket_complete(
                        ticket.ticket_id,
                        summary="Fixed via AI handler",
                        paths=paths,
                        use_lock=False,  # lock already held
                    )
                    log_event(
                        paths.aflog_file,
                        "DISPATCH_SUCCESS",
                        f"AI handler completed: {ticket.ticket_id}",
                        ticket_id=ticket.ticket_id
                    )
            except Exception as e:
                log_event(
                    paths.aflog_file,
                    "DISPATCH_FAILED",
                    f"AI handler failed: {e}",
                    ticket_id=ticket.ticket_id,
                    extra={"error": str(e)}
                )
        
        return ticket


def process_tickets(
    max_tickets: int = 5,
    ai_handler: Optional[Callable[[TicketInfo], bool]] = None,
    paths: Optional[ActifixPaths] = None,
) -> list[TicketInfo]:
    """
    Process multiple open tickets.
    
    Args:
        max_tickets: Maximum tickets to process.
        ai_handler: Optional custom AI handler.
        paths: Optional paths override.
    
    Returns:
        List of processed TicketInfo.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    processed = []
    
    for _ in range(max_tickets):
        ticket = process_next_ticket(ai_handler, paths)
        if ticket:
            processed.append(ticket)
        else:
            break
    
    return processed


def get_ticket_stats(paths: Optional[ActifixPaths] = None) -> dict:
    """
    Get statistics about tickets.
    
    Args:
        paths: Optional paths override.
    
    Returns:
        Dict with ticket statistics.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        return {
            "open": 0,
            "completed": 0,
            "by_priority": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
        }
    
    content = paths.list_file.read_text()
    
    # Count all tickets
    all_tickets = re.findall(r'##+ (ACT-\d{8}-[A-F0-9]+)', content)
    
    # Count completed
    completed = content.count('[x] Completed')
    
    # Count by priority
    by_priority = {
        "P0": len(re.findall(r'\[P0\]', content)),
        "P1": len(re.findall(r'\[P1\]', content)),
        "P2": len(re.findall(r'\[P2\]', content)),
        "P3": len(re.findall(r'\[P3\]', content)),
    }
    
    return {
        "total": len(all_tickets),
        "open": len(all_tickets) - completed,
        "completed": completed,
        "by_priority": by_priority,
    }


# --- Concurrency helpers ---

_THREAD_LOCK = threading.Lock()
_LOCK_FILENAME = "doaf.lock"


@contextlib.contextmanager
def _ticket_lock(paths: ActifixPaths, enabled: bool = True, timeout: float = 10.0) -> Iterator[None]:
    """
    File-based lock to guard ticket reads/writes across threads/processes.
    
    Uses a reentrant thread lock plus a filesystem lock (fcntl/msvcrt). If
    locking fails within timeout, raises TimeoutError.
    """
    if not enabled:
        yield
        return
    
    lock_path = paths.state_dir / _LOCK_FILENAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    with _THREAD_LOCK:
        lock_file = lock_path.open("a+")
        try:
            _acquire_file_lock(lock_file, timeout=timeout)
            yield
        finally:
            _release_file_lock(lock_file)
            lock_file.close()


def _acquire_file_lock(lock_file, timeout: float = 10.0) -> None:
    start = time.monotonic()
    while True:
        try:
            if _try_lock(lock_file):
                return
        except BlockingIOError:
            pass
        
        if time.monotonic() - start > timeout:
            raise TimeoutError("Timed out acquiring DoAF lock")
        time.sleep(0.05)


def _release_file_lock(lock_file) -> None:
    try:
        if _has_fcntl():
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        elif _has_msvcrt():
            import msvcrt
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
    except Exception:
        pass


def _try_lock(lock_file) -> bool:
    if _has_fcntl():
        import fcntl
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    if _has_msvcrt():
        import msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    # Fallback: rely on thread lock only
    return True


def _has_fcntl() -> bool:
    try:
        import fcntl  # noqa: F401
        return True
    except Exception:
        return False


def _has_msvcrt() -> bool:
    try:
        import msvcrt  # noqa: F401
        return True
    except Exception:
        return False
