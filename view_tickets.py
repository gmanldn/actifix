#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to view the first 10 open tickets with full details.
Shows priority-sorted tickets with all context information.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from actifix.persistence.ticket_repo import TicketRepository, TicketFilter
from actifix.persistence.database import get_database_pool


def format_value(value, indent=0):
    """Format a value for display, handling None and complex types."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for k, v in value.items():
            formatted_v = format_value(v, indent + 2)
            spaces = "  " * (indent // 2 + 1)
            lines.append(f"{spaces}{k}: {formatted_v}")
        lines.append("  " * (indent // 2) + "}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            formatted_item = format_value(item, indent + 2)
            spaces = "  " * (indent // 2 + 1)
            lines.append(f"{spaces}- {formatted_item}")
        lines.append("  " * (indent // 2) + "]")
        return "\n".join(lines)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def main():
    """Retrieve and display the first 10 open tickets."""

    print("=" * 100)
    print("ACTIFIX TICKET VIEWER - First 10 Open Tickets (Priority Sorted)")
    print("=" * 100)
    print()

    # Initialize database and repository
    db_path = Path(__file__).parent / "data" / "actifix.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    print(f"Database: {db_path}")
    print()

    try:
        # Get repository
        repo = TicketRepository()

        # Get first 10 open tickets (sorted by priority by default)
        filter_criteria = TicketFilter(status="Open", limit=10)
        tickets = repo.get_tickets(filter_criteria)

        if not tickets:
            print("No open tickets found!")
            return 0

        print(f"Found {len(tickets)} open tickets\n")

        # Display each ticket
        for idx, ticket in enumerate(tickets, 1):
            print("-" * 100)
            print(f"TICKET {idx} of {len(tickets)}")
            print("-" * 100)

            # Core fields
            print(f"Ticket ID:          {ticket['id']}")
            print(f"Priority:           {ticket['priority']}")
            print(f"Status:             {ticket['status']}")
            print()

            # Title (message field serves as title)
            print(f"Title/Message:")
            print(f"  {ticket['message']}")
            print()

            # Description/Context
            print(f"Error Type:         {ticket['error_type']}")
            print(f"Source:             {ticket['source']}")
            print(f"Run Label:          {ticket.get('run_label', 'N/A')}")
            print()

            # Timestamps
            print(f"Created At:         {ticket['created_at']}")
            print(f"Updated At:         {ticket['updated_at']}")
            print()

            # Lock status
            if ticket['locked_by']:
                print(f"Lock Status:        LOCKED")
                print(f"  Locked By:        {ticket['locked_by']}")
                print(f"  Locked At:        {ticket['locked_at']}")
                print(f"  Lease Expires:    {ticket['lease_expires']}")
            else:
                print(f"Lock Status:        UNLOCKED")
            print()

            # Checklist fields
            print(f"Checklist Status:")
            print(f"  Documented:       {format_value(ticket['documented'])}")
            print(f"  Functioning:      {format_value(ticket['functioning'])}")
            print(f"  Tested:           {format_value(ticket['tested'])}")
            print(f"  Completed:        {format_value(ticket['completed'])}")
            print()

            # Stack trace
            if ticket['stack_trace']:
                print(f"Stack Trace:")
                print("  " + "\n  ".join(ticket['stack_trace'].split("\n")[:10]))
                if len(ticket['stack_trace'].split("\n")) > 10:
                    print("  ... (truncated)")
                print()

            # AI remediation notes
            if ticket['ai_remediation_notes']:
                print(f"AI Remediation Notes:")
                print(f"  {ticket['ai_remediation_notes']}")
                print()

            # File context
            if ticket['file_context']:
                print(f"File Context:")
                print(f"  {format_value(ticket['file_context'], indent=2)}")
                print()

            # System state
            if ticket['system_state']:
                print(f"System State:")
                print(f"  {format_value(ticket['system_state'], indent=2)}")
                print()

            # Other metadata
            print(f"Other Metadata:")
            print(f"  Branch:           {ticket.get('branch', 'N/A')}")
            print(f"  Owner:            {ticket.get('owner', 'Unassigned')}")
            print(f"  Correlation ID:   {ticket.get('correlation_id', 'N/A')}")
            print(f"  Duplicate Guard:  {ticket.get('duplicate_guard', 'N/A')}")
            print(f"  Format Version:   {ticket.get('format_version', '1.0')}")

            if ticket['completion_summary']:
                print(f"  Completion Summary: {ticket['completion_summary']}")

            print()

        # Summary
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        stats = repo.get_stats()
        print(f"Total Tickets:      {stats['total']}")
        print(f"Open:               {stats['open']}")
        print(f"In Progress:        {stats['in_progress']}")
        print(f"Completed:          {stats['completed']}")
        print(f"Locked:             {stats['locked']}")
        print()
        print(f"By Priority:")
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = stats['by_priority'].get(priority, 0)
            print(f"  {priority}: {count}")
        print()

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
