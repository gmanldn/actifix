#!/usr/bin/env python3
"""
Cleanup Script: Auto-complete bulk-generated test tickets

This script identifies and auto-completes simple/trivial tickets based on rules:
1. Tickets from known test/bulk generation scripts
2. Tickets with specific test error types
3. Low priority tickets from test sources

Rules can be adjusted before execution.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from actifix.persistence.ticket_repo import get_ticket_repository, TicketFilter


# CONFIGURATION: Auto-completion rules
AUTO_COMPLETE_RULES = {
    "test_sources": [
        "start_weakness_analysis_300.py",
        "start_ai_elegance_300.py",
        "start_ai_module_dev_200.py",
        "start_200_weak_area_tickets.py",
        "start_200_module_quality_tasks.py",
        "simple_ticket_attack.py:attack_simple_tickets",
        "start_100_self_repair_tasks.py",
        "verify_throttling.py:1",
        "verify_throttling.py:10",
        "do_af_concurrency.py",
    ],
    "test_error_types": [
        "SimpleTicket",
        "WeaknessAnalysis",
        "CodeElegance",
        "WeakArea",
        "ModuleQualityTask",
        "AIModuleDevelopment",
        "SelfRepairTask",
        "TestError",
        "ConcurrencyTest",
    ],
    # Additional rules for test patterns
    "test_message_patterns": [
        "Simple ticket #",
        "P0 critical error number",
        "P0 critical error 0",
        "P2 error",
        "P2 validation error in form field number",
        "P3 minor UI issue in component variation",
    ],
}


def matches_test_source(ticket):
    """Check if ticket is from a known test source."""
    source = ticket.get("source", "")
    return any(test_source in source for test_source in AUTO_COMPLETE_RULES["test_sources"])


def matches_test_error_type(ticket):
    """Check if ticket has a test error type."""
    error_type = ticket.get("error_type", "")
    return error_type in AUTO_COMPLETE_RULES["test_error_types"]


def matches_test_message_pattern(ticket):
    """Check if ticket message matches test patterns."""
    message = ticket.get("message", "")
    return any(pattern in message for pattern in AUTO_COMPLETE_RULES["test_message_patterns"])


def is_trivial_ticket(ticket):
    """Determine if a ticket is trivial/test data."""
    return (
        matches_test_source(ticket)
        or matches_test_error_type(ticket)
        or matches_test_message_pattern(ticket)
    )


def preview_cleanup(dry_run=True):
    """Preview what tickets would be auto-completed."""
    repo = get_ticket_repository()

    # Get all open tickets
    open_tickets = repo.get_open_tickets()

    # Categorize tickets
    trivial_tickets = []
    real_tickets = []

    for ticket in open_tickets:
        if is_trivial_ticket(ticket):
            trivial_tickets.append(ticket)
        else:
            real_tickets.append(ticket)

    # Print summary
    print("\n" + "="*80)
    print("TICKET CLEANUP ANALYSIS")
    print("="*80)
    print(f"\nTotal open tickets: {len(open_tickets)}")
    print(f"Trivial/test tickets (would be auto-completed): {len(trivial_tickets)}")
    print(f"Real tickets (would be kept): {len(real_tickets)}")

    # Show breakdown by category
    print("\n" + "-"*80)
    print("TRIVIAL TICKETS BREAKDOWN:")
    print("-"*80)

    by_source = {}
    by_error_type = {}
    by_priority = {}

    for ticket in trivial_tickets:
        source = ticket.get("source", "unknown")
        error_type = ticket.get("error_type", "unknown")
        priority = ticket.get("priority", "unknown")

        by_source[source] = by_source.get(source, 0) + 1
        by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    print("\nBy Source:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    print("\nBy Error Type:")
    for error_type, count in sorted(by_error_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count}")

    print("\nBy Priority:")
    for priority, count in sorted(by_priority.items()):
        print(f"  {priority}: {count}")

    # Show sample of real tickets
    print("\n" + "-"*80)
    print("REAL TICKETS THAT WOULD BE KEPT (sample):")
    print("-"*80)

    for ticket in real_tickets[:10]:
        print(f"\n  ID: {ticket['id']}")
        print(f"  Priority: {ticket['priority']}")
        print(f"  Error Type: {ticket['error_type']}")
        print(f"  Message: {ticket['message'][:100]}")
        print(f"  Source: {ticket['source']}")

    if len(real_tickets) > 10:
        print(f"\n  ... and {len(real_tickets) - 10} more real tickets")

    return trivial_tickets, real_tickets


def execute_cleanup(trivial_tickets, batch_size=100):
    """Execute the cleanup by auto-completing trivial tickets."""
    repo = get_ticket_repository()

    print("\n" + "="*80)
    print("EXECUTING CLEANUP")
    print("="*80)

    completed_count = 0
    failed_count = 0

    total = len(trivial_tickets)

    for i, ticket in enumerate(trivial_tickets, 1):
        ticket_id = ticket['id']

        # Progress indicator
        if i % batch_size == 0 or i == total:
            print(f"Processing {i}/{total} tickets...")

        try:
            # Auto-complete with standardized notes
            success = repo.mark_complete(
                ticket_id=ticket_id,
                completion_notes=f"Auto-completed test/bulk-generated ticket. "
                                f"Source: {ticket.get('source', 'unknown')}. "
                                f"Error type: {ticket.get('error_type', 'unknown')}. "
                                f"This ticket was identified as test data during cleanup.",
                test_steps="Automated cleanup script identified this as test data based on source and error type patterns.",
                test_results="No testing required - ticket was generated by test/bulk generation scripts and does not represent real issues.",
                summary=f"Auto-completed test ticket from {ticket.get('source', 'unknown')}",
            )

            if success:
                completed_count += 1
            else:
                failed_count += 1
                print(f"  WARNING: Failed to complete ticket {ticket_id} (may already be completed)")

        except Exception as e:
            failed_count += 1
            print(f"  ERROR completing ticket {ticket_id}: {e}")

    print("\n" + "="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print(f"Successfully completed: {completed_count}")
    print(f"Failed/skipped: {failed_count}")
    print(f"Total processed: {total}")

    # Show final stats
    stats = repo.get_stats()
    print("\n" + "-"*80)
    print("FINAL DATABASE STATS:")
    print("-"*80)
    print(f"Total tickets: {stats['total']}")
    print(f"Open: {stats['open']}")
    print(f"In Progress: {stats['in_progress']}")
    print(f"Completed: {stats['completed']}")
    print(f"Deleted: {stats['deleted']}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-complete trivial/test tickets")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the cleanup (default is dry-run preview only)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    # Always preview first
    trivial_tickets, real_tickets = preview_cleanup()

    if not args.execute:
        print("\n" + "="*80)
        print("DRY RUN MODE - No tickets were modified")
        print("="*80)
        print("\nTo actually execute the cleanup, run with --execute flag:")
        print("  python cleanup_test_tickets.py --execute")
        return

    # Confirm before executing
    if not args.yes:
        print("\n" + "="*80)
        print("WARNING: This will auto-complete the trivial tickets listed above!")
        print("="*80)
        response = input("\nProceed with cleanup? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cleanup cancelled.")
            return

    # Execute cleanup
    execute_cleanup(trivial_tickets)


if __name__ == "__main__":
    main()
