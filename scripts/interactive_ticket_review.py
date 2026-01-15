#!/usr/bin/env python3
"""
Interactive Ticket Review and Completion Workflow

This script guides users through a rigorous process to complete tickets:
1. Display ticket details
2. Require implementation description (completion_notes, min 20 chars)
3. Require testing documentation (test_steps, min 10 chars)
4. Require test results/evidence (test_results, min 10 chars)
5. Validate and mark complete or show validation errors

The goal is to ensure NO ticket can be marked complete without
real evidence of implementation and testing.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.do_af import mark_ticket_complete
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.state_paths import get_actifix_paths


def display_ticket(ticket: dict) -> None:
    """Display ticket information for review."""
    print("\n" + "=" * 70)
    print(f"TICKET: {ticket['id']}")
    print("=" * 70)
    print(f"Priority:     {ticket['priority']}")
    print(f"Type:         {ticket['error_type']}")
    print(f"Status:       {ticket['status']}")
    print(f"Source:       {ticket['source']}")
    if ticket.get('run_label'):
        print(f"Run Label:    {ticket['run_label']}")
    print(f"\nMessage:\n{ticket['message']}")
    if ticket.get('stack_trace'):
        print(f"\nStack Trace:\n{ticket['stack_trace'][:500]}{'...' if len(ticket.get('stack_trace', '')) > 500 else ''}")
    print("=" * 70)


def validate_input(field_name: str, value: str, min_length: int) -> tuple[bool, str]:
    """
    Validate input field.

    Returns:
        (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"

    if len(value.strip()) < min_length:
        return False, f"{field_name} too short (min {min_length} chars, got {len(value.strip())})"

    return True, ""


def prompt_for_completion_notes() -> str | None:
    """Prompt for completion notes with validation."""
    print("\n" + "-" * 70)
    print("COMPLETION NOTES (What work was done to fix this ticket?)")
    print(f"Requirements: Must describe implementation (min 20 characters)")
    print(f"Example: 'Fixed null pointer exception in database query by adding')
    print(f"         'null checks at lines 42-45. Added defensive validation.'")
    print("-" * 70)

    while True:
        value = input("\nEnter completion notes: ").strip()
        is_valid, error = validate_input("Completion notes", value, 20)

        if is_valid:
            return value
        else:
            print(f"❌ INVALID: {error}")
            retry = input("Try again? (y/n): ").lower().strip()
            if retry != 'y':
                return None


def prompt_for_test_steps() -> str | None:
    """Prompt for test steps with validation."""
    print("\n" + "-" * 70)
    print("TEST STEPS (How was this ticket tested?)")
    print(f"Requirements: Must describe testing method (min 10 characters)")
    print(f"Example: 'Ran pytest test_null_checks.py. Verified with gdb')
    print(f"         'debugger. Added 15 new test cases.'")
    print("-" * 70)

    while True:
        value = input("\nEnter test steps: ").strip()
        is_valid, error = validate_input("Test steps", value, 10)

        if is_valid:
            return value
        else:
            print(f"❌ INVALID: {error}")
            retry = input("Try again? (y/n): ").lower().strip()
            if retry != 'y':
                return None


def prompt_for_test_results() -> str | None:
    """Prompt for test results with validation."""
    print("\n" + "-" * 70)
    print("TEST RESULTS (What were the outcomes? What passed?)")
    print(f"Requirements: Must provide evidence of testing (min 10 characters)")
    print(f"Example: 'All 47 tests passed. Coverage increased to 98%.')
    print(f"         'No null pointer exceptions. Regression tests green.'")
    print("-" * 70)

    while True:
        value = input("\nEnter test results: ").strip()
        is_valid, error = validate_input("Test results", value, 10)

        if is_valid:
            return value
        else:
            print(f"❌ INVALID: {error}")
            retry = input("Try again? (y/n): ").lower().strip()
            if retry != 'y':
                return None


def complete_ticket(ticket: dict, paths) -> bool:
    """Complete a single ticket through the workflow."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║ TICKET COMPLETION WORKFLOW - QUALITY GATES ENFORCED         ║")
    print("╚" + "=" * 68 + "╝")

    display_ticket(ticket)

    # Get completion notes
    completion_notes = prompt_for_completion_notes()
    if completion_notes is None:
        print("⊘ Skipped ticket completion (incomplete notes)")
        return False

    # Get test steps
    test_steps = prompt_for_test_steps()
    if test_steps is None:
        print("⊘ Skipped ticket completion (incomplete test steps)")
        return False

    # Get test results
    test_results = prompt_for_test_results()
    if test_results is None:
        print("⊘ Skipped ticket completion (incomplete test results)")
        return False

    # Confirm before completing
    print("\n" + "-" * 70)
    print("REVIEW BEFORE COMPLETION")
    print("-" * 70)
    print(f"Completion Notes ({len(completion_notes)} chars):\n  {completion_notes}")
    print(f"\nTest Steps ({len(test_steps)} chars):\n  {test_steps}")
    print(f"\nTest Results ({len(test_results)} chars):\n  {test_results}")
    print("-" * 70)

    confirm = input("\nMark ticket as COMPLETED? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("⊘ Cancelled - ticket not marked complete")
        return False

    # Mark complete with validation
    try:
        success = mark_ticket_complete(
            ticket['id'],
            completion_notes=completion_notes,
            test_steps=test_steps,
            test_results=test_results,
            summary=f"Completed via interactive review: {ticket['error_type']}",
            paths=paths
        )

        if success:
            print("\n✓ TICKET COMPLETED SUCCESSFULLY")
            print(f"  ID: {ticket['id']}")
            print(f"  Status: Marked as Completed")
            print(f"  Documentation: Stored with completion evidence")
            return True
        else:
            print("\n✗ TICKET COMPLETION FAILED")
            print(f"  Reason: Unknown error during database update")
            return False

    except ValueError as e:
        print(f"\n✗ VALIDATION ERROR: {e}")
        print("  Your input was rejected. Please ensure:")
        print(f"    - Completion notes: min 20 chars (you provided {len(completion_notes)})")
        print(f"    - Test steps: min 10 chars (you provided {len(test_steps)})")
        print(f"    - Test results: min 10 chars (you provided {len(test_results)})")
        return False


def main():
    """Main interactive review workflow."""
    os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'

    paths = get_actifix_paths()
    repo = get_ticket_repository()

    print("\n" + "╔" + "=" * 68 + "╗")
    print("║ ACTIFIX INTERACTIVE TICKET COMPLETION REVIEW                ║")
    print("║                                                              ║")
    print("║ This tool ensures quality gates are applied before marking  ║")
    print("║ tickets complete. Every ticket requires:                   ║")
    print("║   • Implementation description (min 20 chars)              ║")
    print("║   • Testing methodology (min 10 chars)                    ║")
    print("║   • Test evidence/results (min 10 chars)                  ║")
    print("║                                                              ║")
    print("║ NO ticket can be marked complete without this evidence.    ║")
    print("╚" + "=" * 68 + "╝\n")

    # Get open tickets
    tickets = repo.get_open_tickets(limit=None)

    if not tickets:
        print("No open tickets found. All tickets are completed!")
        return 0

    print(f"Found {len(tickets)} open tickets\n")

    # Prompt for how many to review
    try:
        max_tickets_str = input(f"How many tickets to review? (1-{len(tickets)}): ").strip()
        max_tickets = int(max_tickets_str)
        if max_tickets < 1:
            max_tickets = 1
        elif max_tickets > len(tickets):
            max_tickets = len(tickets)
    except ValueError:
        print("Invalid input, defaulting to 1 ticket")
        max_tickets = 1

    completed = 0
    skipped = 0

    for idx, ticket in enumerate(tickets[:max_tickets], 1):
        print(f"\n[{idx}/{max_tickets}] Processing: {ticket['id']}")

        action = input("(c)omplete, (s)kip, or (q)uit? ").lower().strip()

        if action == 'q':
            print("\n⊘ Exiting review session")
            break

        if action == 's':
            print("Skipped")
            skipped += 1
            continue

        if action == 'c':
            if complete_ticket(ticket, paths):
                completed += 1
            else:
                skipped += 1

    # Summary
    print("\n" + "=" * 70)
    print("REVIEW SESSION SUMMARY")
    print("=" * 70)
    print(f"Completed: {completed} tickets")
    print(f"Skipped:   {skipped} tickets")
    print(f"Total:     {completed + skipped} reviewed of {len(tickets)} open")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⊘ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
