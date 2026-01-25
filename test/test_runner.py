# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Actifix consolidated test runner.

Runs deterministic system/bootstrap checks using the Actifix testing framework
and then executes the pytest suite. Produces Pokertool-style inventory +
progress output and writes stage summaries to state_dir/test_logs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
RUNNER_SOURCE = "test/test_runner.py"
sys.path.insert(0, str(ROOT / "src"))

from actifix.testing import TestRunner
from actifix.testing.reporting import TestCycleReporter
from actifix.testing.system import build_system_tests
from actifix.state_paths import (
    get_actifix_paths,
    init_actifix_files,
    ensure_actifix_dirs,
    reset_actifix_paths,
)
from actifix.raise_af import record_error, TicketPriority

QUICK_PYTEST_FILES = [
    "test/test_actifix_basic.py",
    "test/test_architecture_validation.py",
    "test/test_config_extended.py",
    "test/test_event_repo.py",
    "test/test_frontend_build.py",
    "test/test_module_base.py",
    "test/test_module_dependency_validation.py",
    "test/test_module_metadata.py",
    "test/test_module_registry_status.py",
    "test/test_public_api_contract.py",
    "test/test_raise_af.py",
    "test/test_raise_af_policy.py",
    "test/test_ticket_repo.py",
    "test/test_version_synchronization.py",
    "test/test_pokertool_core.py",
    "test/test_pokertool_detector.py",
    "test/test_pokertool_ml.py",
    "test/test_pokertool_solvers.py",
    "test/test_yhatzee_session_sync.py",
    "test/test_agent_voice_repo.py",
    "test/test_view_agent_thoughts.py",
    "test/test_start_module_surface.py",
    "test/test_start_restart_policy.py",
]

# Coverage runs should stay representative enough to satisfy the global threshold,
# but still avoid the heaviest suites unless the user explicitly requests --full.
COVERAGE_PYTEST_FILES = QUICK_PYTEST_FILES + [
    "test/test_coverage_boost.py",
    "test/test_coverage_boost2.py",
    "test/test_coverage_boost3.py",
    "test/test_coverage_core.py",
    "test/test_coverage_raise_doaf.py",
    "test/test_extended_coverage.py",
]


def _resolve_pytest_targets(files: list[str]) -> list[str]:
    """Return existing pytest targets as string paths relative to the repo root."""
    targets: list[str] = []
    seen = set()
    for rel in files:
        rel_path = str(rel)
        if rel_path in seen:
            continue
        seen.add(rel_path)
        if (ROOT / rel_path).exists():
            targets.append(rel_path)
    return targets


def raise_tickets_for_system_failures(result, paths) -> int:
    """Raise tickets for system test failures and errors."""
    tickets_raised = 0

    # Raise tickets for failed tests
    for test_name in result.failed_tests:
        try:
            record_error(
                message=f"System test failed: {test_name}",
                source=f"{RUNNER_SOURCE}::run_system_suite",
                run_label="test-suite",
                error_type="TestFailure",
                priority=TicketPriority.P1,
                capture_context=True,
                paths=paths,
            )
            tickets_raised += 1
            print(f"  ✗ Raised ticket for failed test: {test_name}")
        except Exception as e:
            print(f"  ⚠️  Failed to raise ticket for {test_name}: {e}")

    # Raise tickets for tests with errors
    for test_name in result.error_tests:
        try:
            record_error(
                message=f"System test error: {test_name}",
                source=f"{RUNNER_SOURCE}::run_system_suite",
                run_label="test-suite",
                error_type="TestError",
                priority=TicketPriority.P0,
                capture_context=True,
                paths=paths,
            )
            tickets_raised += 1
            print(f"  ✗ Raised ticket for test error: {test_name}")
        except Exception as e:
            print(f"  ⚠️  Failed to raise ticket for {test_name}: {e}")

    return tickets_raised


def run_system_suite() -> tuple[TestCycleReporter, TestRunner, Dict[str, Any]]:
    """Run the Actifix system/dependency tests using the custom runner."""
    paths = get_actifix_paths()
    ensure_actifix_dirs(paths)
    init_actifix_files(paths)

    reporter = TestCycleReporter(paths=paths, cycle_name="actifix-system")
    runner = TestRunner("actifix-system", paths=paths)
    reporter.bind_to_runner(runner)

    for name, func, description, tags in build_system_tests(paths):
        runner.add_test(name, func, description=description, tags=tags)

    plan = runner.declare_plan()
    reporter.announce_plan(plan)
    result = runner.execute()

    reporter.record_stage(
        "system-tests",
        result.success,
        {
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "duration": result.duration_seconds,
        },
    )

    # Raise tickets for failures
    if not result.success:
        print("\nRaising tickets for system test failures...")
        tickets_raised = raise_tickets_for_system_failures(result, paths)
        print(f"  → {tickets_raised} ticket(s) raised for system test failures\n")

    summary = {
        "plan": plan,
        "result": result,
    }
    return reporter, runner, summary


def parse_pytest_junit(junit_file: Path, paths) -> Dict[str, Any]:
    """Parse JUnit XML into a summary payload for reporting."""
    import xml.etree.ElementTree as ET

    summary: Dict[str, Any] = {
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "passed": 0,
        "failed_tests": [],
        "error_tests": [],
        "skipped_tests": [],
    }

    try:
        tree = ET.parse(junit_file)
        root = tree.getroot()

        for testsuite in root.findall(".//testsuite"):
            summary["tests"] += int(testsuite.get("tests", 0))
            summary["failures"] += int(testsuite.get("failures", 0))
            summary["errors"] += int(testsuite.get("errors", 0))
            summary["skipped"] += int(testsuite.get("skipped", 0))

            for testcase in testsuite.findall("testcase"):
                classname = testcase.get("classname", "unknown")
                name = testcase.get("name", "unknown")
                test_id = f"{classname}::{name}"

                failure = testcase.find("failure")
                if failure is not None:
                    summary["failed_tests"].append({
                        "id": test_id,
                        "message": failure.get("message", "Test failed"),
                        "details": failure.text or "",
                        "source": classname,
                    })

                error = testcase.find("error")
                if error is not None:
                    summary["error_tests"].append({
                        "id": test_id,
                        "message": error.get("message", "Test error"),
                        "details": error.text or "",
                        "source": classname,
                    })

                skipped = testcase.find("skipped")
                if skipped is not None:
                    summary["skipped_tests"].append(test_id)

        summary["passed"] = (
            summary["tests"] - summary["failures"] - summary["errors"] - summary["skipped"]
        )
    except Exception as exc:
        record_error(
            message=f"Failed to parse pytest JUnit XML: {exc}",
            source=f"{RUNNER_SOURCE}::parse_pytest_junit",
            run_label="test-suite",
            error_type="PytestReportParseError",
            priority=TicketPriority.P2,
            capture_context=True,
            paths=paths,
        )
        raise

    return summary


def raise_tickets_for_pytest_failures(summary: Dict[str, Any], paths) -> int:
    """Raise tickets for pytest failures using parsed JUnit data."""
    tickets_raised = 0

    for failure in summary.get("failed_tests", []):
        try:
            record_error(
                message=f"Pytest failure: {failure['id']}\n{failure['message']}",
                source=failure.get("source", "unknown"),
                run_label="test-suite",
                error_type="PytestFailure",
                priority=TicketPriority.P1,
                stack_trace=failure.get("details", ""),
                capture_context=True,
                paths=paths,
            )
            tickets_raised += 1
            print(f"  ✗ Raised ticket for failed test: {failure['id']}")
        except Exception as e:
            print(f"  ⚠️  Failed to raise ticket for {failure['id']}: {e}")

    for error in summary.get("error_tests", []):
        try:
            record_error(
                message=f"Pytest error: {error['id']}\n{error['message']}",
                source=error.get("source", "unknown"),
                run_label="test-suite",
                error_type="PytestError",
                priority=TicketPriority.P0,
                stack_trace=error.get("details", ""),
                capture_context=True,
                paths=paths,
            )
            tickets_raised += 1
            print(f"  ✗ Raised ticket for test error: {error['id']}")
        except Exception as e:
            print(f"  ⚠️  Failed to raise ticket for {error['id']}: {e}")

    return tickets_raised


def load_performance_report(report_path: Path, paths) -> Dict[str, Any]:
    """Load pytest performance report if present."""
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        record_error(
            message=f"Failed to read pytest performance report: {exc}",
            source=f"{RUNNER_SOURCE}::load_performance_report",
            run_label="test-suite",
            error_type="PytestPerformanceReportReadError",
            priority=TicketPriority.P2,
            capture_context=True,
            paths=paths,
        )
        raise


def report_pytest_summary(summary: Dict[str, Any]) -> None:
    """Print a concise pytest summary for immediate feedback."""
    print("\nPytest summary")
    print(
        f"  Total: {summary['tests']} | Passed: {summary['passed']} | "
        f"Failed: {summary['failures']} | Errors: {summary['errors']} | "
        f"Skipped: {summary['skipped']}"
    )

    failures = summary.get("failed_tests", [])
    errors = summary.get("error_tests", [])

    if failures:
        print("  Failures:")
        for failure in failures[:10]:
            print(f"    - {failure['id']}")
        if len(failures) > 10:
            print(f"    - ... and {len(failures) - 10} more")

    if errors:
        print("  Errors:")
        for error in errors[:10]:
            print(f"    - {error['id']}")
        if len(errors) > 10:
            print(f"    - ... and {len(errors) - 10} more")


def report_perf_summary(perf_report: Dict[str, Any]) -> None:
    """Print top slow tests from the performance report."""
    slowest = perf_report.get("slowest_tests", [])
    if not slowest:
        return

    print("\nTop slow tests (from performance report)")
    for entry in slowest[:5]:
        markers = ", ".join(entry.get("markers") or []) or "no markers"
        duration_ms = entry.get("duration_ms", 0.0)
        print(f"  {duration_ms:7.1f}ms | {markers:20s} | {entry.get('name', 'unknown')}")


def run_pytest(
    coverage: bool,
    quick: bool,
    pattern: Optional[str],
    targets: Optional[list[str]] = None,
    runslow: bool = False,
    fast_coverage: bool = False,
    run_id: Optional[str] = None,
    paths=None,
) -> Dict[str, Any]:
    """Execute pytest with optional coverage and pattern filtering."""
    if paths is None:
        paths = get_actifix_paths()
    cmd: List[str] = [sys.executable, "-m", "pytest"]

    # Parallelize coverage runs when optional pytest-xdist is installed/configured
    def _collect_xdist_args() -> List[str]:
        """Return pytest-xdist args when available or configured via env."""
        if os.getenv("ACTIFIX_DISABLE_XDIST"):
            return []
        worker_override = os.getenv("ACTIFIX_XDIST_WORKERS")
        if worker_override:
            return ["-n", worker_override]
        if importlib.util.find_spec("xdist") is None:
            return []
        return ["-n", "auto"]

    # Add JUnit XML output for failure tracking
    junit_file = ROOT / ".pytest_results.xml"
    cmd += ["--junit-xml", str(junit_file)]
    xdist_args = _collect_xdist_args()

    if coverage:
        try:
            import pytest_cov  # noqa: F401
            cmd += ["--cov=src/actifix", "--cov-report=term-missing"]
        except ImportError:
            print("pytest-cov plugin not found; skipping coverage reporting")

        # Fast coverage mode: exclude slow tests and use parallel execution.
        # Keep integration tests because several "coverage boost" suites rely on them.
        if fast_coverage:
            print("  → Fast mode: excluding slow/db/concurrent/perf tests (use --full for all)")
            cmd += [
                "-m",
                "not slow and not very_slow and not performance and not db and not concurrent",
            ]
            cmd.extend(xdist_args)
        else:
            # Full coverage: run all tests, but still use parallel if available
            print("  → Full mode: running all tests including slow/integration")
            cmd.extend(xdist_args)
    else:
        # Non-coverage runs can also use fast mode
        if fast_coverage:
            print("  → Fast mode: excluding slow, heavy integration, and perf tests (use --full for all)")
            cmd += [
                "-m",
                "not slow and not very_slow and not performance and not db and not integration and not concurrent",
            ]
            cmd.extend(xdist_args)
        else:
            print("  → Full mode: running all tests including slow/integration")
            cmd.extend(xdist_args)

    if not targets:
        targets = ["test"]

    if quick:
        # Quick mode runs a curated, high-signal subset.
        cmd += ["-q", *targets]
    else:
        cmd.extend(targets)

    if pattern:
        cmd += ["-k", pattern]

    if runslow:
        cmd.append("--runslow")

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT / "src"))
    if run_id:
        env["ACTIFIX_TEST_RUN_ID"] = run_id

    print("\nRunning pytest suite...")
    process = subprocess.run(cmd, cwd=ROOT, env=env)

    junit_summary = None
    perf_report = None
    perf_report_path = None

    if junit_file.exists():
        junit_summary = parse_pytest_junit(junit_file, paths)
        report_pytest_summary(junit_summary)

    if run_id:
        perf_report_path = paths.test_logs_dir / f"pytest_performance_{run_id}.json"
        if perf_report_path.exists():
            perf_report = load_performance_report(perf_report_path, paths)
            report_perf_summary(perf_report)

    # Raise tickets for failures if JUnit XML was generated
    tickets_raised = 0
    if junit_summary and process.returncode != 0:
        print("\nRaising tickets for pytest failures...")
        tickets_raised = raise_tickets_for_pytest_failures(junit_summary, paths)
        print(f"  → {tickets_raised} ticket(s) raised for pytest failures\n")

    return {
        "returncode": process.returncode,
        "command": " ".join(cmd),
        "tickets_raised": tickets_raised,
        "summary": {
            "tests": junit_summary["tests"],
            "passed": junit_summary["passed"],
            "failures": junit_summary["failures"],
            "errors": junit_summary["errors"],
            "skipped": junit_summary["skipped"],
            "failed_tests": [entry["id"] for entry in junit_summary["failed_tests"]],
            "error_tests": [entry["id"] for entry in junit_summary["error_tests"]],
        } if junit_summary else None,
        "performance_report": str(perf_report_path) if perf_report_path and perf_report_path.exists() else None,
        "slow_test_count": perf_report.get("slow_tests") if perf_report else None,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Actifix test runner")
    quick_group = parser.add_mutually_exclusive_group()
    quick_group.add_argument("--quick", action="store_true", help="Run the quick test subset (default)")
    quick_group.add_argument("--full", action="store_true", help="Run the full pytest suite including slow tests")
    quick_group.add_argument("--slow", action="store_true", help="Include slow/integration tests in the run")
    parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    parser.add_argument("--fast-coverage", action="store_true", help="Fast coverage mode (exclude slow tests, use parallel execution)")
    parser.add_argument("--pattern", type=str, help="Pytest -k pattern")
    args = parser.parse_args(argv)

    reset_actifix_paths()

    reporter, runner, system_summary = run_system_suite()
    plan = system_summary["plan"]
    result = system_summary["result"]

    print(
        f"\nSystem tests summary: {result.passed} passed, {result.failed} failed, "
        f"{result.errors} errors ({result.duration_seconds:.2f}s)"
    )
    if result.failed_tests:
        print("  Failed system tests:")
        for name in result.failed_tests:
            print(f"    - {name}")
    if result.error_tests:
        print("  System test errors:")
        for name in result.error_tests:
            print(f"    - {name}")

    quick = True
    runslow = False
    if args.full:
        quick = False
        runslow = True
    elif args.slow:
        quick = False
        runslow = True
    elif args.quick:
        quick = True

    # Default: fast mode (exclude slow tests, use parallel)
    # --full or --slow: include all tests
    # --fast-coverage: explicit fast coverage mode
    use_fast_mode = not (args.full or args.slow)
    use_fast_coverage = args.fast_coverage or use_fast_mode or (args.coverage and os.getenv("ACTIFIX_FAST_COVERAGE"))

    pytest_targets: list[str]
    if args.full or args.slow:
        pytest_targets = ["test"]
    elif args.coverage:
        pytest_targets = _resolve_pytest_targets(COVERAGE_PYTEST_FILES) or ["test"]
    else:
        pytest_targets = _resolve_pytest_targets(QUICK_PYTEST_FILES) or ["test"]

    pytest_stage = run_pytest(
        args.coverage,
        quick,
        args.pattern,
        targets=pytest_targets,
        runslow=runslow,
        fast_coverage=use_fast_coverage,
        run_id=reporter.run_id,
        paths=reporter.paths,
    )
    reporter.record_stage(
        "pytest",
        pytest_stage["returncode"] == 0,
        pytest_stage,
    )
    
    log_path = reporter.write_cycle_log(plan, result)
    print(f"\nTest cycle log written to: {log_path}")
    
    if not result.success or pytest_stage["returncode"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
