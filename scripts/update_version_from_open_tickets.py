#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update pyproject.toml version to match the current open ticket count.

Usage:
  ACTIFIX_CHANGE_ORIGIN=raise_af python3 scripts/update_version_from_open_tickets.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from actifix.log_utils import atomic_write
from actifix.persistence.ticket_repo import get_ticket_repository


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def main() -> int:
    if not PYPROJECT.exists():
        print(f"Error: {PYPROJECT} not found", file=sys.stderr)
        return 1

    repo = get_ticket_repository()
    stats = repo.get_stats()
    open_count = stats.get("open", 0)
    new_version = str(open_count)

    content = PYPROJECT.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated_lines = []
    replaced = False
    for line in lines:
        if not replaced and line.strip().startswith("version = "):
            updated_lines.append(f'version = "{new_version}"')
            replaced = True
        else:
            updated_lines.append(line)
    if not replaced:
        print("Error: version field not found in pyproject.toml", file=sys.stderr)
        return 1

    updated = "\n".join(updated_lines) + "\n"
    atomic_write(PYPROJECT, updated, encoding="utf-8")

    print(f"Updated version to {new_version} (open tickets).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
