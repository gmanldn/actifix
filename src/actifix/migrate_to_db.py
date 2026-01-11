#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migrate Actifix tickets from ACTIFIX-LIST.md to SQLite database.

Usage:
    python -m actifix.migrate_to_db

This script reads existing tickets from ACTIFIX-LIST.md and imports them
into the new database structure while preserving all data.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .raise_af import ActifixEntry, TicketPriority
from .persistence.ticket_repo import get_ticket_repository
from .state_paths import get_actifix_paths


def parse_markdown_ticket(block: str) -> Optional[ActifixEntry]:
    """Parse a ticket from markdown format."""
    # Extract ticket ID
    id_match = re.search(r'### (ACT-\d{8}-[A-F0-9]+)', block)
    if not id_match:
        return None
    
    ticket_id = id_match.group(1)
    
    # Extract fields
    priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', block)
    priority_str = priority_match.group(1) if priority_match else 'P2'
    
    error_type_match = re.search(r'\*\*Error Type\*\*:\s*(.+)', block)
    error_type = error_type_match.group(1).strip() if error_type_match else 'unknown'
    
    source_match = re.search(r'\*\*Source\*\*:\s*`([^`]+)`', block)
    source = source_match.group(1) if source_match else 'unknown'
    
    run_match = re.search(r'\*\*Run\*\*:\s*(.+)', block)
    run_label = run_match.group(1).strip() if run_match else 'unknown'
    
    created_match = re.search(r'\*\*Created\*\*:\s*([^\n]+)', block)
    created_str = created_match.group(1).strip() if created_match else datetime.now(timezone.utc).isoformat()
    
    try:
        created_at = datetime.fromisoformat(created_str)
    except Exception:
        created_at = datetime.now(timezone.utc)
    
    guard_match = re.search(r'\*\*Duplicate Guard\*\*:\s*`([^`]+)`', block)
    duplicate_guard = guard_match.group(1) if guard_match else f"{ticket_id}-guard"
    
    # Extract message from header
    header_line = block.split('\n')[0]
    msg_match = re.search(r'\[P\d\]\s*\w+.*?:\s*(.+)', header_line)
    message = msg_match.group(1) if msg_match else 'No message'
    
    # Extract stack trace
    stack_match = re.search(r'```\n(.*?)\n```', block, re.DOTALL)
    stack_trace = stack_match.group(1) if stack_match else ''
    
    try:
        priority = TicketPriority(priority_str)
    except Exception:
        priority = TicketPriority.P2
    
    return ActifixEntry(
        message=message,
        source=source,
        run_label=run_label,
        entry_id=ticket_id,
        created_at=created_at,
        priority=priority,
        error_type=error_type,
        stack_trace=stack_trace,
        duplicate_guard=duplicate_guard,
    )


def migrate_tickets() -> dict:
    """Migrate tickets from ACTIFIX-LIST.md to database."""
    paths = get_actifix_paths()
    list_file = paths.base_dir / 'ACTIFIX-LIST.md'
    
    if not list_file.exists():
        return {
            'success': False,
            'error': 'ACTIFIX-LIST.md not found',
            'migrated': 0,
            'skipped': 0,
        }
    
    content = list_file.read_text(encoding='utf-8')
    
    # Find all ticket blocks
    blocks = re.split(r'(?=### ACT-)', content)
    
    repo = get_ticket_repository()
    migrated = 0
    skipped = 0
    errors = []
    
    for block in blocks:
        if not block.strip() or 'ACT-' not in block:
            continue
        
        try:
            entry = parse_markdown_ticket(block)
            if entry:
                # Try to create ticket
                created = repo.create_ticket(entry)
                if created:
                    migrated += 1
                    print(f"✓ Migrated {entry.entry_id}")
                else:
                    skipped += 1
                    print(f"⊘ Skipped {entry.entry_id} (duplicate)")
        except Exception as e:
            errors.append(str(e))
            print(f"✗ Error migrating ticket: {e}")
    
    return {
        'success': True,
        'migrated': migrated,
        'skipped': skipped,
        'errors': errors,
    }


def main():
    """CLI entry point."""
    print("Actifix Database Migration")
    print("=" * 50)
    print()
    print("Migrating tickets from ACTIFIX-LIST.md to database...")
    print()
    
    result = migrate_tickets()
    
    print()
    print("=" * 50)
    if result['success']:
        print(f"Migration complete!")
        print(f"  Migrated: {result['migrated']}")
        print(f"  Skipped:  {result['skipped']}")
        if result['errors']:
            print(f"  Errors:   {len(result['errors'])}")
    else:
        print(f"Migration failed: {result.get('error', 'Unknown error')}")
    print()


if __name__ == '__main__':
    main()
