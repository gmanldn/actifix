#!/usr/bin/env python3

"""
Actifix consolidated test runner.

Runs deterministic system/bootstrap checks using the Actifix testing framework
and then executes the pytest suite. Produces Pokertool-style inventory +
progress output and writes stage summaries to state_dir/test_logs.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT = Path(__file__).parent
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
    
    summary = {
        "plan": plan,
        "result": result,
    }
    return reporter, runner, summary


def run_pytest(coverage: bool, quick: bool, pattern: Optional[str]) -> Dict[str, Any]:
    """Execute pytest with optional coverage and pattern filtering."""
    cmd: List[str] = [sys.executable, "-m", "pytest"]
    
    if quick:
        # Quick mode keeps the suite narrow and quiet
        cmd += ["-q", "test"]
    else:
        cmd.append("test")
    
    if pattern:
        cmd += ["-k", pattern]
    
    if coverage:
        cmd += ["--cov=src/actifix", "--cov-report=term-missing"]
    
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT / "src"))
    
    print("\nRunning pytest suite...")
    process = subprocess.run(cmd, cwd=ROOT, env=env)
    
    return {
        "returncode": process.returncode,
        "command": " ".join(cmd),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Actifix test runner")
    parser.add_argument("--quick", action="store_true", help="Run a faster subset of tests")
    parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    parser.add_argument("--pattern", type=str, help="Pytest -k pattern")
    args = parser.parse_args(argv)
    
    reset_actifix_paths()
    
    reporter, runner, system_summary = run_system_suite()
    plan = system_summary["plan"]
    result = system_summary["result"]
    
    pytest_stage = run_pytest(args.coverage, args.quick, args.pattern)
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
