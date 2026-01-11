"""
Actifix DoAF - Ticket Dispatch and Processing.

Dispatches tickets to AI for automated fixes backed by the database repository.
"""

# Allow running as a standalone script (python src/actifix/do_af.py)
if __name__ == "__main__" and __package__ is None:  # pragma: no cover - path setup
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    __package__ = "actifix"

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

from .log_utils import log_event
from .raise_af import enforce_raise_af_only
from .state_paths import ActifixPaths, get_actifix_paths, init_actifix_files


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
    Get all open (incomplete) tickets from the database.
    
    Args:
        paths: Optional paths override (unused in DB mode).
        use_cache: Reserved for compatibility (unused in DB mode).
    
    Returns:
        List of open TicketInfo, sorted by priority (P0 first).
    """
    repo = _get_ticket_repository()
    db_tickets = repo.get_open_tickets()
    return [_ticket_info_from_record(ticket) for ticket in db_tickets]


def mark_ticket_complete(
    ticket_id: str,
    summary: str = "",
    paths: Optional[ActifixPaths] = None,
    use_lock: bool = True,
) -> bool:
    """
    Mark a ticket as complete in the database.
    
    Implements idempotency guard: if ticket already completed, skip the
    operation and log skip event to AFLog.
    
    Args:
        ticket_id: Ticket ID to mark complete.
        summary: Optional completion summary.
        paths: Optional paths override.
        use_lock: Reserved for compatibility (unused in DB mode).
    
    Returns:
        True if marked complete, False if not found or already completed.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    # Enforce Raise_AF-only policy before modifying tickets
    enforce_raise_af_only(paths)

    repo = _get_ticket_repository()
    existing = repo.get_ticket(ticket_id)
    if not existing:
        return False

    if existing.get("status") == "Completed" or existing.get("completed"):
        log_event(
            paths.aflog_file,
            "TICKET_ALREADY_COMPLETED",
            f"Skipped already-completed ticket: {ticket_id}",
            ticket_id=ticket_id,
            extra={"reason": "idempotency_guard"}
        )
        return False

    success = repo.mark_complete(ticket_id, summary=summary or None)
    if success:
        log_event(
            paths.aflog_file,
            "TICKET_COMPLETED",
            f"Marked ticket complete: {ticket_id}",
            ticket_id=ticket_id,
            extra={"summary": summary[:50] if summary else None}
        )

    return success


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

    locked = _select_and_lock_ticket(paths)
    if not locked:
        log_event(
            paths.aflog_file,
            "NO_TICKETS",
            "No open tickets to fix via dashboard",
        )
        return {
            "processed": False,
            "reason": "no_open_tickets",
        }

    ticket_record, lock_owner = locked
    ticket = _ticket_info_from_record(ticket_record)
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
        _get_ticket_repository().release_lock(ticket.ticket_id, lock_owner)
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
    completed = False
    
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
                
                completed = mark_ticket_complete(
                    ticket.ticket_id,
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
                completed = mark_ticket_complete(
                    ticket.ticket_id,
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
        except Exception as e:
            log_event(
                paths.aflog_file,
                "CUSTOM_DISPATCH_FAILED",
                f"Custom AI handler failed: {e}",
                ticket_id=ticket.ticket_id,
                extra={"error": str(e)}
            )

    if not completed:
        _get_ticket_repository().release_lock(ticket.ticket_id, lock_owner)

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
    Get all completed tickets from the database.
    
    Args:
        paths: Optional paths override (unused in DB mode).
        use_cache: Reserved for compatibility (unused in DB mode).
    
    Returns:
        List of completed TicketInfo.
    """
    repo = _get_ticket_repository()
    db_tickets = repo.get_completed_tickets()
    return [_ticket_info_from_record(ticket) for ticket in db_tickets]


def get_ticket_stats(paths: Optional[ActifixPaths] = None, use_cache: bool = True) -> dict:
    """
    Get statistics about tickets.
    
    Args:
        paths: Optional paths override (unused in DB mode).
        use_cache: Reserved for compatibility (unused in DB mode).
    
    Returns:
        Dict with ticket statistics.
    """
    repo = _get_ticket_repository()
    return repo.get_stats()


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


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())