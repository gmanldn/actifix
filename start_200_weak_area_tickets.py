#!/usr/bin/env python3
"""
Create 200 tickets describing weak areas in the codebase.
Each ticket targets code quality, robustness, performance, or testing issues
found by inspecting the core modules.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
os.environ["ACTIFIX_CAPTURE_ENABLED"] = "1"

from actifix.raise_af import record_error, TicketPriority


def _build_tasks() -> list[str]:
    """Construct the 200 weak-area ticket messages."""
    quality_targets = [
        ("src/actifix/raise_af.py", "record_error"),
        ("src/actifix/raise_af.py", "capture_file_context"),
        ("src/actifix/do_af.py", "process_next_ticket"),
        ("src/actifix/persistence/ticket_repo.py", "get_and_lock_next_ticket"),
        ("src/actifix/persistence/database.py", "DatabasePool._get_connection"),
    ]
    quality_templates = [
        "Add precise type annotations for {function} inputs/outputs so static typing catches mismatched callers.",
        "Document {function} and its helper chain so maintainers understand the invariants and side effects.",
        "Replace repeated literal strings in {function} with named constants and explain their significance.",
        "Split the responsibilities inside {function} so each branch can be tested independently.",
        "Normalize newline/log formatting inside {function} to match project style and avoid noise when batching.",
        "Clarify the public interface of {function} with explicit Optional vs required parameters to avoid hidden defaults.",
        "Extract the duplicated error formatting logic in {function} into shared helpers to prevent drift.",
        "Add logging context around {function} so telemetry consistently records module, operation, and intent.",
        "Document the side effects {function} has on global state or files so future refactors do not regress behavior.",
        "Review {function} for duplicated error text and normalize it for reliable filtering via logs or tickets.",
    ]

    robustness_targets = [
        ("src/actifix/raise_af.py", "replay_fallback_queue"),
        ("src/actifix/do_af.py", "_select_and_lock_ticket"),
        ("src/actifix/persistence/ticket_repo.py", "acquire_lock"),
        ("src/actifix/persistence/database.py", "transaction"),
        ("src/actifix/health.py", "get_health"),
    ]
    robustness_templates = [
        "Guard {function} against filesystem permission failures before touching artifact files.",
        "Handle sqlite3.IntegrityError explicitly inside {function} and wrap it with a descriptive ticket when it happens.",
        "Validate environment overrides (paths, timeouts) at the top of {function} to fail fast on invalid configs.",
        "Retry with backoff inside {function} when the database reports ""busy"" or ""locked"" errors.",
        "Log and record a ticket when {function} raises unexpected exceptions rather than letting callers swallow them.",
        "Sanitize inputs for {function} to avoid injecting newline or control characters into log/event payloads.",
        "Enforce cache TTLs or invalidation before {function} reuses stale data or locked rows.",
        "Check for None repository or connection returns in {function} and raise an informative ticket so callers can recover.",
        "Capture diagnostic context before {function} exits on failure so traceability remains intact.",
        "Ensure {function} respects the Raise_AF enforcement flag even when invoked from background threads or CLIs.",
    ]

    performance_targets = [
        ("src/actifix/raise_af.py", "capture_system_state"),
        ("src/actifix/do_af.py", "StatefulTicketManager.get_open_tickets"),
        ("src/actifix/persistence/ticket_repo.py", "get_stats"),
        ("src/actifix/persistence/database.py", "_initialize_schema"),
        ("src/actifix/log_utils.py", "append_with_guard"),
    ]
    performance_templates = [
        "Cache repeated DB stats queries inside {function} rather than hitting the database on every call.",
        "Stream only the required file snippet in {function} to avoid reading entire files into memory.",
        "Batch writes when {function} logs multiple events in rapid succession to reduce I/O." ,
        "Reuse database connections across {function} invocations instead of opening new ones per usage.",
        "Avoid serializing JSON multiple times per call inside {function} by keeping the result in a temporary variable.",
        "Short-circuit {function} as early as possible when inputs have not changed to prevent wasted work.",
        "Move regex compilation or other heavy work outside loops inside {function} to prevent repeated cost.",
        "Limit the collected system state size within {function} by trimming to necessary fields before logging.",
        "Track fallback queue writes in {function} to avoid saturating disk when the database is slow.",
        "Adopt incremental file reads/writes inside {function} to avoid building huge strings in memory.",
    ]

    testing_targets = [
        ("src/actifix/raise_af.py", "record_error"),
        ("src/actifix/do_af.py", "process_tickets"),
        ("src/actifix/persistence/ticket_repo.py", "create_ticket"),
        ("src/actifix/persistence/database.py", "DatabasePool._initialize_schema"),
        ("src/actifix/health.py", "check_sla_breaches"),
    ]
    testing_templates = [
        "Add unit tests covering {function} when ACTIFIX_CAPTURE_ENABLED toggles between 0 and 1.",
        "Add concurrency tests that invoke {function} from multiple threads to expose race conditions.",
        "Add regression tests reproducing previously fixed locking issues around {function}.",
        "Add integration tests ensuring {function} updates ticket statuses and event logs atomically.",
        "Add parameterized tests verifying how {function} behaves for each ticket priority level.",
        "Mock environment and filesystem state so {function} can be exercised without writing to real files.",
        "Inject sqlite3 failures into {function} and assert the fallback queue is populated as expected.",
        "Add tests that replay fallback queue items after outages to verify {function} handles retries correctly.",
        "Assert that {function} adjusts health metrics when ticket counts change to catch silent regressions.",
        "Cover boundary conditions for {function} to ensure documented agent contracts hold under all inputs.",
    ]

    tasks: list[str] = []

    def _expand(targets, templates, prefix):
        for module_path, function_name in targets:
            for template in templates:
                tasks.append(
                    f"[{prefix}] {module_path}:{function_name} - {template.format(function=function_name, module=module_path)}"
                )

    _expand(quality_targets, quality_templates, "QUALITY")
    _expand(robustness_targets, robustness_templates, "ROBUSTNESS")
    _expand(performance_targets, performance_templates, "PERFORMANCE")
    _expand(testing_targets, testing_templates, "TESTING")

    if len(tasks) != 200:
        raise AssertionError(f"Expected 200 tasks, generated {len(tasks)}")

    return tasks


def main() -> None:
    tasks = _build_tasks()
    created = 0

    for message in tasks:
        entry = record_error(
            message=message,
            source=Path(__file__).name,
            run_label="weak-area-200",
            error_type="WeakArea",
            priority=TicketPriority.P2,
            skip_duplicate_check=True,
            skip_ai_notes=True,
            capture_context=False,
        )
        if entry:
            created += 1

    print(f"Created {created}/{len(tasks)} weak-area tickets")


if __name__ == "__main__":
    main()
