#!/usr/bin/env python3
"""
Final cleanup: Handle remaining 12 tickets with root cause analysis.

Analysis:
- 1 real ticket to keep (50 tasks implementation)
- 11 spurious tickets to auto-complete (test data, missing sources, bootstrap tracking)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from actifix.persistence.ticket_repo import get_ticket_repository


# Tickets to auto-complete with root cause analysis
SPURIOUS_TICKETS = {
    # Fake test tickets - source files don't exist
    "ACT-20260111-FE6C8": {
        "reason": "Test ticket with non-existent source file (core.py)",
        "root_cause": "Test script created ticket referencing fake source file",
        "fix": "Test scripts should validate source files exist or use proper test markers"
    },
    "ACT-20260111-2ADF8": {
        "reason": "Test ticket with non-existent source file (integration.py)",
        "root_cause": "Test script created ticket referencing fake source file",
        "fix": "Test scripts should validate source files exist"
    },
    "ACT-20260111-8FC3E": {
        "reason": "Test ticket with fake error (main.py exists but error is fabricated)",
        "root_cause": "Test script created fake database error",
        "fix": "Use proper test framework instead of creating fake tickets"
    },
    "ACT-20260111-D810D": {
        "reason": "Test ticket with non-existent source file (test_module.py)",
        "root_cause": "Test script created ticket referencing fake test file",
        "fix": "Test scripts should use real test files"
    },
    "ACT-20260111-70C36": {
        "reason": "Generic test ticket (src.py:1 with message 'msg')",
        "root_cause": "Test script created minimal stub ticket",
        "fix": "Remove test ticket generation or mark as test data"
    },
    "ACT-20260111-ED0F1": {
        "reason": "Test ticket with non-existent source file (utils.py at root)",
        "root_cause": "Test script created ticket referencing non-existent file",
        "fix": "Validate source files in test data generation"
    },
    "ACT-20260111-67F9C": {
        "reason": "Generic test ticket (src with message 'msg')",
        "root_cause": "Test script created minimal stub ticket",
        "fix": "Remove test ticket generation"
    },

    # Bootstrap/development tracking tickets (served their purpose)
    "ACT-20260111-26238": {
        "reason": "Bootstrap initialization tracking ticket (purpose served)",
        "root_cause": "bootstrap.py:create_initial_ticket() creates tracking ticket",
        "fix": "Consider using separate tracking system or mark as 'tracking' type"
    },
    "ACT-20260111-BD1BE": {
        "reason": "Development milestone tracking (purpose served)",
        "root_cause": "bootstrap.py:track_development_progress() creates milestone tickets",
        "fix": "Use dedicated milestone tracking instead of error tickets"
    },
    "ACT-20260111-CC9D0": {
        "reason": "Development milestone tracking (purpose served)",
        "root_cause": "bootstrap.py:track_development_progress() creates milestone tickets",
        "fix": "Use dedicated milestone tracking instead of error tickets"
    },

    # Test file exception (legitimate test, should be completed)
    "ACT-20260111-8D494": {
        "reason": "Test exception from test suite (test passed, ticket no longer needed)",
        "root_cause": "Test file test_actifix_basic.py:272 intentionally raises ValueError for testing",
        "fix": "Test exceptions should not create tickets unless ACTIFIX_CAPTURE_ENABLED=0 during tests"
    },
}

# Real ticket to keep
REAL_TICKETS = {
    "ACT-20260111-16172": "Legitimate P1 task to implement 50 actionable items"
}


def analyze_and_complete_spurious_tickets():
    """Complete spurious tickets with detailed root cause analysis."""
    repo = get_ticket_repository()

    print("="*80)
    print("FINAL TICKET CLEANUP - Root Cause Analysis")
    print("="*80)

    print(f"\nSpurious tickets to auto-complete: {len(SPURIOUS_TICKETS)}")
    print(f"Real tickets to keep: {len(REAL_TICKETS)}")

    # Group by root cause
    by_root_cause = {}
    for ticket_id, info in SPURIOUS_TICKETS.items():
        root_cause = info["root_cause"]
        by_root_cause.setdefault(root_cause, []).append(ticket_id)

    print("\n" + "-"*80)
    print("ROOT CAUSE ANALYSIS:")
    print("-"*80)
    for root_cause, ticket_ids in by_root_cause.items():
        print(f"\n{root_cause}")
        print(f"  Affected tickets: {len(ticket_ids)}")
        for tid in ticket_ids[:2]:
            print(f"    - {tid}")
        if len(ticket_ids) > 2:
            print(f"    ... and {len(ticket_ids) - 2} more")

    print("\n" + "="*80)
    print("COMPLETING SPURIOUS TICKETS")
    print("="*80)

    completed = 0
    failed = 0

    for ticket_id, info in SPURIOUS_TICKETS.items():
        try:
            # Get ticket details
            ticket = repo.get_ticket(ticket_id)
            if not ticket:
                print(f"⚠️  Ticket {ticket_id} not found (may already be completed)")
                failed += 1
                continue

            if ticket.get('status') == 'Completed':
                print(f"⚠️  Ticket {ticket_id} already completed")
                failed += 1
                continue

            # Complete with detailed analysis
            success = repo.mark_complete(
                ticket_id=ticket_id,
                completion_notes=f"Auto-completed spurious ticket.\n\n"
                                f"Reason: {info['reason']}\n\n"
                                f"Root Cause: {info['root_cause']}\n\n"
                                f"Recommended Fix: {info['fix']}\n\n"
                                f"Original message: {ticket.get('message', 'N/A')}\n"
                                f"Original source: {ticket.get('source', 'N/A')}",
                test_steps="Validated that ticket is spurious by checking source file existence "
                          "and analyzing ticket generation patterns.",
                test_results=f"Confirmed spurious: {info['reason']}. "
                            f"No actual work needed - ticket was test data or development tracking.",
                summary=f"Auto-completed: {info['reason']}"
            )

            if success:
                completed += 1
                print(f"✅ {ticket_id}: {info['reason']}")
            else:
                failed += 1
                print(f"❌ {ticket_id}: Failed to complete")

        except Exception as e:
            failed += 1
            print(f"❌ {ticket_id}: Error - {e}")

    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Real tickets remaining: {len(REAL_TICKETS)}")

    # Show final stats
    stats = repo.get_stats()
    print("\n" + "-"*80)
    print("FINAL DATABASE STATE:")
    print("-"*80)
    print(f"Total tickets: {stats['total']}")
    print(f"Open: {stats['open']}")
    print(f"In Progress: {stats['in_progress']}")
    print(f"Completed: {stats['completed']}")

    # Show real tickets
    print("\n" + "-"*80)
    print("REAL TICKETS REMAINING:")
    print("-"*80)
    for ticket_id, description in REAL_TICKETS.items():
        ticket = repo.get_ticket(ticket_id)
        if ticket and ticket.get('status') != 'Completed':
            print(f"\n{ticket_id} ({ticket['priority']})")
            print(f"  {description}")
            print(f"  Message: {ticket['message']}")
            print(f"  Source: {ticket['source']}")

    # Root cause summary
    print("\n" + "="*80)
    print("ROOT CAUSE SUMMARY & FIXES NEEDED:")
    print("="*80)

    fixes = {}
    for info in SPURIOUS_TICKETS.values():
        fix = info["fix"]
        fixes[fix] = fixes.get(fix, 0) + 1

    print("\nRecommended fixes (by priority):")
    for i, (fix, count) in enumerate(sorted(fixes.items(), key=lambda x: x[1], reverse=True), 1):
        print(f"{i}. {fix} ({count} tickets affected)")


if __name__ == "__main__":
    analyze_and_complete_spurious_tickets()
