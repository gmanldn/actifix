#!/usr/bin/env python3
"""Provide tooling to consolidate redundant ticket buckets."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from actifix.persistence.ticket_repo import TicketFilter, get_ticket_repository
from actifix.raise_af import enforce_raise_af_only
from actifix.state_paths import get_actifix_paths

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}


def _normalize_message(message: str | None) -> str:
    text = (message or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\d+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_source(source: str | None) -> str:
    if not source:
        return ""
    normalized = source.replace("\\", "/").lower()
    normalized = re.sub(r":\d+$", "", normalized)
    return normalized.strip()


def _group_tickets(tickets: list[dict]) -> dict[tuple[str, str, str], list[dict]]:
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for ticket in tickets:
        key = (
            _normalize_message(ticket.get("message")),
            _normalize_source(ticket.get("source")),
            (ticket.get("error_type") or "unknown").lower(),
        )
        groups[key].append(ticket)

    return groups


def _select_canonical(group: list[dict]) -> dict:
    def sort_key(ticket: dict) -> tuple[int, datetime]:
        priority = ticket.get("priority") or ""
        order = PRIORITY_ORDER.get(priority, len(PRIORITY_ORDER))
        created_at = ticket.get("created_at") or datetime.max
        return (order, created_at)

    return min(group, key=sort_key)


def _summarize_group(group: list[dict]) -> str:
    canonical = _select_canonical(group)
    duplicates = [t for t in group if t["id"] != canonical["id"]]
    lines = [
        f"Canonical: {canonical['id']} | priority={canonical.get('priority')} | created_at={canonical.get('created_at')}",
        "Duplicates:",
    ]

    for ticket in duplicates:
        lines.append(f"  - {ticket['id']} | priority={ticket.get('priority')} | created_at={ticket.get('created_at')} | source={ticket.get('source')}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate duplicate ticket buckets by grouping similar messages and sources."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually soft-delete duplicate buckets (default is dry run).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of groups printed, useful for large runs.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_actifix_paths()
    enforce_raise_af_only(paths)

    repo = get_ticket_repository()
    open_tickets = repo.get_tickets(TicketFilter(status="Open"))
    in_progress = repo.get_tickets(TicketFilter(status="In Progress"))
    tickets = open_tickets + [t for t in in_progress if t["id"] not in {x["id"] for x in open_tickets}]

    groups = _group_tickets(tickets)
    duplicate_groups = [group for group in groups.values() if len(group) > 1]

    print("\n" + "=" * 72)
    print("BUCKET CONSOLIDATION REPORT")
    print("=" * 72)
    print(f"Total open/in-progress tickets scanned: {len(tickets)}")
    print(f"Duplicate buckets found: {len(duplicate_groups)}")

    for idx, group in enumerate(duplicate_groups, 1):
        if args.limit and idx > args.limit:
            break
        print(f"\nGroup {idx}/{len(duplicate_groups)}")
        print("-" * 72)
        print(_summarize_group(group))

    if not args.execute:
        print("\nDry run complete. Run with --execute to soft-delete duplicate buckets.")
        return 0

    deleted = 0
    for group in duplicate_groups:
        canonical = _select_canonical(group)
        for ticket in group:
            if ticket["id"] == canonical["id"]:
                continue
            success = repo.delete_ticket(ticket["id"], soft_delete=True)
            if success:
                deleted += 1
                print(f"Deleted duplicate ticket {ticket['id']} (kept {canonical['id']})")
            else:
                print(f"Failed to delete {ticket['id']} (may already be removed)")

    print("\n" + "=" * 72)
    print(f"Soft-deleted {deleted} duplicate tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())