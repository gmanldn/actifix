#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process the 100 comprehensive test tickets created for system validation.

Filters tickets by run label "comprehensive-test-suite" and marks them complete
using Actifix DoAF utilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import actifix
from actifix.do_af import get_open_tickets, mark_ticket_complete
from actifix.state_paths import get_actifix_paths


def process_comprehensive_tickets(summary: str = "Processed comprehensive test ticket") -> int:
    paths = get_actifix_paths()
    tickets = get_open_tickets(paths)
    target = [t for t in tickets if t.run_name == "comprehensive-test-suite"]
    processed = 0

    for ticket in target:
        if mark_ticket_complete(ticket.ticket_id, summary=summary, paths=paths):
            processed += 1
            print(f"Completed {ticket.ticket_id}: {ticket.message}")
        else:
            print(f"Skipped (not found) {ticket.ticket_id}: {ticket.message}")

    print(f"\nTotal processed: {processed}")
    return processed


def main():
    try:
        count = process_comprehensive_tickets()
        if count == 0:
            print("No comprehensive-test-suite tickets found to process.")
    except Exception as exc:
        print(f"Error processing tickets: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
