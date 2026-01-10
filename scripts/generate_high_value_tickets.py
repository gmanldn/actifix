#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate high-value Actifix tickets through RaiseAF for testing or demos.

Actifix classifies tickets by severity. This helper script repeatedly calls
`actifix.record_error()` with critical/high priority contexts so that test users
can inspect ACTIFIX-LIST.md or feed the tickets into DoAF pipelines.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

# Ensure src/ is importable
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "src"))

import actifix
from actifix import TicketPriority


HIGH_VALUE_ISSUES = [
    {
        "message": "P0: Primary datastore unreachable (connection refused).",
        "source": "storage.connector:connect",
        "error_type": "DatastoreUnavailable",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P0: Distributed lock manager failed to acquire quorum.",
        "source": "coordination.lock_manager:acquire",
        "error_type": "LockAcquisitionError",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P1: Authentication service returned 500 on login call.",
        "source": "auth.api:login",
        "error_type": "AuthenticationFailure",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P1: Core feature flagging service is timing out.",
        "source": "feature_flags.poller:timeout",
        "error_type": "TimeoutError",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P1: High-frequency trade engine reported invalid state.",
        "source": "trading.engine:validate_state",
        "error_type": "StateValidationError",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P1: Payment processor rejected settlement batch.",
        "source": "payments.settlement:submit",
        "error_type": "SettlementError",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P0: Telemetry ingestion pipeline dropped telemetry packets.",
        "source": "telemetry.ingest:ingest_batch",
        "error_type": "TelemetryGap",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P1: Secrets rotation job misconfigured provider credentials.",
        "source": "secrets.rotation:rotate",
        "error_type": "ConfigurationError",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P0: Health check thread found inconsistent correlation state.",
        "source": "health.monitor:validate_correlation",
        "error_type": "CorrelationMismatch",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P1: Quarantine system marked storage as corrupt.",
        "source": "quarantine.manager:isolate",
        "error_type": "CorruptionDetected",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P1: Notification service failed to acknowledge critical alert.",
        "source": "notifications.worker:emit",
        "error_type": "NotificationFailure",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P0: GC pause exceeded 60s in production worker.",
        "source": "runtime.gc:collect",
        "error_type": "LongGCPause",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P1: Storage quota exceeded for audit logs.",
        "source": "logging.quota:enforce",
        "error_type": "QuotaExceeded",
        "priority": TicketPriority.P1,
    },
    {
        "message": "P0: Leader election lost majority in cluster.",
        "source": "election.coordinator:evaluate_majority",
        "error_type": "LeaderLoss",
        "priority": TicketPriority.P0,
    },
    {
        "message": "P1: Client credentials rejected due to signature mismatch.",
        "source": "auth.tokens:validate_signature",
        "error_type": "SignatureMismatch",
        "priority": TicketPriority.P1,
    },
]


def _enable_capture() -> None:
    """Ensure capture is enabled for the script lifetime."""
    os.environ[actifix.ACTIFIX_CAPTURE_ENV_VAR] = "1"


def generate_tickets(
    max_tickets: int,
    run_label: str,
    base_dir: Path | None,
    priority_override: TicketPriority | None,
) -> Sequence[actifix.ActifixEntry]:
    """Record tickets via RaiseAF."""

    payloads = HIGH_VALUE_ISSUES[:max_tickets]
    entries: list[actifix.ActifixEntry] = []

    for issue in payloads:
        priority = priority_override or issue["priority"]
        entry = actifix.record_error(
            message=issue["message"],
            source=issue["source"],
            run_label=run_label,
            priority=priority,
            error_type=issue["error_type"],
            base_dir=base_dir,
        )

        if entry:
            entries.append(entry)
            print(f"Recorded ticket {entry.entry_id} ({priority.value}) - {issue['message']}")
        else:
            print(f"Skipped duplicate ticket for {issue['message']}")

    return entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate many high-priority Actifix tickets via RaiseAF."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=len(HIGH_VALUE_ISSUES),
        help="Maximum number of tickets to record (default uses the full list).",
    )
    parser.add_argument(
        "--run-label",
        default="high-value-run",
        help="Run label attached to each ticket.",
    )
    parser.add_argument(
        "--priority",
        choices=[p.value for p in TicketPriority],
        help="Force all tickets to a single priority level.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Actifix directory to append tickets to (defaults to ./actifix).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    _enable_capture()

    priority_override = (
        TicketPriority(args.priority) if args.priority else None
    )

    count = max(1, min(args.count, len(HIGH_VALUE_ISSUES)))

    print(f"Recording {count} high-value ticket(s) (priority override: {priority_override}).")
    generate_tickets(
        max_tickets=count,
        run_label=args.run_label,
        base_dir=args.base_dir,
        priority_override=priority_override,
    )


if __name__ == "__main__":
    main()
