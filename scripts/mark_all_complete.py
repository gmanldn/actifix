#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mark all comprehensive test tickets as complete using Actifix do_af functions.
"""

import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.state_paths import get_actifix_paths
from actifix.do_af import mark_ticket_complete


def mark_all_comprehensive_complete():
    """Mark all comprehensive test suite tickets as complete."""
    paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        print("ACTIFIX-LIST.md not found")
        return 0
    
    content = paths.list_file.read_text()
    
    # Find all ACT-20260110 ticket IDs
    ticket_ids = re.findall(r'## (ACT-20260110-[A-F0-9]+)', content)
    
    print(f"Found {len(ticket_ids)} tickets from 2026-01-10")
    
    marked = 0
    for ticket_id in ticket_ids:
        if mark_ticket_complete(ticket_id, "Processed comprehensive test ticket", paths):
            marked += 1
            if marked <= 10 or marked % 10 == 0:
                print(f"  Marked {ticket_id} as complete ({marked}/{len(ticket_ids)})")
    
    print(f"\n✅ Marked {marked} tickets as complete")
    return marked


def main():
    try:
        count = mark_all_comprehensive_complete()
        print(f"\nTotal tickets marked complete: {count}")
    except Exception as exc:
        print(f"Error marking tickets: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
