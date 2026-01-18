#!/usr/bin/env python3
"""
Pytest plugin for test performance profiling and optimization.

Automatically detects slow tests and categorizes them.
Generates reports for performance analysis.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import pytest
from actifix.raise_af import TicketPriority, record_error
from actifix.state_paths import get_actifix_paths, ensure_actifix_dirs
from actifix.log_utils import atomic_write


class SlowTestTracker:
    """Track and report on slow tests during execution."""

    def __init__(self, slow_threshold_ms: float = 100, hang_threshold_ms: float = 30000):
        """
        Initialize slow test tracker.

        Args:
            slow_threshold_ms: Threshold in milliseconds to mark test as slow
            hang_threshold_ms: Threshold in milliseconds to call out hanging tests
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.hang_threshold_ms = hang_threshold_ms
        self.slow_tests: List[Dict] = []
        self.hang_tests: List[Dict] = []
        self.test_times: Dict[str, float] = {}
        self.by_category: Dict[str, List[Dict]] = defaultdict(list)
        self.total_collected: int = 0
        self.exitstatus: int = 0

    def set_session_stats(self, total_collected: int, exitstatus: int) -> None:
        """Capture session-wide stats for reporting."""
        self.total_collected = total_collected
        self.exitstatus = exitstatus

    def record_test_time(self, nodeid: str, duration_ms: float, markers: List[str]):
        """Record test execution time."""
        self.test_times[nodeid] = duration_ms

        test_info = {
            "name": nodeid,
            "duration_ms": duration_ms,
            "markers": markers,
        }

        if duration_ms > self.slow_threshold_ms:
            self.slow_tests.append(test_info)

            # Categorize by marker
            if markers:
                for marker in markers:
                    self.by_category[marker].append(test_info)
            else:
                self.by_category["unmarked"].append(test_info)

        if duration_ms >= self.hang_threshold_ms:
            self.hang_tests.append(test_info)

    def _summarize_categories(self) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for category, tests in self.by_category.items():
            total_ms = sum(t["duration_ms"] for t in tests)
            avg_ms = total_ms / len(tests) if tests else 0.0
            summary[category] = {
                "count": len(tests),
                "total_ms": total_ms,
                "avg_ms": avg_ms,
            }
        return summary

    def _resolve_report_path(self, run_id: str) -> Path:
        paths = get_actifix_paths()
        ensure_actifix_dirs(paths)
        return paths.test_logs_dir / f"pytest_performance_{run_id}.json"

    def _build_report_payload(self, run_id: str) -> Dict:
        sorted_tests = sorted(self.slow_tests, key=lambda x: x["duration_ms"], reverse=True)
        total_duration_ms = sum(self.test_times.values())
        return {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "slow_threshold_ms": self.slow_threshold_ms,
            "hang_threshold_ms": self.hang_threshold_ms,
            "total_collected": self.total_collected,
            "total_executed": len(self.test_times),
            "total_duration_ms": total_duration_ms,
            "slow_tests": len(self.slow_tests),
            "hang_tests": len(self.hang_tests),
            "slowest_tests": sorted_tests[:20],
            "slow_tests_sample": sorted_tests[:100],
            "by_category": self._summarize_categories(),
            "exitstatus": self.exitstatus,
        }

    def _write_report(self) -> Path:
        run_id = os.getenv("ACTIFIX_TEST_RUN_ID")
        if not run_id:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = self._resolve_report_path(run_id)
        payload = self._build_report_payload(run_id)
        try:
            atomic_write(report_path, json.dumps(payload, indent=2))
        except Exception as exc:
            record_error(
                message=f"Failed to write pytest performance report: {exc}",
                source="test/pytest_plugins.py::_write_report",
                run_label="test-suite",
                error_type="TestPerformanceReportError",
                priority=TicketPriority.P2,
                capture_context=True,
            )
            raise
        return report_path

    def report(self):
        """Generate performance report."""
        report_path = self._write_report()
        if not self.slow_tests:
            if self.hang_tests:
                self._report_hangs()
                self._record_hang_tickets()
            print(f"Pytest performance report written to {report_path}")
            return

        print("\n" + "=" * 80)
        print("SLOW TEST ANALYSIS")
        print("=" * 80)
        print(f"Threshold: {self.slow_threshold_ms}ms")
        print(f"Total slow tests: {len(self.slow_tests)}")
        print()

        # Sort by duration
        sorted_tests = sorted(self.slow_tests, key=lambda x: x["duration_ms"], reverse=True)

        print("TOP 20 SLOWEST TESTS:")
        print("-" * 80)
        for i, test in enumerate(sorted_tests[:20], 1):
            markers_str = ", ".join(test["markers"]) if test["markers"] else "no markers"
            print(f"{i:2d}. {test['duration_ms']:7.1f}ms | {markers_str:20s} | {test['name']}")

        print("\n" + "-" * 80)
        print("SLOW TESTS BY CATEGORY:")
        print("-" * 80)
        for category, tests in sorted(
            self.by_category.items(), key=lambda x: len(x[1]), reverse=True
        ):
            avg_time = sum(t["duration_ms"] for t in tests) / len(tests)
            total_time = sum(t["duration_ms"] for t in tests)
            print(
                f"{category:20s}: {len(tests):3d} tests, {total_time:8.1f}ms total, {avg_time:7.1f}ms avg"
            )

        print("\n" + "=" * 80)
        if self.hang_tests:
            self._report_hangs()
            self._record_hang_tickets()
        print(f"Pytest performance report written to {report_path}")

    def _report_hangs(self):
        """Print diagnostics for tests that exceed the hang threshold."""
        sorted_hangs = sorted(self.hang_tests, key=lambda x: x["duration_ms"], reverse=True)
        print("\n" + "=" * 80)
        print(f"HANGING TESTS (>= {self.hang_threshold_ms:.0f}ms)")
        print("=" * 80)
        for i, test in enumerate(sorted_hangs[:10], 1):
            markers_str = ", ".join(test["markers"]) if test["markers"] else "no markers"
            print(
                f"{i:2d}. {test['duration_ms']:8.1f}ms | {markers_str:20s} | {test['name']}"
            )
        print("\n" + "=" * 80)

    def _record_hang_tickets(self) -> None:
        """Record P0 tickets for tests that exceeded the hang threshold."""
        for test in self.hang_tests:
            markers_str = ", ".join(test["markers"]) if test["markers"] else "unmarked"
            message = (
                f"Pytest hang detected: {test['name']} took {test['duration_ms']:.1f}ms "
                f"(markers: {markers_str})"
            )
            try:
                record_error(
                    message=message,
                    source="test/pytest_plugins.py::SlowTestTracker",
                    run_label="test-suite",
                    error_type="TestHang",
                    priority=TicketPriority.P0,
                    stack_trace=f"Markers: {markers_str}",
                    capture_context=False,
                )
                print(f"  ✗ Raised hang ticket for {test['name']} ({markers_str})")
            except Exception as exc:
                print(f"  ⚠️  Failed to record hang for {test['name']}: {exc}")


# Global tracker instance
_slow_test_tracker = SlowTestTracker(
    slow_threshold_ms=float(os.getenv("ACTIFIX_SLOW_TEST_THRESHOLD_MS", "100")),
    hang_threshold_ms=float(os.getenv("ACTIFIX_HANG_TEST_THRESHOLD_MS", "30000")),
)


def pytest_configure(config):
    """Register plugin with pytest."""
    config.pluginmanager.register(_slow_test_tracker, "slow_test_tracker")


def pytest_runtest_makereport(item, call):
    """Hook to record test durations."""
    if call.when == "call":
        # Get markers
        markers = [marker.name for marker in item.iter_markers()]

        # Record test time
        duration_ms = call.duration * 1000
        _slow_test_tracker.record_test_time(item.nodeid, duration_ms, markers)


def pytest_sessionfinish(session, exitstatus):
    """Hook called at end of test session."""
    _slow_test_tracker.set_session_stats(session.testscollected or 0, exitstatus)
    _slow_test_tracker.report()
