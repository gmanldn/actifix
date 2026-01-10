"""
Deterministic test-cycle reporting for Actifix.

Mirrors the Pokertool-style inventory → execution → summary flow with:
- Declared plan inventory (with tag counts)
- Numbered, colored progress output
- JSON stage summaries written to state_dir/test_logs
- AFLog entries for every cycle
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterable, Dict, Any

from . import TestPlan, TestResult, TestCase, TestStatus
from ..state_paths import ActifixPaths, get_actifix_paths, ensure_actifix_dirs
from ..log_utils import log_event, atomic_write
from . import TestRunner


YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


class TestCycleReporter:
    """Handles inventory, progress, and persistence for a test cycle."""
    
    def __init__(
        self,
        paths: Optional[ActifixPaths] = None,
        cycle_name: str = "actifix-tests",
    ):
        self.paths = paths or get_actifix_paths()
        ensure_actifix_dirs(self.paths)
        
        self.cycle_name = cycle_name
        self.started_at = datetime.now(timezone.utc)
        self.run_id = self.started_at.strftime("%Y%m%dT%H%M%SZ")
        self.test_log_dir = self.paths.test_logs_dir
        self.test_log_dir.mkdir(parents=True, exist_ok=True)
        
        self._stage_logs: list[dict[str, Any]] = []
    
    def announce_plan(self, plan: TestPlan) -> None:
        """Print the yellow inventory line plus per-tag counts."""
        total = len(plan.tests)
        tag_counts: dict[str, int] = {}
        for test in plan.tests:
            for tag in test.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        tag_summary = ", ".join(f"{tag}:{count}" for tag, count in sorted(tag_counts.items()))
        inventory_line = f"{YELLOW}Inventory: {total} test(s){RESET}"
        if tag_summary:
            inventory_line += f" [{tag_summary}]"
        print(inventory_line)
    
    def progress(
        self,
        current: int,
        total: int,
        test_case: TestCase,
        status: TestStatus = TestStatus.RUNNING,
    ) -> None:
        """Emit numbered progress lines with status coloring."""
        symbols = {
            TestStatus.RUNNING: "...",
            TestStatus.PASSED: f"{GREEN}✓{RESET}",
            TestStatus.FAILED: f"{RED}✗{RESET}",
            TestStatus.ERROR: f"{RED}!{RESET}",
            TestStatus.SKIPPED: f"{YELLOW}-{RESET}",
            TestStatus.PENDING: " ",
        }
        symbol = symbols.get(status, "?")
        line = f"[{current}/{total}] {test_case.name} {symbol}"
        print(line)
    
    def record_stage(self, stage_name: str, success: bool, details: dict[str, Any]) -> None:
        """Collect stage results for the consolidated test cycle log."""
        self._stage_logs.append({
            "stage": stage_name,
            "success": success,
            "details": details,
        })

    def bind_to_runner(self, runner: TestRunner) -> None:
        """Attach this reporter to a TestRunner for progress output."""
        runner.set_progress_callback(self.progress)
    
    def write_cycle_log(
        self,
        plan: TestPlan,
        result: TestResult,
        extra_stages: Optional[Iterable[dict[str, Any]]] = None,
    ) -> Path:
        """
        Write a JSON summary for the cycle.
        
        Returns:
            Path to the written JSON log.
        """
        finished_at = datetime.now(timezone.utc)
        log_path = self.test_log_dir / f"test_cycle_{self.run_id}.json"
        
        cycle = {
            "cycle": self.cycle_name,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "plan": {
                "name": plan.name,
                "total": len(plan.tests),
                "declared_at": plan.created_at.isoformat(),
                "min_coverage": plan.min_coverage_percent,
                "tags": [test.tags for test in plan.tests],
            },
            "result": {
                "success": result.success,
                "total": result.total_tests,
                "executed": result.executed_tests,
                "passed": result.passed,
                "failed": result.failed,
                "errors": result.errors,
                "skipped": result.skipped,
                "plan_matched": result.plan_matched,
                "plan_mismatch_reason": result.plan_mismatch_reason,
                "failed_tests": result.failed_tests,
                "error_tests": result.error_tests,
                "duration_seconds": result.duration_seconds,
            },
            "stages": list(self._stage_logs),
        }
        
        if extra_stages:
            cycle["stages"].extend(list(extra_stages))
        
        atomic_write(log_path, json.dumps(cycle, indent=2))
        
        log_event(
            self.paths.aflog_file,
            "TEST_CYCLE_COMPLETED",
            f"Test cycle {self.cycle_name} completed",
            extra={
                "run_id": self.run_id,
                "passed": result.passed,
                "failed": result.failed,
                "errors": result.errors,
            }
        )
        
        return log_path
