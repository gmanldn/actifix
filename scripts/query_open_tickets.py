#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query Open Tickets Script

This script connects to the actifix database and retrieves all open tickets,
sorted by priority (P0 first, then P1, P2, P3, P4).

For each ticket, it prints: ticket_id, priority, title, description
"""

import sys
from pathlib import Path

# Add src directory to path to import actifix modules
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from actifix.persistence.ticket_repo import get_ticket_repository


def main():
    """Main function to query and display open tickets."""

    try:
        # Get the ticket repository
        repo = get_ticket_repository()

        # Get all open tickets (automatically sorted by priority)
        open_tickets = repo.get_open_tickets()

        if not open_tickets:
            print("No open tickets found.")
            return

        print(f"Found {len(open_tickets)} open tickets:\n")
        print("=" * 100)

        # Priority order for sorting in output
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}

        # Print tickets
        for ticket in open_tickets:
            ticket_id = ticket['id']
            priority = ticket['priority']
            error_type = ticket['error_type']
            message = ticket['message']
            status = ticket['status']
            created_at = ticket['created_at']

            print(f"\nTicket ID:     {ticket_id}")
            print(f"Priority:      {priority}")
            print(f"Status:        {status}")
            print(f"Error Type:    {error_type}")
            print(f"Title:         {message}")
            print(f"Created At:    {created_at}")

            # Print optional fields if they exist
            if ticket.get('stack_trace'):
                print(f"Stack Trace:   {ticket['stack_trace'][:100]}..." if len(str(ticket['stack_trace'])) > 100 else f"Stack Trace:   {ticket['stack_trace']}")

            if ticket.get('ai_remediation_notes'):
                print(f"AI Notes:      {ticket['ai_remediation_notes'][:100]}..." if len(str(ticket['ai_remediation_notes'])) > 100 else f"AI Notes:      {ticket['ai_remediation_notes']}")

            if ticket.get('owner'):
                print(f"Owner:         {ticket['owner']}")

            if ticket.get('locked_by'):
                print(f"Locked By:     {ticket['locked_by']}")

            print("-" * 100)

        # Print summary statistics
        print(f"\nSummary: {len(open_tickets)} open tickets total")

        # Count by priority
        priority_counts = {}
        for ticket in open_tickets:
            priority = ticket['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        print("\nBreakdown by priority:")
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = priority_counts.get(priority, 0)
            if count > 0:
                print(f"  {priority}: {count} ticket(s)")

        print("=" * 100)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
