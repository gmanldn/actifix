#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix ticket completion checkboxes for comprehensive test tickets.

Adds "Completed" checkbox to tickets that have the other 3 checkboxes marked.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.state_paths import get_actifix_paths
from actifix.log_utils import atomic_write


def fix_ticket_completion():
    """Add Completed checkbox to all comprehensive test tickets."""
    paths = get_actifix_paths()
    
    if not paths.list_file.exists():
        print("ACTIFIX-LIST.md not found")
        return 0
    
    content = paths.list_file.read_text()
    modified = 0
    
    # Process each ticket
    import re
    
    # Pattern to match tickets with only 3 checkboxes (no Completed)
    pattern = r'(## ACT-20260110-[A-F0-9]+.*?\*\*Run\*\*: comprehensive-test-suite.*?\*\*Checklist:\*\*\n- \[x\] Documented\n- \[x\] Functioning\n- \[x\] Tested)\n(?!\- \[x\] Completed)'
    
    def add_completed(match):
        nonlocal modified
        modified += 1
        return match.group(1) + '\n- [x] Completed\n- Summary: Processed comprehensive test ticket'
    
    new_content = re.sub(pattern, add_completed, content, flags=re.DOTALL)
    
    if modified > 0:
        atomic_write(paths.list_file, new_content)
        print(f"\n✅ Fixed {modified} tickets")
    else:
        print("No tickets needed fixing")
    
    return modified


def main():
    try:
        count = fix_ticket_completion()
        print(f"\nTotal tickets fixed: {count}")
    except Exception as exc:
        print(f"Error fixing tickets: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
