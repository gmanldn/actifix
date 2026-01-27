#!/usr/bin/env python3
"""
Ingest external error logs into Actifix tickets.

Usage:
  cat error.log | python3 scripts/ingest_error_logs.py
  python3 scripts/ingest_error_logs.py /path/to/error.log
  python3 scripts/ingest_error_logs.py /path/to/error.jsonl --format jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from actifix import enable_actifix_capture
from actifix.bootstrap import ActifixContext
from actifix.raise_af import record_error, TicketPriority


def _iter_lines(file_path: Optional[Path]) -> Iterable[tuple[int, str]]:
    if file_path is None:
        for line_num, line in enumerate(sys.stdin, 1):
            yield line_num, line
        return

    with file_path.open() as handle:
        for line_num, line in enumerate(handle, 1):
            yield line_num, line


def _resolve_priority(priority: Optional[str]) -> TicketPriority:
    if not priority:
        return TicketPriority.P2
    try:
        return getattr(TicketPriority, priority)
    except AttributeError:
        return TicketPriority.P2


def _build_default_source(
    source_prefix: str,
    file_path: Optional[Path],
    line_num: int,
) -> str:
    if file_path is None:
        return f"{source_prefix}:stdin:{line_num}"
    return f"{source_prefix}:{file_path}:{line_num}"


def _parse_json_line(payload: str) -> Optional[dict]:
    payload = payload.strip()
    if not payload:
        return None
    if not payload.lstrip().startswith("{"):
        return None
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _ingest_entry(
    payload: dict,
    default_priority: TicketPriority,
    default_error_type: str,
    default_run_label: str,
    default_source: str,
    capture_context: bool,
) -> None:
    message = str(payload.get("message") or payload.get("error") or "").strip()
    if not message:
        return
    priority_value = payload.get("priority")
    priority = _resolve_priority(priority_value) if priority_value else default_priority
    record_error(
        message=message,
        source=str(payload.get("source") or default_source),
        run_label=str(payload.get("run_label") or default_run_label),
        priority=priority,
        error_type=str(payload.get("error_type") or default_error_type),
        stack_trace=payload.get("stack_trace"),
        capture_context=capture_context,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Ingest error logs into Actifix tickets.')
    parser.add_argument('file', nargs='?', help='Path to log file (or use stdin).')
    parser.add_argument('--priority', default='P2', choices=['P0', 'P1', 'P2', 'P3', 'P4'], help='Ticket priority (default: P2)')
    parser.add_argument('--format', default='auto', choices=['auto', 'plain', 'jsonl'], help='Input format (default: auto)')
    parser.add_argument('--run-label', default='external-log-ingest', help='Run label for imported tickets.')
    parser.add_argument('--error-type', default='ExternalLog', help='Error type for imported tickets.')
    parser.add_argument('--source-prefix', default='ingest_error_logs.py', help='Source prefix for generated tickets.')
    parser.add_argument('--no-context', action='store_true', help='Skip file/system context capture.')
    parser.add_argument('--max-lines', type=int, default=0, help='Limit the number of lines ingested.')
    args = parser.parse_args(argv)

    with ActifixContext():
        enable_actifix_capture()
        if args.file:
            log_path = Path(args.file)
            if not log_path.exists():
                print(f'Error: File {args.file} not found.', file=sys.stderr)
                return 1
        else:
            log_path = None

        capture_context = not args.no_context
        default_priority = _resolve_priority(args.priority)
        max_lines = args.max_lines if args.max_lines and args.max_lines > 0 else None

        processed = 0
        for line_num, line in _iter_lines(log_path):
            if max_lines is not None and processed >= max_lines:
                break
            stripped = line.strip()
            if not stripped:
                continue
            processed += 1
            source = _build_default_source(args.source_prefix, log_path, line_num)
            if args.format in ("auto", "jsonl"):
                payload = _parse_json_line(stripped)
                if payload is not None:
                    _ingest_entry(
                        payload,
                        default_priority,
                        args.error_type,
                        args.run_label,
                        source,
                        capture_context,
                    )
                    continue
                if args.format == "jsonl":
                    record_error(
                        message=f"Failed to parse JSON line {line_num} in {log_path or 'stdin'}",
                        source=source,
                        priority=TicketPriority.P3,
                        error_type="ExternalLogParseError",
                        capture_context=False,
                    )
                    continue
            record_error(
                message=stripped,
                source=source,
                priority=default_priority,
                error_type=args.error_type,
                run_label=args.run_label,
                capture_context=capture_context,
            )
        print('Ingestion complete. Check Actifix tickets for new entries.')
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
