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


def raise_tickets_for_pytest_failures(junit_file: Path, paths) -> int:
    """Parse JUnit XML and raise tickets for pytest failures."""
    import xml.etree.ElementTree as ET

    tickets_raised = 0

    try:
        tree = ET.parse(junit_file)
        root = tree.getroot()

        # Iterate through all testcases
        for testsuite in root.findall(".//testsuite"):
            for testcase in testsuite.findall("testcase"):
                classname = testcase.get("classname", "unknown")
                name = testcase.get("name", "unknown")
                test_id = f"{classname}::{name}"

                # Check for failures
                failure = testcase.find("failure")
                if failure is not None:
                    failure_msg = failure.get("message", "Test failed")
                    failure_text = failure.text or ""

                    try:
                        record_error(
                            message=f"Pytest failure: {test_id}\n{failure_msg}",
                            source=classname,
                            run_label="test-suite",
                            error_type="PytestFailure",
                            priority=TicketPriority.P1,
                            stack_trace=failure_text,
                            capture_context=True,
                            paths=paths,
                        )
                        tickets_raised += 1
                        print(f"  ✗ Raised ticket for failed test: {test_id}")
                    except Exception as e:
                        print(f"  ⚠️  Failed to raise ticket for {test_id}: {e}")

                # Check for errors
                error = testcase.find("error")
                if error is not None:
                    error_msg = error.get("message", "Test error")
                    error_text = error.text or ""

                    try:
                        record_error(
                            message=f"Pytest error: {test_id}\n{error_msg}",
                            source=classname,
                            run_label="test-suite",
                            error_type="PytestError",
                            priority=TicketPriority.P0,
                            stack_trace=error_text,
                            capture_context=True,
                            paths=paths,
                        )
                        tickets_raised += 1
                        print(f"  ✗ Raised ticket for test error: {test_id}")
                    except Exception as e:
                        print(f"  ⚠️  Failed to raise ticket for {test_id}: {e}")

    except Exception as e:
        print(f"  ⚠️  Failed to parse JUnit XML: {e}")

    return tickets_raised


def run_pytest(coverage: bool, quick: bool, pattern: Optional[str], fast_coverage: bool = False) -> Dict[str, Any]:
    """Execute pytest with optional coverage and pattern filtering."""
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

    if coverage:
        try:
            import pytest_cov  # noqa: F401
            cmd += ["--cov=src/actifix", "--cov-report=term-missing"]
        except ImportError:
            print("pytest-cov plugin not found; skipping coverage reporting")

        # Fast coverage mode: exclude slow tests and use parallel execution
        if fast_coverage:
            print("  → Fast coverage mode: excluding slow tests and using parallel execution")
            cmd += ["-m", "not slow"]
            cmd.extend(_collect_xdist_args())
        else:
            # Full coverage: run all tests, but still use parallel if available
            cmd.extend(_collect_xdist_args())
    else:
        # Non-coverage runs can also use fast mode
        if fast_coverage:
            cmd += ["-m", "not slow"]

    if quick:
        # Quick mode keeps the suite narrow and quiet
        cmd += ["-q", "test"]
    else:
        cmd.append("test")

    if pattern:
        cmd += ["-k", pattern]

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT / "src"))

    print("\nRunning pytest suite...")
    process = subprocess.run(cmd, cwd=ROOT, env=env)

    # Raise tickets for failures if JUnit XML was generated
    tickets_raised = 0
    if junit_file.exists() and process.returncode != 0:
        print("\nRaising tickets for pytest failures...")
        paths = get_actifix_paths()
        tickets_raised = raise_tickets_for_pytest_failures(junit_file, paths)
        print(f"  → {tickets_raised} ticket(s) raised for pytest failures\n")

    return {
        "returncode": process.returncode,
        "command": " ".join(cmd),
        "tickets_raised": tickets_raised,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Actifix test runner")
    quick_group = parser.add_mutually_exclusive_group()
    quick_group.add_argument("--quick", action="store_true", help="Run the quick test subset (default)")
    quick_group.add_argument("--full", action="store_true", help="Run the full pytest suite")
    parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    parser.add_argument("--fast-coverage", action="store_true", help="Fast coverage mode (exclude slow tests, use parallel execution)")
    parser.add_argument("--pattern", type=str, help="Pytest -k pattern")
    args = parser.parse_args(argv)
    
    reset_actifix_paths()
    
    reporter, runner, system_summary = run_system_suite()
    plan = system_summary["plan"]
    result = system_summary["result"]
    
    quick = True
    if args.full:
        quick = False
    elif args.quick:
        quick = True

    # Use fast coverage mode if specified, otherwise use regular coverage
    use_fast_coverage = args.fast_coverage or (args.coverage and os.getenv("ACTIFIX_FAST_COVERAGE"))
    pytest_stage = run_pytest(args.coverage, quick, args.pattern, fast_coverage=use_fast_coverage)
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