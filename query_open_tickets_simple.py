#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Query for Open Tickets

Quick script to list all open tickets from the actifix database.
Shows ticket ID, priority, and title for each ticket.
"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from actifix.persistence.ticket_repo import get_ticket_repository


def main():
    """Query and display open tickets in a simple format."""

    try:
        repo = get_ticket_repository()
        tickets = repo.get_open_tickets()

        if not tickets:
            print("No open tickets found.")
            return

        print(f"\n{'ID':<20} {'Priority':<10} {'Title':<70}")
        print("-" * 100)

        for ticket in tickets:
            ticket_id = ticket['id']
            priority = ticket['priority']
            title = ticket['message'][:68]
            print(f"{ticket_id:<20} {priority:<10} {title:<70}")

        print("-" * 100)
        print(f"\nTotal: {len(tickets)} open tickets\n")

        # Summary by priority
        priority_counts = {}
        for ticket in tickets:
            priority = ticket['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        print("Breakdown by priority:")
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = priority_counts.get(priority, 0)
            if count > 0:
                print(f"  {priority}: {count} ticket(s)")
        print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
