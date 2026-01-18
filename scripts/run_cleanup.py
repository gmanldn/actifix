#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manual Cleanup Script

Run ticket cleanup manually with custom settings.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from actifix.persistence.ticket_cleanup import run_automatic_cleanup, print_cleanup_report
from actifix.persistence.cleanup_config import CleanupConfig


def main():
    parser = argparse.ArgumentParser(
        description='Run ticket cleanup with retention policies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Dry run (preview what would be cleaned)
  python run_cleanup.py

  # Execute cleanup
  python run_cleanup.py --execute

  # Custom retention periods
  python run_cleanup.py --execute --retention-days 30 --test-retention-days 3

  # Don't auto-complete test tickets, delete them instead
  python run_cleanup.py --execute --no-auto-complete

  # Keep all completed tickets, only clean test tickets
  python run_cleanup.py --execute --retention-days 999999 --test-retention-days 1
        '''
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually execute cleanup (default is dry-run mode)'
    )

    parser.add_argument(
        '--retention-days',
        type=int,
        default=90,
        help='Days to keep regular completed tickets (default: 90)'
    )

    parser.add_argument(
        '--test-retention-days',
        type=int,
        default=7,
        help='Days to keep test/automation tickets (default: 7)'
    )

    parser.add_argument(
        '--no-auto-complete',
        action='store_true',
        help='Delete test tickets instead of auto-completing them'
    )

    args = parser.parse_args()

    dry_run = not args.execute

    print(f"\n{'='*80}")
    print(f"TICKET CLEANUP - {'DRY RUN MODE' if dry_run else 'EXECUTION MODE'}")
    print(f"{'='*80}\n")

    print(f"Settings:")
    print(f"  Retention for completed tickets: {args.retention_days} days")
    print(f"  Retention for test tickets: {args.test_retention_days} days")
    print(f"  Auto-complete test tickets: {not args.no_auto_complete}")
    print()

    if dry_run:
        print("⚠️  This is a DRY RUN - no changes will be made")
        print("    Run with --execute to apply changes\n")
    else:
        print("⚠️  EXECUTING CLEANUP - changes will be applied!\n")

    results = run_automatic_cleanup(
        retention_days=args.retention_days,
        test_ticket_retention_days=args.test_retention_days,
        auto_complete_test_tickets=not args.no_auto_complete,
        dry_run=dry_run
    )

    print_cleanup_report(results)

    # Return exit code based on whether anything was cleaned
    total_cleaned = (
        results.get('retention_policy', {}).get('total_deleted', 0) +
        results.get('test_cleanup', {}).get('test_tickets_cleaned', 0)
    )

    if total_cleaned > 0:
        if dry_run:
            print(f"ℹ️  Would clean {total_cleaned} tickets. Run with --execute to apply.")
        else:
            print(f"✓ Cleaned {total_cleaned} tickets successfully.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
