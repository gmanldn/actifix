#!/usr/bin/env python3
"""Generate regression test stubs from Actifix tickets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict

from actifix.log_utils import atomic_write
from actifix.raise_af import record_error, TicketPriority
from actifix.persistence.ticket_repo import get_ticket_repository

ROOT = Path(__file__).resolve().parents[1]


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    return cleaned.lower() or "ticket"


def build_regression_test_content(ticket: Dict[str, str]) -> str:
    ticket_id = ticket.get("id", "unknown")
    message = ticket.get("message", "Unknown ticket")
    source = ticket.get("source", "unknown")
    slug = _slugify(ticket_id)

    return (
        "#!/usr/bin/env python3\n"
        "\"\"\"Regression test stub generated from Actifix ticket.\"\"\"\n\n"
        "import pytest\n\n\n"
        f"def test_regression_{slug}():\n"
        f"    \"\"\"Ticket {ticket_id}: {message} (source: {source})\"\"\"\n"
        "    pytest.skip(\"TODO: implement regression steps for this ticket\")\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate regression test stubs from Actifix tickets.")
    parser.add_argument("ticket_id", help="Ticket ID to generate a regression test for.")
    parser.add_argument(
        "--output",
        help="Optional output path for the test file.",
    )
    args = parser.parse_args()

    try:
        repo = get_ticket_repository()
        ticket = repo.get_ticket(args.ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {args.ticket_id} not found")

        output_path = Path(args.output) if args.output else (
            ROOT / "test" / "generated" / f"test_regression_{_slugify(args.ticket_id)}.py"
        )
        content = build_regression_test_content(ticket)
        atomic_write(output_path, content)
        print(f"Generated regression test stub: {output_path}")
        return 0
    except Exception as exc:
        record_error(
            message=f"Failed to generate regression test: {exc}",
            source="scripts/regression_test_generator.py:main",
            run_label="regression-test-generator",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
