#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticket Cleanup and Retention Policies

Provides automatic cleanup of old completed tickets and test/automation tickets.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


# Configuration defaults
DEFAULT_RETENTION_DAYS = 90  # Keep completed tickets for 90 days
DEFAULT_TEST_TICKET_RETENTION_DAYS = 7  # Keep test tickets for only 7 days


# Test/automation ticket patterns
TEST_SOURCES = {
    'start_weakness_analysis_300.py',
    'start_ai_elegance_300.py',
    'start_ai_module_dev_200.py',
    'start_200_weak_area_tickets.py',
    'start_200_module_quality_tasks.py',
    'start_100_self_repair_tasks.py',
    'simple_ticket_attack.py',
}

TEST_ERROR_TYPES = {
    'WeaknessAnalysis',
    'CodeElegance',
    'AIModuleDevelopment',
    'WeakArea',
    'ModuleQualityTask',
    'SelfRepairTask',
    'SimpleTicket',
    'TestError',
    'TestPerformance',
    'TestHang',
    'TestNetworkDependency',
    'TestCycleOptimization',
}


def is_test_ticket(ticket: Dict[str, Any]) -> bool:
    """
    Determine if a ticket is from test/automation scripts.

    Args:
        ticket: Ticket dictionary with source and error_type fields.

    Returns:
        True if this appears to be a test/automation ticket.
    """
    source = ticket.get('source', '')
    error_type = ticket.get('error_type', '')

    # Check if source matches known test scripts
    if any(test_src in source for test_src in TEST_SOURCES):
        return True

    # Check if error type is test-related
    if error_type in TEST_ERROR_TYPES:
        return True

    # Check for test patterns in source
    if 'test.' in source or 'test/' in source or 'pytest' in source.lower():
        return True

    return False


def get_ticket_age_days(ticket: Dict[str, Any]) -> float:
    """
    Calculate ticket age in days.

    Args:
        ticket: Ticket dictionary with created timestamp.

    Returns:
        Age in days.
    """
    created = ticket.get('created')
    if not created:
        return 0

    if isinstance(created, str):
        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        except Exception:
            return 0
    elif isinstance(created, datetime):
        created_dt = created
    else:
        return 0

    now = datetime.now(timezone.utc)
    if created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    age = now - created_dt
    return age.total_seconds() / 86400  # Convert to days


def apply_retention_policy(
    repo,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    test_ticket_retention_days: int = DEFAULT_TEST_TICKET_RETENTION_DAYS,
    dry_run: bool = True
) -> Dict[str, int]:
    """
    Apply retention policy to completed tickets.

    This will soft-delete old completed tickets based on retention policies:
    - Regular completed tickets older than retention_days
    - Test/automation tickets older than test_ticket_retention_days

    Args:
        repo: TicketRepository instance.
        retention_days: Days to keep regular completed tickets.
        test_ticket_retention_days: Days to keep test/automation tickets.
        dry_run: If True, don't actually delete, just report.

    Returns:
        Dict with counts of tickets that would be/were deleted.
    """
    from .ticket_repo import TicketFilter

    stats = {
        'completed_expired': 0,
        'test_tickets_expired': 0,
        'total_deleted': 0,
    }

    # Get all completed tickets
    completed_tickets = repo.get_tickets(TicketFilter(status='Completed'))

    tickets_to_delete = []

    for ticket in completed_tickets:
        age_days = get_ticket_age_days(ticket)
        is_test = is_test_ticket(ticket)

        should_delete = False

        if is_test and age_days > test_ticket_retention_days:
            stats['test_tickets_expired'] += 1
            should_delete = True
        elif not is_test and age_days > retention_days:
            stats['completed_expired'] += 1
            should_delete = True

        if should_delete:
            ticket_id = ticket.get('id') or ticket.get('ticket_id')
            if ticket_id:
                tickets_to_delete.append(ticket_id)

    stats['total_deleted'] = len(tickets_to_delete)

    if not dry_run and tickets_to_delete:
        for ticket_id in tickets_to_delete:
            try:
                repo.delete_ticket(ticket_id, soft_delete=True)
            except Exception as e:
                logger.warning(f"Failed to delete ticket {ticket_id}: {e}")

    return stats


def cleanup_test_tickets(
    repo,
    auto_complete: bool = True,
    dry_run: bool = True
) -> Dict[str, int]:
    """
    Cleanup open test/automation tickets.

    This will auto-complete or soft-delete open test tickets that shouldn't
    have been created in the first place.

    Args:
        repo: TicketRepository instance.
        auto_complete: If True, mark as completed instead of deleting.
        dry_run: If True, don't actually modify, just report.

    Returns:
        Dict with counts of tickets that would be/were cleaned up.
    """
    from .ticket_repo import TicketFilter

    stats = {
        'test_tickets_found': 0,
        'test_tickets_cleaned': 0,
    }

    # Get all open tickets
    open_tickets = repo.get_tickets(TicketFilter(status='Open'))

    tickets_to_clean = []

    for ticket in open_tickets:
        if is_test_ticket(ticket):
            stats['test_tickets_found'] += 1
            ticket_id = ticket.get('id') or ticket.get('ticket_id')
            if ticket_id:
                tickets_to_clean.append(ticket_id)

    stats['test_tickets_cleaned'] = len(tickets_to_clean)

    if not dry_run and tickets_to_clean:
        for ticket_id in tickets_to_clean:
            try:
                if auto_complete:
                    # Mark as completed with required documentation
                    repo.mark_complete(
                        ticket_id,
                        completion_notes=(
                            "Implementation: Auto-completed by cleanup policy - identified as test/automation ticket.\n"
                            "Files:\n"
                            "- src/actifix/persistence/ticket_cleanup.py"
                        ),
                        test_steps='Automated cleanup policy verification',
                        test_results='Ticket identified as test-generated and auto-completed per retention policy',
                        summary='Auto-cleanup: test ticket'
                    )
                else:
                    repo.delete_ticket(ticket_id, soft_delete=True)
            except Exception as e:
                logger.warning(f"Failed to clean up ticket {ticket_id}: {e}")

    return stats


def cleanup_duplicate_tickets(
    repo,
    min_age_hours: float = 24.0,
    dry_run: bool = True,
) -> Dict[str, int]:
    """
    Cleanup stale duplicate tickets by auto-completing older duplicates.

    A duplicate is identified by matching (message, source, error_type).
    The newest ticket in each duplicate group is kept open. Older tickets
    are auto-completed if they exceed min_age_hours.

    Args:
        repo: TicketRepository instance.
        min_age_hours: Minimum age in hours before auto-completing duplicates.
        dry_run: If True, don't modify tickets, just report.

    Returns:
        Dict with counts of duplicates found/cleaned/skipped.
    """
    from .ticket_repo import TicketFilter

    stats = {
        'duplicate_groups': 0,
        'duplicates_found': 0,
        'duplicates_closed': 0,
        'duplicates_skipped_locked': 0,
        'duplicates_skipped_recent': 0,
    }

    open_tickets = repo.get_tickets(TicketFilter(status='Open'))
    groups: Dict[tuple, list] = {}

    for ticket in open_tickets:
        key = (
            ticket.get('message') or '',
            ticket.get('source') or '',
            ticket.get('error_type') or '',
        )
        groups.setdefault(key, []).append(ticket)

    now = datetime.now(timezone.utc)

    for tickets in groups.values():
        if len(tickets) <= 1:
            continue
        stats['duplicate_groups'] += 1
        tickets_sorted = sorted(
            tickets,
            key=lambda t: t.get('created_at') or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        newest = tickets_sorted[0]
        older = tickets_sorted[1:]
        stats['duplicates_found'] += len(older)

        for ticket in older:
            if ticket.get('locked_by'):
                stats['duplicates_skipped_locked'] += 1
                continue
            created_at = ticket.get('created_at')
            if not isinstance(created_at, datetime):
                stats['duplicates_skipped_recent'] += 1
                continue
            age_hours = (now - created_at).total_seconds() / 3600.0
            if age_hours < min_age_hours:
                stats['duplicates_skipped_recent'] += 1
                continue
            if dry_run:
                stats['duplicates_closed'] += 1
                continue
            try:
                repo.mark_complete(
                    ticket['id'],
                    completion_notes=(
                        "Implementation: Auto-completed stale duplicate ticket; "
                        f"newer ticket remains open (latest id {newest.get('id')}).\n"
                        "Files:\n"
                        "- src/actifix/persistence/ticket_cleanup.py"
                    ),
                    test_steps="Automated duplicate cleanup policy execution.",
                    test_results="Ticket auto-completed as duplicate per cleanup policy.",
                    summary="Auto-cleanup: stale duplicate ticket",
                )
                stats['duplicates_closed'] += 1
            except Exception as exc:
                logger.warning(f"Failed to auto-complete duplicate ticket {ticket.get('id')}: {exc}")

    return stats


def run_automatic_cleanup(
    retention_days: int = DEFAULT_RETENTION_DAYS,
    test_ticket_retention_days: int = DEFAULT_TEST_TICKET_RETENTION_DAYS,
    auto_complete_test_tickets: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run automatic cleanup with retention policies.

    This is the main entry point for scheduled cleanup tasks.

    Args:
        retention_days: Days to keep regular completed tickets.
        test_ticket_retention_days: Days to keep test/automation tickets.
        auto_complete_test_tickets: Auto-complete open test tickets.
        dry_run: If True, don't actually modify, just report.

    Returns:
        Dict with cleanup statistics.
    """
    from .ticket_repo import get_ticket_repository

    repo = get_ticket_repository()

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dry_run': dry_run,
        'retention_policy': {},
        'test_cleanup': {},
    }

    # Apply retention policy to completed tickets
    retention_stats = apply_retention_policy(
        repo,
        retention_days=retention_days,
        test_ticket_retention_days=test_ticket_retention_days,
        dry_run=dry_run
    )
    results['retention_policy'] = retention_stats

    # Cleanup open test tickets
    if auto_complete_test_tickets:
        test_stats = cleanup_test_tickets(
            repo,
            auto_complete=True,
            dry_run=dry_run
        )
        results['test_cleanup'] = test_stats

    return results


def print_cleanup_report(results: Dict[str, Any]) -> None:
    """Print a formatted cleanup report."""
    print("\n" + "=" * 80)
    print("AUTOMATIC TICKET CLEANUP REPORT")
    print("=" * 80)
    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Mode: {'DRY RUN (no changes made)' if results['dry_run'] else 'EXECUTE (changes applied)'}")

    print("\n" + "-" * 80)
    print("RETENTION POLICY CLEANUP:")
    print("-" * 80)
    retention = results['retention_policy']
    print(f"  Regular completed tickets expired: {retention.get('completed_expired', 0)}")
    print(f"  Test tickets expired: {retention.get('test_tickets_expired', 0)}")
    print(f"  Total deleted: {retention.get('total_deleted', 0)}")

    if 'test_cleanup' in results:
        print("\n" + "-" * 80)
        print("TEST TICKET CLEANUP:")
        print("-" * 80)
        test = results['test_cleanup']
        print(f"  Open test tickets found: {test.get('test_tickets_found', 0)}")
        print(f"  Test tickets cleaned: {test.get('test_tickets_cleaned', 0)}")

    print("\n" + "=" * 80)
    if results['dry_run']:
        print("To apply these changes, run with dry_run=False")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    import sys

    dry_run = '--execute' not in sys.argv

    results = run_automatic_cleanup(dry_run=dry_run)
    print_cleanup_report(results)
