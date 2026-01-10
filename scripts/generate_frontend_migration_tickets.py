#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Actifix tickets to migrate the React architecture from Pokertool,
removing all poker-specific functionality and replacing the UI with a
minimal Actifix-branded page.

Resulting frontend goal:
- Black background
- Striking gold, full-width text: "Love Actifix - Always Bitches!!!"
- Small pangolin image displayed with the text
- No poker-related code, assets, or integrations
"""

import os
import sys
from pathlib import Path

# Add src to path so actifix can be imported when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import actifix
from actifix import TicketPriority
from actifix.raise_af import ensure_scaffold
from actifix.state_paths import get_actifix_paths, init_actifix_files


TASKS = [
    {
        "message": (
            "RF001: Mirror Pokertool React/TypeScript architecture into a new "
            "Actifix frontend (same build tooling, routing, state layout), "
            "but strip all poker domain code and APIs."
        ),
        "source": "frontend/setup",
        "error_type": "FrontendArchitectureMigration",
        "priority": TicketPriority.P1,
    },
    {
        "message": (
            "RF002: Replace landing view with a single black page that renders "
            "the text 'Love Actifix - Always Bitches!!!' in striking gold, "
            "full-width across the viewport."
        ),
        "source": "frontend/theme",
        "error_type": "FrontendStyling",
        "priority": TicketPriority.P1,
    },
    {
        "message": (
            "RF003: Add a small pangolin image asset (local, optimized) and "
            "display it alongside the hero text with accessible alt text."
        ),
        "source": "frontend/assets",
        "error_type": "FrontendAsset",
        "priority": TicketPriority.P2,
    },
    {
        "message": (
            "RF004: Remove poker-specific components, hooks, API calls, and "
            "state from the imported architecture; ensure no poker strings or "
            "routes remain."
        ),
        "source": "frontend/cleanup",
        "error_type": "FrontendDe-scoping",
        "priority": TicketPriority.P1,
    },
    {
        "message": (
            "RF005: Wire up build/test scripts (npm/yarn) matching Pokertool's "
            "setup, adjusted for Actifix branding and without poker endpoints."
        ),
        "source": "frontend/tooling",
        "error_type": "FrontendTooling",
        "priority": TicketPriority.P2,
    },
    {
        "message": (
            "RF006: Add minimal frontend tests/linters to assert the black "
            "background, gold hero text content, and pangolin image render."
        ),
        "source": "frontend/testing",
        "error_type": "FrontendTesting",
        "priority": TicketPriority.P2,
    },
    {
        "message": (
            "RF007: Update documentation for Actifix frontend setup, run, and "
            "build steps; note the absence of poker features."
        ),
        "source": "frontend/docs",
        "error_type": "FrontendDocs",
        "priority": TicketPriority.P3,
    },
]


def main() -> int:
    """Raise migration tickets using the Actifix error pipeline."""
    # Enable capture explicitly
    os.environ[actifix.ACTIFIX_CAPTURE_ENV_VAR] = "1"
    
    paths = get_actifix_paths()
    init_actifix_files(paths)
    ensure_scaffold(paths.base_dir)
    
    total = len(TASKS)
    print(f"Raising {total} frontend migration tickets...")
    
    created = 0
    skipped = 0
    
    for idx, task in enumerate(TASKS, 1):
        try:
            entry = actifix.record_error(
                message=task["message"],
                source=task["source"],
                run_label="frontend-migration",
                error_type=task["error_type"],
                priority=task["priority"],
                capture_context=False,
                skip_ai_notes=True,
                paths=paths,
            )
            if entry:
                created += 1
                print(f"[{idx}/{total}] Created {entry.entry_id}: {task['message']}")
            else:
                skipped += 1
                print(f"[{idx}/{total}] Skipped duplicate: {task['message']}")
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[{idx}/{total}] ERROR raising ticket: {exc}")
    
    print(f"\nDone. Created {created}, skipped {skipped} (duplicates).")
    print("Check actifix/ACTIFIX-LIST.md for the recorded items.")
    return 0 if skipped < total else 1


if __name__ == "__main__":
    raise SystemExit(main())
