#!/usr/bin/env python3
"""
Ingest external error logs into Actifix tickets.
Usage:
  cat error.log | python3 scripts/ingest_error_logs.py
  or
  python3 scripts/ingest_error_logs.py /path/to/error.log
"""

import argparse
import sys
from pathlib import Path

import actifix
from actifix.bootstrap import ActifixContext
from actifix.raise_af import record_error, TicketPriority

def main():
    parser = argparse.ArgumentParser(description='Ingest error logs into Actifix tickets.')
    parser.add_argument('file', nargs='?', help='Path to log file (or use stdin).')
    parser.add_argument('--priority', default='P2', choices=['P0', 'P1', 'P2', 'P3', 'P4'], help='Ticket priority (default: P2)')
    args = parser.parse_args()

    with ActifixContext():
        if args.file:
            log_path = Path(args.file)
            if not log_path.exists():
                print(f'Error: File {args.file} not found.', file=sys.stderr)
                sys.exit(1)
            with log_path.open() as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        record_error(
                            message=line,
                            source=f'ingest_error_logs.py:{args.file}:{line_num}',
                            priority=getattr(TicketPriority, args.priority),
                            error_type='ExternalLog'
                        )
        else:
            for line_num, line in enumerate(sys.stdin, 1):
                line = line.strip()
                if line:
                    record_error(
                        message=line,
                        source=f'ingest_error_logs.py:stdin:{line_num}',
                        priority=getattr(TicketPriority, args.priority),
                        error_type='ExternalLog'
                    )
        print('Ingestion complete. Check Actifix tickets for new entries.')

if __name__ == '__main__':
    main()