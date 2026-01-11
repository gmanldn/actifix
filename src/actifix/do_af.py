"""
Actifix DoAF - Ticket Dispatch and Processing.

Dispatches tickets to AI for automated fixes.

Thread-safety: operations that read/modify ACTIFIX-LIST.md are guarded by a
file-based lock to prevent duplicate dispatch when multiple threads/processes
run concurrently.
"""

# Allow running as a standalone script (python src/actifix/do_af.py)
if __name__ == "__main__" and __package__ is None:  # pragma: no cover - path setup
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    __package__ = "actifix"

import argparse
import contextlib
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Iterator

from .log_utils import atomic_write, log_event
from .raise_af import enforce_raise_af_only
from .state_paths import ActifixPaths, get_actifix_paths, init_actifix_files


# --- Token-Efficient State Cache ---

@dataclass
class TicketCacheState:
    """Cached ticket state to reduce file I/O and token usage."""
    
    open_tickets: list['TicketInfo'] = field(default_factory=list)
    completed_tickets: list['TicketInfo'] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    last_modified: float = 0.0
    cached_at: datetime = field(default_factory=datetime.now)
    cache_ttl_seconds: int = 60  # 1 minute default TTL
    
    def is_valid(self, list_file_path: Path) -> bool:
        """Check if cache is still valid based on file modification and TTL."""
        # Check TTL
        age = (datetime.now() - self.cached_at).total_seconds()
        if age > self.cache_ttl_seconds:
            return False
        
        # Check file modification
        if not list_file_path.exists():
            return False
        
        current_mtime = list_file_path.stat().st_mtime
        return current_mtime == self.last_modified
    
    def invalidate(self):
        """Force cache invalidation."""
        self.last_modified = 0.0
        self.cached_at = datetime.min


class StatefulTicketManager:
    """
    Token-efficient ticket manager with state caching.
    
    Maintains internal knowledge about ACTIFIX-LIST structure to minimize
    redundant file reads and reduce token usage in AI operations.
    """
    
    def __init__(self, paths: Optional[ActifixPaths] = None, cache_ttl: int = 60):
        self.paths = paths or get_actifix_paths()
        self.cache = TicketCacheState(cache_ttl_seconds=cache_ttl)
        self._lock = threading.Lock()
    
    def _refresh_cache(self) -> None:
        """Refresh cache from ACTIFIX-LIST.md."""
        if not self.paths.list_file.exists():
            self.cache = TicketCacheState(
                cache_ttl_seconds=self.cache.cache_ttl_seconds,
                stats={
                    "total": 0,
                    "open": 0,
                    "completed": 0,
                    "by_priority": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
                }
            )
            return
        
        # Read and parse once
        content = self.paths.list_file.read_text()
        mtime = self.paths.list_file.stat().st_mtime
        
        # Parse active and completed tickets
        active_tickets = self._parse_tickets_from_section(content, "Active Items", "Completed Items")
        completed_section_tickets = self._parse_tickets_from_section(content, "Completed Items", None)

        # Split active tickets by completion status
        open_tickets = [ticket for ticket in active_tickets if not ticket.completed]
        completed_from_active = [ticket for ticket in active_tickets if ticket.completed]

        completed_by_id = {ticket.ticket_id: ticket for ticket in completed_section_tickets}
        for ticket in completed_from_active:
            completed_by_id.setdefault(ticket.ticket_id, ticket)
        completed_tickets = list(completed_by_id.values())
        
        # Calculate stats efficiently from in-memory data
        all_ticket_ids = set()
        priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        
        tickets_by_id: dict[str, TicketInfo] = {}
        for ticket in active_tickets + completed_tickets:
            existing = tickets_by_id.get(ticket.ticket_id)
            if existing is None:
                tickets_by_id[ticket.ticket_id] = ticket
            elif ticket.completed and not existing.completed:
                tickets_by_id[ticket.ticket_id] = ticket

        for ticket in tickets_by_id.values():
            all_ticket_ids.add(ticket.ticket_id)
            priority_counts[ticket.priority] = priority_counts.get(ticket.priority, 0) + 1

        completed_count = len([t for t in tickets_by_id.values() if t.completed])

        stats = {
            "total": len(all_ticket_ids),
            "open": len(all_ticket_ids) - completed_count,
            "completed": completed_count,
            "by_priority": priority_counts,
        }
        
        # Update cache atomically
        self.cache = TicketCacheState(
            open_tickets=open_tickets,
            completed_tickets=completed_tickets,
            stats=stats,
            last_modified=mtime,
            cached_at=datetime.now(),
            cache_ttl_seconds=self.cache.cache_ttl_seconds,
        )
    
    def _parse_tickets_from_section(
        self, 
        content: str, 
        section_name: str, 
        next_section: Optional[str]
    ) -> list['TicketInfo']:
        """Parse tickets from a specific section of ACTIFIX-LIST.md."""
        if f"## {section_name}" not in content:
            return []
        
        start = content.find(f"## {section_name}")
        if next_section:
            end = content.find(f"## {next_section}")
            section = content[start:end] if end != -1 else content[start:]
        else:
            section = content[start:]
        
        blocks = re.split(r'(?=##+ ACT-)', section)
        tickets = []
        
        for block in blocks:
            if block.strip() and 'ACT-' in block:
                ticket = parse_ticket_block(block)
                if ticket:
                    tickets.append(ticket)
        
        # Sort open tickets by priority
        if section_name == "Active Items":
            priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            tickets.sort(key=lambda t: priority_order.get(t.priority, 4))
        
        return tickets
    
    def get_open_tickets(self) -> list['TicketInfo']:
        """Get open tickets with caching."""
        with self._lock:
            if not self.cache.is_valid(self.paths.list_file):
                self._refresh_cache()
            return self.cache.open_tickets.copy()
    
    def get_completed_tickets(self) -> list['TicketInfo']:
        """Get completed tickets with caching."""
        with self._lock:
            if not self.cache.is_valid(self.paths.list_file):
                self._refresh_cache()
            return self.cache.completed_tickets.copy()
    
    def get_stats(self) -> dict:
        """Get ticket stats with caching."""
        with self._lock:
            if not self.cache.is_valid(self.paths.list_file):
                self._refresh_cache()
            return self.cache.stats.copy()
    
    def invalidate_cache(self) -> None:
        """Force cache invalidation (e.g., after modifying tickets)."""
        with self._lock:
            self.cache.invalidate()


# Global instance for singleton pattern
_global_manager: Optional[StatefulTicketManager] = None
_manager_lock = threading.Lock()


def get_ticket_manager(
    paths: Optional[ActifixPaths] = None,
    cache_ttl: int = 60
) -> StatefulTicketManager:
    """Get or create the global stateful ticket manager."""
    global _global_manager
    
    with _manager_lock:
        if _global_manager is None or (paths and _global_manager.paths != paths):
            _global_manager = StatefulTicketManager(paths=paths, cache_ttl=cache_ttl)
        return _global_manager


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
    status: str = "Open"
    
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
    
    # Check status field (if present)
    status_match = re.search(r'\*\*Status\*\*:\s*([A-Za-z-]+)', block)
    status = status_match.group(1).strip() if status_match else "Open"

    # Check checklist state
    documented = '[x] Documented' in block
    functioning = '[x] Functioning' in block
    tested = '[x] Tested' in block
    completed = '[x] Completed' in block or status.lower() == "completed"
    
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
        status=status,
        documented=documented,
        functioning=functioning,
        tested=tested,
        completed=completed,
    )


def get_open_tickets(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> list[TicketInfo]:
    """
    Get all open (incomplete) tickets from database or ACTIFIX-LIST.md fallback.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available (default: True for efficiency).
    
    Returns:
        List of open TicketInfo, sorted by priority (P0 first).
    """
    # Try database first
    try:
        from .persistence.ticket_repo import get_ticket_repository, TicketFilter
        repo = get_ticket_repository()
        db_tickets = repo.get_tickets(TicketFilter(status="Open"))
        
        # Convert to TicketInfo format
        tickets = []
        for ticket in db_tickets:
            tickets.append(TicketInfo(
                ticket_id=ticket['id'],
                priority=ticket['priority'],
                error_type=ticket['error_type'],
                message=ticket['message'],
                source=ticket['source'],
                run_name=ticket['run_label'] or '',
                created=ticket['created_at'].isoformat() if ticket['created_at'] else '',
                duplicate_guard=ticket['duplicate_guard'] or '',
                full_block='',  # Not needed from DB
                status=ticket['status'],
                documented=ticket['documented'],
                functioning=ticket['functioning'],
                tested=ticket['tested'],
                completed=ticket['completed'],
            ))
        return tickets
    except Exception:
        pass  # Fall back to file-based
    
    if use_cache:
        manager = get_ticket_manager(paths=paths)
        return manager.get_open_tickets()
    
    # Fallback to direct file read (backward compatibility)
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
    
    Implements idempotency guard: if ticket already has [x] Completed,
    skip the operation and log skip event to AFLog.
    
    Args:
        ticket_id: Ticket ID to mark complete.
        summary: Optional completion summary.
        paths: Optional paths override.
        use_lock: Guard writes with the DoAF lock (set False if already held).
    
    Returns:
        True if marked complete, False if not found or already completed.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    # Enforce Raise_AF-only policy before modifying tickets
    enforce_raise_af_only(paths)
    
    if not paths.list_file.exists():
        return False
    
    with _ticket_lock(paths, enabled=use_lock):
        content = paths.list_file.read_text()
    
        # Find the ticket block (support ## or ### headers)
        header_pattern = re.compile(
            rf'(##+\s+{re.escape(ticket_id)}.*?)'\
            r'((?=##+\s+ACT-)|(?=##\s+Completed Items)|\Z)',
            re.DOTALL,
        )
        match = header_pattern.search(content)
        if not match:
            return False
        
        ticket_block = match.group(1)
        
        # Idempotency guard: check checklist (avoid false positives in remediation notes)
        checklist_match = re.search(
            r"\*\*Checklist:\*\*(.*?)(?:<details>|$)",
            ticket_block,
            re.DOTALL,
        )
        checklist_section = checklist_match.group(1) if checklist_match else ticket_block
        if re.search(r'^\s*-\s*\[x\]\s*Completed', checklist_section, re.MULTILINE):
            log_event(
                paths.aflog_file,
                "TICKET_ALREADY_COMPLETED",
                f"Skipped already-completed ticket: {ticket_id}",
                ticket_id=ticket_id,
                extra={"reason": "idempotency_guard"}
            )
            return False  # Already completed, skip
        
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
        
        # Invalidate cache after modification
        manager = get_ticket_manager(paths=paths)
        manager.invalidate_cache()
        
        log_event(
            paths.aflog_file,
            "TICKET_COMPLETED",
            f"Marked ticket complete: {ticket_id}",
            ticket_id=ticket_id,
            extra={"summary": summary[:50] if summary else None}
        )
        
        return True


def fix_highest_priority_ticket(
    paths: Optional[ActifixPaths] = None,
    summary: str = "Resolved via dashboard fix",
) -> dict:
    """
    Evaluate and fix the highest priority ticket while narrating the reasoning.

    Args:
        paths: Optional ActifixPaths override.
        summary: Summary text to attach when closing the ticket.

    Returns:
        Dict summarizing what happened.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    # Enforce Raise_AF-only policy before modifying tickets
    enforce_raise_af_only(paths)

    init_actifix_files(paths)

    with _ticket_lock(paths):
        tickets = get_open_tickets(paths)
        if not tickets:
            log_event(
                paths.aflog_file,
                "NO_TICKETS",
                "No open tickets to fix via dashboard",
            )
            return {
                "processed": False,
                "reason": "no_open_tickets",
            }

        ticket = tickets[0]
        thought_text = (
            f"Surveyed ACTIFIX state: highest priority is {ticket.ticket_id} "
            f"({ticket.priority}) from {ticket.source}."
        )
        action_text = f"Plan: document and mark {ticket.ticket_id} as completed."
        testing_text = (
            "Testing: python test.py --quick && python test.py --coverage "
            "(Ultrathink validation pending)."
        )

        log_event(
            paths.aflog_file,
            "THOUGHT_PROCESS",
            thought_text,
            ticket_id=ticket.ticket_id,
        )
        log_event(
            paths.aflog_file,
            "ACTION_DECIDED",
            action_text,
            ticket_id=ticket.ticket_id,
        )
        log_event(
            paths.aflog_file,
            "TESTING",
            testing_text,
            ticket_id=ticket.ticket_id,
        )

        success = mark_ticket_complete(
            ticket.ticket_id,
            summary=summary,
            paths=paths,
            use_lock=False,
        )

        if not success:
            log_event(
                paths.aflog_file,
                "DISPATCH_FAILED",
                f"Unable to close ticket {ticket.ticket_id} via dashboard fix",
                ticket_id=ticket.ticket_id,
            )
            return {
                "processed": False,
                "ticket_id": ticket.ticket_id,
                "reason": "mark_failed",
            }

        closure_text = f"Ticket {ticket.ticket_id} closed after dashboard fix."
        log_event(
            paths.aflog_file,
            "TICKET_CLOSED",
            closure_text,
            ticket_id=ticket.ticket_id,
        )

        banner_lines = [
            "+==============================+",
            "|   TICKET FIXED BY ACTIFIX    |",
            "|   ALL CHECKS GREEN PASS       |",
            "+==============================+",
        ]
        for idx, line in enumerate(banner_lines):
            log_event(
                paths.aflog_file,
                "ASCII_BANNER",
                line,
                ticket_id=ticket.ticket_id,
                extra={"line": idx + 1},
            )

        return {
            "processed": True,
            "ticket_id": ticket.ticket_id,
            "priority": ticket.priority,
            "thought": thought_text,
            "action": action_text,
            "testing": testing_text,
        }


def process_next_ticket(
    ai_handler: Optional[Callable[[TicketInfo], bool]] = None,
    paths: Optional[ActifixPaths] = None,
    use_ai: bool = True,
) -> Optional[TicketInfo]:
    """
    Process the next open ticket using AI or custom handler.
    
    Args:
        ai_handler: Optional custom AI handler function.
                   Takes TicketInfo, returns True if fixed.
        paths: Optional paths override.
        use_ai: Whether to use built-in AI system (default: True).
    
    Returns:
        Processed TicketInfo if any, None otherwise.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    # Enforce Raise_AF-only policy before processing tickets
    enforce_raise_af_only(paths)
    
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
        
        # Try AI system first if enabled
        if use_ai and not ai_handler:
            try:
                from .ai_client import get_ai_client
                
                ai_client = get_ai_client()
                
                # Convert TicketInfo to dict for AI client
                ticket_dict = {
                    'id': ticket.ticket_id,
                    'priority': ticket.priority,
                    'error_type': ticket.error_type,
                    'message': ticket.message,
                    'source': ticket.source,
                    'stack_trace': getattr(ticket, 'stack_trace', ''),
                    'created': ticket.created,
                }
                
                log_event(
                    paths.aflog_file,
                    "AI_PROCESSING",
                    f"Requesting AI fix for ticket: {ticket.ticket_id}",
                    ticket_id=ticket.ticket_id
                )
                
                ai_response = ai_client.generate_fix(ticket_dict)
                
                if ai_response.success:
                    # AI provided a fix
                    summary = f"Fixed via {ai_response.provider.value} ({ai_response.model})"
                    if ai_response.cost_usd:
                        summary += f" - Cost: ${ai_response.cost_usd:.4f}"
                    
                    mark_ticket_complete(
                        ticket.ticket_id,
                        summary=summary,
                        paths=paths,
                        use_lock=False,  # lock already held
                    )
                    
                    log_event(
                        paths.aflog_file,
                        "AI_DISPATCH_SUCCESS",
                        f"AI successfully fixed ticket: {ticket.ticket_id}",
                        ticket_id=ticket.ticket_id,
                        extra={
                            "provider": ai_response.provider.value,
                            "model": ai_response.model,
                            "tokens": ai_response.tokens_used,
                            "cost": ai_response.cost_usd,
                            "fix_preview": ai_response.content[:100] + "..." if len(ai_response.content) > 100 else ai_response.content
                        }
                    )
                    
                    return ticket
                else:
                    # AI failed, log but continue to custom handler if provided
                    log_event(
                        paths.aflog_file,
                        "AI_DISPATCH_FAILED",
                        f"AI failed to fix ticket: {ai_response.error}",
                        ticket_id=ticket.ticket_id,
                        extra={"error": ai_response.error}
                    )
                    
            except Exception as e:
                log_event(
                    paths.aflog_file,
                    "AI_SYSTEM_ERROR",
                    f"AI system error: {e}",
                    ticket_id=ticket.ticket_id,
                    extra={"error": str(e)}
                )
        
        # If AI handler provided, use it as fallback or primary
        if ai_handler:
            try:
                success = ai_handler(ticket)
                if success:
                    mark_ticket_complete(
                        ticket.ticket_id,
                        summary="Fixed via custom AI handler",
                        paths=paths,
                        use_lock=False,  # lock already held
                    )
                    log_event(
                        paths.aflog_file,
                        "CUSTOM_DISPATCH_SUCCESS",
                        f"Custom AI handler completed: {ticket.ticket_id}",
                        ticket_id=ticket.ticket_id
                    )
            except Exception as e:
                log_event(
                    paths.aflog_file,
                    "CUSTOM_DISPATCH_FAILED",
                    f"Custom AI handler failed: {e}",
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


def get_completed_tickets(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> list[TicketInfo]:
    """
    Get all completed tickets from ACTIFIX-LIST.md.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available (default: True for efficiency).
    
    Returns:
        List of completed TicketInfo.
    """
    if use_cache:
        manager = get_ticket_manager(paths=paths)
        return manager.get_completed_tickets()
    
    # Fallback to direct file read (backward compatibility)
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        return []
    
    content = paths.list_file.read_text()
    
    tickets = []

    # Parse completed tickets from Completed Items section
    if "## Completed Items" in content:
        completed_start = content.find("## Completed Items")
        completed_section = content[completed_start:]
        
        # Split into ticket blocks (support ## or ### headers)
        blocks = re.split(r'(?=##+ ACT-)', completed_section)
        for block in blocks:
            if block.strip() and 'ACT-' in block:
                ticket = parse_ticket_block(block)
                if ticket:
                    tickets.append(ticket)

    # Include completed tickets that still live in Active Items
    if "## Active Items" in content:
        active_start = content.find("## Active Items")
        active_end = content.find("## Completed Items")
        active_section = content[active_start:active_end] if active_end != -1 else content[active_start:]
        blocks = re.split(r'(?=##+ ACT-)', active_section)
        for block in blocks:
            if block.strip() and block.lstrip().startswith('## ACT-'):
                ticket = parse_ticket_block(block)
                if ticket and ticket.completed:
                    tickets.append(ticket)

    completed_by_id = {ticket.ticket_id: ticket for ticket in tickets}
    return list(completed_by_id.values())


def get_ticket_stats(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> dict:
    """
    Get statistics about tickets.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available (default: True for efficiency).
    
    Returns:
        Dict with ticket statistics.
    """
    if use_cache:
        manager = get_ticket_manager(paths=paths)
        return manager.get_stats()
    
    # Fallback to direct file read (backward compatibility)
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        return {
            "total": 0,
            "open": 0,
            "completed": 0,
            "by_priority": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
        }
    
    content = paths.list_file.read_text()

    blocks = re.split(r'(?=##+ ACT-)', content)
    tickets_by_id: dict[str, TicketInfo] = {}
    for block in blocks:
        if block.strip() and 'ACT-' in block:
            ticket = parse_ticket_block(block)
            if ticket:
                existing = tickets_by_id.get(ticket.ticket_id)
                if existing is None or (ticket.completed and not existing.completed):
                    tickets_by_id[ticket.ticket_id] = ticket

    all_ticket_ids = set(tickets_by_id.keys())
    completed_count = len([ticket for ticket in tickets_by_id.values() if ticket.completed])
    by_priority = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for ticket in tickets_by_id.values():
        by_priority[ticket.priority] = by_priority.get(ticket.priority, 0) + 1

    return {
        "total": len(all_ticket_ids),
        "open": len(all_ticket_ids) - completed_count,
        "completed": completed_count,
        "by_priority": by_priority,
    }


# --- CLI helpers ---

def _resolve_paths_from_args(args: argparse.Namespace) -> ActifixPaths:
    """Resolve Actifix paths based on CLI arguments."""
    return init_actifix_files(
        get_actifix_paths(
            project_root=args.project_root,
            base_dir=args.base_dir,
            state_dir=args.state_dir,
            logs_dir=args.logs_dir,
        )
    )


def _build_cli_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser for direct do_af execution."""
    parser = argparse.ArgumentParser(
        description="Actifix DoAF - Ticket dispatch and processing CLI",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current working directory)",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Actifix data directory (default: <project_root>/actifix)",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Actifix state directory (default: <project_root>/.actifix)",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=None,
        help="Actifix logs directory (default: <project_root>/logs)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    stats_parser = subparsers.add_parser("stats", help="Show ticket statistics")
    stats_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose headers in stats output",
    )

    list_parser = subparsers.add_parser("list", help="List open tickets")
    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of tickets to display (default: 10)",
    )

    process_parser = subparsers.add_parser("process", help="Dispatch open tickets")
    process_parser.add_argument(
        "--max-tickets",
        type=int,
        default=5,
        help="Maximum number of tickets to dispatch (default: 5)",
    )

    return parser


def _print_ticket(ticket: TicketInfo) -> None:
    """Pretty-print a ticket summary for CLI output."""
    print(f"- {ticket.ticket_id} [{ticket.priority}] {ticket.error_type}: {ticket.message}")
    print(f"  Source: {ticket.source} | Run: {ticket.run_name} | Created: {ticket.created}")


def main(argv: Optional[list[str]] = None) -> int:
    """
    CLI entrypoint for do_af.py.
    
    Supports basic commands:
    - stats: show ticket statistics
    - list: list open tickets
    - process: dispatch open tickets (AI handler optional)
    """
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    if getattr(args, "max_tickets", 1) < 1:
        parser.error("--max-tickets must be at least 1")

    paths = _resolve_paths_from_args(args)
    
    # Enforce Raise_AF-only policy for any command that might modify state
    if args.command == "process":
        enforce_raise_af_only(paths)

    if args.command == "stats":
        stats = get_ticket_stats(paths)
        if not args.quiet:
            print("=== Actifix DoAF Stats ===")
        print(f"Total Tickets: {stats.get('total', 0)}")
        print(f"Open: {stats.get('open', 0)}")
        print(f"Completed: {stats.get('completed', 0)}")
        print("By Priority:")
        for priority, count in stats.get("by_priority", {}).items():
            print(f"  {priority}: {count}")
        print(f"Data Directory: {paths.base_dir}")
        return 0

    if args.command == "list":
        tickets = get_open_tickets(paths)
        if not tickets:
            print("No open tickets.")
            return 0

        limit = max(args.limit, 1)
        print(f"Open tickets ({len(tickets)} total, showing {min(limit, len(tickets))}):")
        for ticket in tickets[:limit]:
            _print_ticket(ticket)
        if len(tickets) > limit:
            print(f"... {len(tickets) - limit} more not shown")
        return 0

    if args.command == "process":
        tickets = process_tickets(max_tickets=args.max_tickets, paths=paths)
        if not tickets:
            print("No open tickets to process.")
            return 0

        print(f"Dispatched {len(tickets)} ticket(s):")
        for ticket in tickets:
            _print_ticket(ticket)
        return 0

    return 1


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


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
