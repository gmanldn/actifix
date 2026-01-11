"""
Simple Ticket Attack
====================

Small helper that creates a batch of 200 simple Actifix tickets so the
framework can exercise its ticket capture, duplicate guards, and AI-ready
contexting without touching production code. Each ticket is created through
``record_error`` to honor the Actifix method and keep all metadata in sync.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import List, Sequence

from actifix.bootstrap import ActifixContext
from actifix.raise_af import (
    ACTIFIX_CAPTURE_ENV_VAR,
    TicketPriority,
    record_error,
)

DEFAULT_COUNT = 200
DEFAULT_RUN_LABEL = "simple-ticket-attack"
DESCRIPTION_THEMES: Sequence[str] = (
    "Write a smoke test for {component}",
    "Document runtime invariants around {component}",
    "Add regression coverage for {component}",
    "Audit logging consistency in {component}",
    "Validate configuration keys referenced by {component}",
    "Simplify error handling inside {component}",
    "Confirm thread safety for {component}",
    "Refresh AI remediation notes about {component}",
    "Check health metrics tied to {component}",
    "Capture additional telemetry when {component} runs",
)
DESCRIPTION_COMPONENTS: Sequence[str] = (
    "bootstrap flow",
    "state path management",
    "raise_af capture logic",
    "do_af ticket dispatcher",
    "api interface",
    "log_utils helpers",
    "persistence storage stack",
    "persistence queue",
    "health check suite",
    "quarantine workflow",
    "testing harness",
    "frontend integration",
    "docs pipeline",
    "config loader",
    "startup monitor",
    "version monitor",
    "workflow guards",
    "atomic writer",
    "fallback queue",
    "ticket cache",
)


def _build_description_pool() -> List[str]:
    """Produce a deterministic list of simple ticket descriptions."""
    return [
        theme.format(component=component)
        for theme, component in product(DESCRIPTION_THEMES, DESCRIPTION_COMPONENTS)
    ]


DESCRIPTION_POOL = _build_description_pool()


@dataclass
class SimpleTicketAttackResult:
    """Result of recording a single simple ticket."""

    index: int
    message: str
    ticket_id: str | None
    created: bool


def _normalize_priority(value: TicketPriority | str | None) -> TicketPriority:
    """Return a valid priority enum (default to P3)."""
    if isinstance(value, TicketPriority):
        return value

    try:
        return TicketPriority(value)  # type: ignore[arg-type]
    except Exception:
        return TicketPriority.P3


def _build_messages(
    count: int,
    start_index: int,
    pool: Sequence[str],
) -> list[tuple[int, str]]:
    """Create `count` messages describing the simple tickets."""
    if count <= 0:
        return []

    pool_len = len(pool)
    messages = []
    for offset in range(count):
        idx = start_index + offset
        template = pool[offset % pool_len]
        messages.append((idx, f"Simple ticket #{idx}: {template}"))
    return messages


def attack_simple_tickets(
    *,
    count: int = DEFAULT_COUNT,
    priority: TicketPriority | str | None = None,
    run_label: str = DEFAULT_RUN_LABEL,
    capture_context: bool = False,
    start_index: int = 1,
    dry_run: bool = False,
) -> List[SimpleTicketAttackResult]:
    """
    Record a batch of simple tickets through `record_error`.

    Args:
        count: Number of tickets to create.
        priority: Ticket priority (defaults to ``P3``).
        run_label: Run label written into each ticket.
        capture_context: Include file/system context (disabled by default).
        start_index: Index used when numbering the tickets.
        dry_run: If true, return the planned tickets without persisting them.

    Returns:
        A list of `SimpleTicketAttackResult` objects describing each attempt.
    """
    os.environ.setdefault(ACTIFIX_CAPTURE_ENV_VAR, "1")
    resolved_priority = _normalize_priority(priority)
    source = f"{Path(__file__).name}:attack_simple_tickets"
    messages = _build_messages(count, start_index, DESCRIPTION_POOL)
    results: List[SimpleTicketAttackResult] = []

    if dry_run:
        return [
            SimpleTicketAttackResult(index=idx, message=message, ticket_id=None, created=False)
            for idx, message in messages
        ]

    with ActifixContext():
        for idx, message in messages:
            entry = record_error(
                message=message,
                source=source,
                run_label=run_label,
                error_type="SimpleTicket",
                priority=resolved_priority,
                capture_context=capture_context,
            )
            results.append(
                SimpleTicketAttackResult(
                    index=idx,
                    message=message,
                    ticket_id=getattr(entry, "ticket_id", None),
                    created=entry is not None,
                )
            )

    return results


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint to attack tickets."""
    parser = argparse.ArgumentParser(
        description="Create a batch of simple Actifix tickets via record_error."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help="Total number of simple tickets to create (default: 200).",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="Index used when numbering the generated tickets.",
    )
    parser.add_argument(
        "--priority",
        choices=[p.value for p in TicketPriority],
        default=TicketPriority.P3.value,
        help="Priority level for all tickets.",
    )
    parser.add_argument(
        "--run-label",
        default=DEFAULT_RUN_LABEL,
        help="Run label recorded in each ticket.",
    )
    parser.add_argument(
        "--capture-context",
        action="store_true",
        help="Include file/system context for each ticket.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the tickets that would be created without writing.",
    )

    args = parser.parse_args(argv)
    results = attack_simple_tickets(
        count=args.count,
        priority=args.priority,
        run_label=args.run_label,
        capture_context=args.capture_context,
        start_index=args.start_index,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(f"[Dry Run] Prepared {len(results)} simple tickets (no records created).")
        return 0

    created = [res for res in results if res.created]
    skipped = [res for res in results if not res.created]

    print(f"Created {len(created)} simple tickets (skipped {len(skipped)} duplicates).")
    if created:
        print(f"First ticket: {created[0].ticket_id}")
        print(f"Last ticket: {created[-1].ticket_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
