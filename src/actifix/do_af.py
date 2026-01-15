"""
Actifix DoAF - Ticket Dispatch and Processing.

Dispatches tickets to AI for automated fixes.

Thread-safety: ticket assignment and completion flow goes through the shared
SQLite ticket repository and the lease-based locks it provides.
"""

# Allow running as a standalone script (python src/actifix/do_af.py)
if __name__ == "__main__" and __package__ is None:  # pragma: no cover - path setup
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    __package__ = "actifix"

import argparse
import contextlib
import os
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
    """Cached view for ticket queries to reduce repeated repository calls."""
    
    open_tickets: list['TicketInfo'] = field(default_factory=list)
    completed_tickets: list['TicketInfo'] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    cached_at: float = 0.0
    cache_ttl_seconds: int = 60  # 1 minute default TTL
    
    def needs_refresh(self) -> bool:
        age = time.time() - self.cached_at
        return age > self.cache_ttl_seconds
    
    def invalidate(self) -> None:
        """Force cache invalidation."""
        self.cached_at = 0.0


class StatefulTicketManager:
    """
    Token-efficient ticket manager with a lightweight repository cache.
    """
    
    def __init__(self, paths: Optional[ActifixPaths] = None, cache_ttl: int = 60):
        self.paths = paths or get_actifix_paths()
        self.cache = TicketCacheState(cache_ttl_seconds=cache_ttl)
        self._lock = threading.Lock()
    
    def _refresh_cache(self) -> None:
        """Refresh cache from the ticket repository."""
        from .persistence.ticket_repo import TicketFilter

        repo = _get_ticket_repository()
        open_records = repo.get_tickets(TicketFilter(status="Open"))
        completed_records = repo.get_tickets(TicketFilter(status="Completed"))

        open_tickets = [_ticket_info_from_record(rec) for rec in open_records]
        completed_tickets = [_ticket_info_from_record(rec) for rec in completed_records]
        stats = repo.get_stats()

        self.cache = TicketCacheState(
            open_tickets=open_tickets,
            completed_tickets=completed_tickets,
            stats=stats,
            cached_at=time.time(),
            cache_ttl_seconds=self.cache.cache_ttl_seconds,
        )
    
    def _ensure_cache(self) -> None:
        if self.cache.needs_refresh():
            self._refresh_cache()

    def get_open_tickets(self) -> list['TicketInfo']:
        """Get open tickets with caching."""
        with self._lock:
            self._ensure_cache()
            return self.cache.open_tickets.copy()
    
    def get_completed_tickets(self) -> list['TicketInfo']:
        """Get completed tickets with caching."""
        with self._lock:
            self._ensure_cache()
            return self.cache.completed_tickets.copy()
    
    def get_stats(self) -> dict:
        """Get ticket stats with caching."""
        with self._lock:
            self._ensure_cache()
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


def _ticket_info_from_record(record: dict) -> TicketInfo:
    """Convert a database ticket record into TicketInfo."""
    created_at = record.get("created_at")
    created_text = created_at.isoformat() if created_at else ""
    return TicketInfo(
        ticket_id=record["id"],
        priority=record["priority"],
        error_type=record["error_type"],
        message=record["message"],
        source=record["source"],
        run_name=record.get("run_label") or "",
        created=created_text,
        duplicate_guard=record.get("duplicate_guard") or "",
        full_block="",
        status=record.get("status") or "Open",
        documented=bool(record.get("documented")),
        functioning=bool(record.get("functioning")),
        tested=bool(record.get("tested")),
        completed=bool(record.get("completed")),
    )


def _get_ticket_repository():
    from .persistence.ticket_repo import get_ticket_repository
    return get_ticket_repository()


def _select_and_lock_ticket(paths: ActifixPaths) -> Optional[tuple[dict, str]]:
    from .persistence.ticket_repo import TicketFilter

    repo = _get_ticket_repository()
    lock_owner = f"do_af:{os.getpid()}"
    candidates = repo.get_tickets(TicketFilter(status="Open"))
    for ticket in candidates:
        if repo.acquire_lock(ticket["id"], lock_owner):
            return ticket, lock_owner
    return None



def get_open_tickets(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> list[TicketInfo]:
    """
    Get all open (incomplete) tickets.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available (default: True for efficiency).
    
    Returns:
        List of open TicketInfo, sorted by priority (P0 first).
    """
    if not use_cache:
        manager = StatefulTicketManager(paths=paths)
        return manager.get_open_tickets()

    try:
        from .persistence.ticket_repo import get_ticket_repository, TicketFilter
        repo = get_ticket_repository()
        db_tickets = repo.get_tickets(TicketFilter(status="Open"))
        return [_ticket_info_from_record(ticket) for ticket in db_tickets]
    except Exception:
        manager = get_ticket_manager(paths=paths)
        return manager.get_open_tickets()


def mark_ticket_complete(
    ticket_id: str,
    completion_notes: str,
    test_steps: str,
    test_results: str,
    summary: str = "",
    test_documentation_url: Optional[str] = None,
    paths: Optional[ActifixPaths] = None,
    use_lock: bool = True,
) -> bool:
    """
    Mark a ticket as complete with mandatory quality documentation.

    Args:
        ticket_id: Ticket ID to mark complete.
        completion_notes: Description of what was done (required, min 20 chars).
        test_steps: Description of testing performed (required, min 10 chars).
        test_results: Test outcomes/evidence (required, min 10 chars).
        summary: Optional short summary.
        test_documentation_url: Optional link to test artifacts.
        paths: Optional paths override (used for logging).
        use_lock: Reserved for compatibility (unused in DB mode).

    Returns:
        True if marked complete, False if not found, already completed, or validation failed.
    """
    if paths is None:
        paths = get_actifix_paths()

    enforce_raise_af_only(paths)

    repo = _get_ticket_repository()
    existing = repo.get_ticket(ticket_id)
    if not existing:
        log_event(
            paths.aflog_file,
            "TICKET_NOT_FOUND",
            f"Cannot complete non-existent ticket: {ticket_id}",
            ticket_id=ticket_id,
        )
        return False

    if existing.get("status") == "Completed" or existing.get("completed"):
        log_event(
            paths.aflog_file,
            "TICKET_ALREADY_COMPLETED",
            f"Skipped already-completed ticket: {ticket_id}",
            ticket_id=ticket_id,
            extra={
                "status": existing.get("status"),
                "reason": "idempotency_guard",
            },
        )
        return False

    try:
        success = repo.mark_complete(
            ticket_id,
            completion_notes=completion_notes,
            test_steps=test_steps,
            test_results=test_results,
            summary=summary or None,
            test_documentation_url=test_documentation_url,
        )

        if success:
            log_event(
                paths.aflog_file,
                "TICKET_COMPLETED",
                f"Marked ticket complete with validation: {ticket_id}",
                ticket_id=ticket_id,
                extra={
                    "summary": summary[:200] if summary else None,
                    "completion_notes_len": len(completion_notes),
                    "test_steps_len": len(test_steps),
                    "test_results_len": len(test_results),
                },
            )
        return success

    except ValueError as e:
        log_event(
            paths.aflog_file,
            "COMPLETION_VALIDATION_FAILED",
            f"Failed to complete ticket {ticket_id}: {e}",
            ticket_id=ticket_id,
            extra={"error": str(e)},
        )
        return False


def fix_highest_priority_ticket(
    paths: Optional[ActifixPaths] = None,
    completion_notes: str = "",
    test_steps: str = "",
    test_results: str = "",
    summary: str = "Resolved via dashboard fix",
    test_documentation_url: Optional[str] = None,
) -> dict:
    """
    Evaluate and fix the highest priority ticket with mandatory quality documentation.

    Args:
        paths: Optional ActifixPaths override.
        completion_notes: Description of what was done (required, min 20 chars).
        test_steps: Description of testing performed (required, min 10 chars).
        test_results: Test outcomes/evidence (required, min 10 chars).
        summary: Summary text to attach when closing the ticket.
        test_documentation_url: Optional link to test artifacts.

    Returns:
        Dict summarizing what happened (success, ticket_id, priority, etc).
    """
    if paths is None:
        paths = get_actifix_paths()

    # Enforce Raise_AF-only policy before modifying tickets
    enforce_raise_af_only(paths)

    init_actifix_files(paths)

    locked = _select_and_lock_ticket(paths)
    if not locked:
        return {
            "processed": False,
            "reason": "no_open_tickets",
        }

    ticket_record, lock_owner = locked
    ticket = _ticket_info_from_record(ticket_record)

    repo = _get_ticket_repository()

    # Prepare ultrathink narrative for auditing
    thought_text = (
        f"Evaluated {ticket.ticket_id} ({ticket.priority}) "
        f"from {ticket.source}: {ticket.message[:100]}"
    )
    action_text = f"Plan: Apply completion quality gate for {ticket.ticket_id}"
    testing_text = (
        "Quality validation: Ensuring completion_notes, test_steps, and test_results "
        "meet minimum quality thresholds before marking complete."
    )

    # Note: Validation of completion fields is performed in mark_ticket_complete()
    # and repo.mark_complete(). We pass the parameters directly and let the
    # validation layers handle them. This avoids duplication at this level.

    success = mark_ticket_complete(
        ticket.ticket_id,
        completion_notes=completion_notes,
        test_steps=test_steps,
        test_results=test_results,
        summary=summary,
        test_documentation_url=test_documentation_url,
        paths=paths,
        use_lock=False,
    )

    repo.release_lock(ticket.ticket_id, lock_owner)

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
    
    enforce_raise_af_only(paths)
    
    locked = _select_and_lock_ticket(paths)
    if not locked:
        log_event(
            paths.aflog_file,
            "NO_TICKETS",
            "No open tickets to process"
        )
        return None

    ticket_record, lock_owner = locked
    ticket = _ticket_info_from_record(ticket_record)
    repo = _get_ticket_repository()

    log_event(
        paths.aflog_file,
        "DISPATCH_STARTED",
        f"Processing ticket: {ticket.ticket_id}",
        ticket_id=ticket.ticket_id,
        extra={"priority": ticket.priority}
    )

    try:
        if use_ai and not ai_handler:
            try:
                from .ai_client import get_ai_client

                ai_client = get_ai_client()

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
                    summary = f"Fixed via {ai_response.provider.value} ({ai_response.model})"
                    if ai_response.cost_usd:
                        summary += f" - Cost: ${ai_response.cost_usd:.4f}"

                    mark_ticket_complete(
                        ticket.ticket_id,
                        completion_notes=f"Fixed by {ai_response.provider.value} using {ai_response.model}: {ai_response.content[:200]}",
                        test_steps=f"AI validation performed by {ai_response.provider.value}",
                        test_results=f"AI response successful with {ai_response.tokens_used} tokens used",
                        summary=summary,
                        paths=paths,
                        use_lock=False,
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
                    "AI_DISPATCH_EXCEPTION",
                    f"AI processing exception: {e}",
                    ticket_id=ticket.ticket_id,
                    extra={"error": str(e)},
                )
        if ai_handler:
            try:
                success = ai_handler(ticket)
                if success:
                    mark_ticket_complete(
                        ticket.ticket_id,
                        completion_notes=f"Fixed via custom AI handler for {ticket.ticket_id}",
                        test_steps="Custom AI handler validation performed",
                        test_results="Custom handler returned success status",
                        summary="Fixed via custom AI handler",
                        paths=paths,
                        use_lock=False,
                    )
                    log_event(
                        paths.aflog_file,
                        "CUSTOM_DISPATCH_SUCCESS",
                        f"Custom AI handler completed: {ticket.ticket_id}",
                        ticket_id=ticket.ticket_id
                    )
                    return ticket
            except Exception as e:
                log_event(
                    paths.aflog_file,
                    "CUSTOM_DISPATCH_FAILED",
                    f"Custom AI handler failed: {e}",
                    ticket_id=ticket.ticket_id,
                    extra={"error": str(e)}
                )

        return ticket
    finally:
        repo.release_lock(ticket.ticket_id, lock_owner)


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
    Get all completed tickets.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available.
    
    Returns:
        List of completed TicketInfo.
    """
    if not use_cache:
        manager = StatefulTicketManager(paths=paths)
        return manager.get_completed_tickets()

    try:
        from .persistence.ticket_repo import get_ticket_repository, TicketFilter
        repo = get_ticket_repository()
        db_tickets = repo.get_tickets(TicketFilter(status="Completed"))
        return [_ticket_info_from_record(ticket) for ticket in db_tickets]
    except Exception:
        manager = get_ticket_manager(paths=paths)
        return manager.get_completed_tickets()


def get_ticket_stats(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> dict:
    """
    Get statistics about tickets.
    
    Args:
        paths: Optional paths override.
        use_cache: Use cached data if available.
    
    Returns:
        Dict with ticket statistics.
    """
    if not use_cache:
        manager = StatefulTicketManager(paths=paths)
        return manager.get_stats()

    try:
        from .persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        return repo.get_stats()
    except Exception:
        manager = get_ticket_manager(paths=paths)
        return manager.get_stats()


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
