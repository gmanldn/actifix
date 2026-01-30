#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_pokertool_tickets.py
============================

This helper script uses the Actifix ``raise_af.record_error`` API to
pre‑populate a series of tickets covering the work required to port
the external PokerTool project into the Actifix architecture.  Running
this script will generate multiple Actifix tickets in your local
``actifix.db`` database, one for each major porting milestone.  The
messages for each ticket include structured "Root Cause", "Impact" and
"Action" sections so that the tickets meet Actifix quality gates.

Usage:

    python3 create_pokertool_tickets.py

Ensure that ``ACTIFIX_CHANGE_ORIGIN`` is set to ``raise_af`` in your
environment before running this script, otherwise RaiseAF’s policy
enforcement will refuse to record the tickets.  If you wish to preview
the tickets without actually persisting them, pass ``--dry-run`` on
the command line.

This script is designed to be cross‑platform and has no external
dependencies beyond the Actifix code base.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List

# Make sure the src directory is on the import path. When this script resides
# in ``scripts/``, the project root is its parent directory.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_ROOT = os.path.join(ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

# Import the Actifix ticket creation API. We deliberately import
# ``record_error`` lazily to avoid resolving any optional dependencies
# until it is actually needed.
try:
    from actifix.raise_af import TicketPriority, record_error  # type: ignore
except Exception as exc:
    raise ImportError(
        "Could not import actifix.raise_af. Ensure this script is run from the "
        "Actifix repository root."  # noqa: E501
    ) from exc


@dataclass
class TicketTask:
    """Define a porting task to be translated into an Actifix ticket."""

    message: str
    priority: TicketPriority = TicketPriority.P2
    run_label: str = "pokertool_porting"
    source: str = "pokertool_porting_script"


def build_tasks() -> List[TicketTask]:
    """
    Assemble the list of porting tasks.  Each task includes a fully
    structured message which will be passed to ``record_error``.  The
    tasks are ordered logically from scaffolding the module through
    incremental subsystem migrations.

    Returns:
        A list of TicketTask objects ready for ticket creation.
    """

    tasks: List[TicketTask] = []

    # 1. Scaffolding the Actifix module
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: The PokerTool codebase does not currently exist "
                "as an Actifix module. Without a properly defined module, the "
                "Actifix runtime cannot register its routes or initialise the "
                "analysis engine.\n\n"
                "Impact: Failing to create a module skeleton will block all "
                "subsequent porting work – there will be nowhere to place the "
                "ported functions, and the new service will not be reachable at "
                "http://localhost:8060.\n\n"
                "Action: Create a new package ``actifix/modules/pokertool``. "
                "Implement an ``__init__.py`` that defines ``MODULE_DEFAULTS``, "
                "``MODULE_METADATA`` and ``MODULE_DEPENDENCIES`` following the pattern "
                "documented in the existing modules.  Write a ``create_blueprint`` "
                "function that returns a Flask blueprint with at least a ``/health`` "
                "endpoint and stub API routes.  Set the metadata name to "
                "\"pokertool\" and summarise its purpose using phrases like "
                "real‑time analysis, modern web interface and detection system from "
                "the original project【330924805208830†L0-L12】.  Configure the module to run on "
                "port 8060 by updating the Actifix configuration or providing "
                "instructions in the module README."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 2. Port the core analysis engine
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: PokerTool’s core analysis engine – functions such "
                "as ``analyse_hand`` and card utilities in ``src/pokertool/core`` – are not "
                "available inside the Actifix ecosystem.  The core computes hand "
                "strength, generates coaching prompts and orchestrates calls into "
                "GTO and machine‑learning submodules.\n\n"
                "Impact: Without porting the core analysis logic, the new module will "
                "return empty or placeholder responses.  Users will not receive any "
                "hand recommendations, undermining the value of the integration.\n\n"
                "Action: Copy the core analysis package from the PokerTool repository into "
                "``actifix/modules/pokertool/core.py`` or a subpackage.  Refactor it to remove "
                "any global state and to accept inputs via function arguments or JSON payloads. "
                "Expose a REST endpoint, e.g. ``/analyse-hand``, in the module blueprint that "
                "accepts hand histories and returns analysis results.  Ensure the API is "
                "stateless, returns JSON and is thread‑safe."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 3. Integrate the advanced detection system
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: PokerTool includes a sophisticated detection system with 99.2 % "
                "accuracy and 40–80 ms latency, responsible for reading table states from "
                "the player’s screen【330924805208830†L1-L10】.  This subsystem is absent from Actifix.\n\n"
                "Impact: Without the detection engine, the module cannot capture board state or "
                "player actions in real time.  Live analysis and coaching prompts would be "
                "impossible, negating one of the major features advertised in the original "
                "project【330924805208830†L1-L12】.\n\n"
                "Action: Identify and port the detection components (likely under ``src/pokertool/``) "
                "into a dedicated subpackage, e.g. ``actifix/modules/pokertool/detector``.  Wrap "
                "dependencies such as OpenCV, Tesseract or PyTorch in Actifix-friendly abstractions. "
                "Implement an API endpoint that starts the detection process and streams game "
                "state updates to the front‑end via WebSockets or Server‑Sent Events.  Provide a "
                "shutdown mechanism and ensure the code runs cross‑platform."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 4. Port GTO solvers and machine‑learning models
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: The original PokerTool repository integrates GTO solvers (Nash "
                "equilibrium search and ICM calculations) and machine‑learning components for "
                "opponent modelling and active learning【330924805208830†L1-L10】.  These are not present in "
                "the Actifix codebase.\n\n"
                "Impact: Omitting these algorithms would reduce the analysis engine to basic "
                "heuristics.  Users expect sophisticated advice informed by game theory and ML, so "
                "failing to port them would significantly degrade functionality.\n\n"
                "Action: Extract the solver and machine‑learning modules from the PokerTool source.  "
                "Integrate them into the new module under ``actifix/modules/pokertool/solvers`` and "
                "``actifix/modules/pokertool/ml``.  Provide clear interfaces for computing Nash equilibrium "
                "solutions, ICM payouts and opponent models.  Add asynchronous wrappers to prevent "
                "long‑running computations from blocking the web server.  Document any external "
                "dependencies and ensure they are installed via the Actifix build process."
            ),
            priority=TicketPriority.P3,
        )
    )

    # 5. Implement monitoring and health integration
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: Robust monitoring and health checks are mandatory within the Actifix "
                "framework.  PokerTool already includes a backend status dashboard, health endpoints, "
                "centralised logging and a trouble feed system【330924805208830†L14-L21】.  Those features need to be "
                "exposed through the new module.\n\n"
                "Impact: Without monitoring hooks, we cannot assess the health of the analysis engine, "
                "detection pipeline or GTO solvers.  Errors would go unnoticed, and the system could "
                "fail silently.\n\n"
                "Action: Add a ``/health`` endpoint to the module blueprint that checks the status of each "
                "subsystem (analysis core, detection, solvers, database).  Integrate with Actifix’s "
                "logging so that exceptions automatically generate tickets.  Provide optional endpoints "
                "for metrics such as latency and accuracy.  Update the Actifix monitoring configuration "
                "to include the new module’s health URL."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 6. Migrate database integration
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: PokerTool supports multiple database backends – ``PokerDatabase`` (SQLite), "
                "``SecureDatabase`` (encrypted) and ``ProductionDatabase`` (PostgreSQL)【330924805208830†L23-L26】.  These database "
                "interfaces must be unified with Actifix’s configuration system.\n\n"
                "Impact: Without a compatible database layer, persistent state such as game history, "
                "model parameters and configuration settings cannot be saved or retrieved.  This would "
                "prevent training, leak detection and regression prevention features from working.\n\n"
                "Action: Port the database classes into the module and adapt them to use Actifix’s data "
                "directory structure (``data/actifix.db`` by default).  Provide configuration options to "
                "select the backend (SQLite for development, PostgreSQL for production).  Implement "
                "migration scripts or ORM models as needed.  Update the module’s health check to verify "
                "connectivity and migrations."
            ),
            priority=TicketPriority.P3,
        )
    )

    # 7. Adapt API endpoints and configure port
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: The original PokerTool backend exposes its API on port 5001 with custom "
                "routes.  Under Actifix, each module is mounted on a unified host and must register its "
                "endpoints via a blueprint.  The required port for this module is 8060.\n\n"
                "Impact: Without adapting the API routes and port, the front‑end will point at the wrong "
                "address, causing connection failures.  Developers might also accidentally run multiple "
                "servers on conflicting ports.\n\n"
                "Action: Within the module’s ``create_blueprint`` function, prefix all routes with ``/pokertool`` "
                "and ensure that Actifix’s application factory binds the service to port 8060.  Update any "
                "client configuration (e.g. React environment variables) to use ``http://localhost:8060``.  "
                "Provide a section in the module README explaining how to override the port via environment "
                "variables."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 8. Transfer and adapt tests
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: PokerTool ships with more than 2,550 automated tests and enforces 95 %+ "
                "coverage across all subsystems【330924805208830†L0-L12】.  These tests are crucial for preventing "
                "regressions during the port.  Actifix’s own quality gates also require high coverage and "
                "passing test suites.\n\n"
                "Impact: If we do not bring across a representative subset of the original tests – or write "
                "equivalent tests – we risk silently breaking core functionality.  Failing quality gates will "
                "block ticket closure.\n\n"
                "Action: Identify key test cases from the PokerTool repository that cover the core analysis, "
                "detection, solvers and database integration.  Translate them into pytest files under ``tests/`` "
                "within the Actifix repo, using module import paths such as ``actifix.modules.pokertool``.  Mark "
                "long‑running or integration tests appropriately.  Ensure total coverage remains above 95 % and "
                "all ported tests pass before closing the migration tickets."
            ),
            priority=TicketPriority.P3,
        )
    )

    # 9. Document and update architecture
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: Actifix uses a central ``MAP.yaml`` and associated documentation to model the module "
                "topology and dependencies.  Adding a new module without updating these artefacts would break "
                "architecture validation and leave the integration undocumented.\n\n"
                "Impact: Outdated architecture metadata makes it hard for developers to understand how the "
                "pokertool module fits into the system.  Tools that generate dependency graphs could fail, and "
                "new contributors might misconfigure the module.\n\n"
                "Action: Write comprehensive documentation for the new module, including a design overview, "
                "endpoints, dependency list and configuration options.  Add a node for "
                "``pokertool`` in ``docs/architecture/MAP.yaml`` with edges to its dependencies.  Create an ADR "
                "explaining the decision to port PokerTool into Actifix and summarise key trade‑offs.  Update "
                "the ``MODULES.md`` summary to include the new module."
            ),
            priority=TicketPriority.P2,
        )
    )

    # 10. Port and integrate the front‑end dashboard
    tasks.append(
        TicketTask(
            message=(
                "Root Cause: PokerTool includes a modern React dashboard that communicates with the backend via "
                "REST and WebSocket APIs【330924805208830†L1-L10】.  The Actifix platform currently exposes only the "
                "Dev Assistant front‑end, so users would have no interface to the pokertool module without "
                "porting the UI.\n\n"
                "Impact: Without a front‑end, users cannot view analysis results, interact with the solver or "
                "configure settings.  This would render the port largely unusable for non‑technical users.\n\n"
                "Action: Incorporate the PokerTool React application into the ``actifix-frontend`` project or "
                "serve it as a separate static bundle.  Update API calls to point at the new ``/pokertool`` "
                "endpoints on port 8060.  Ensure that WebSocket connections are upgraded properly through the "
                "Actifix proxy layer.  Provide guidance for building and serving the UI in development and "
                "production."
            ),
            priority=TicketPriority.P3,
        )
    )

    return tasks


def create_tickets(tasks: List[TicketTask], dry_run: bool = False) -> None:
    """
    Iterate over the provided tasks, creating an Actifix ticket for each.  If
    ``dry_run`` is True, the tickets will not be recorded, and the script will
    simply print their messages.  Otherwise, ``record_error`` is invoked.

    Args:
        tasks: A list of TicketTask objects to process.
        dry_run: Whether to skip creating tickets in the database.
    """
    for idx, task in enumerate(tasks, 1):
        if dry_run:
            print(f"[DRY‑RUN] Would create ticket #{idx}:\n{task.message}\n")
            continue
        try:
            entry = record_error(
                message=task.message,
                source=task.source,
                run_label=task.run_label,
                priority=task.priority,
            )
            if entry:
                ticket_id = entry.entry_id
            else:
                ticket_id = "duplicate-skipped"
            print(f"Created ticket {idx}: {ticket_id}")
        except Exception as exc:
            print(f"ERROR: Failed to create ticket {idx}: {exc}", file=sys.stderr)
            try:
                record_error(
                    message=f"Failed to create PokerTool ticket {idx}: {exc}",
                    source="scripts/create_pokertool_tickets.py",
                    run_label=task.run_label,
                    priority=TicketPriority.P1,
                )
            except Exception as inner_exc:
                print(f"ERROR: Failed to record error ticket: {inner_exc}", file=sys.stderr)
            raise


def main() -> None:
    """
    Command‑line entry point.  Parses a ``--dry-run`` flag and then builds
    and processes the tasks.  If the ``ACTIFIX_CHANGE_ORIGIN`` environment
    variable is not already set to ``raise_af``, the script will set it on
    behalf of the user to satisfy policy enforcement.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Create Actifix tickets for porting PokerTool.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print tickets without writing to the database.",
    )
    args = parser.parse_args()

    # Set the origin for RaiseAF if not already provided.  This environment
    # variable is required for the raise_af policy enforcement logic.
    os.environ.setdefault("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    tasks = build_tasks()
    create_tickets(tasks, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
