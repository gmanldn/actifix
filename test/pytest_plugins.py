#!/usr/bin/env python3
"""
Pytest plugin for test performance profiling and optimization.

Automatically detects slow tests and categorizes them.
Generates reports for performance analysis.
"""

import pytest
from collections import defaultdict
from typing import Dict, List


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

    def report(self):
        """Generate performance report."""
        if not self.slow_tests:
            if self.hang_tests:
                self._report_hangs()
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


# Global tracker instance
_slow_test_tracker = SlowTestTracker(slow_threshold_ms=100)


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
    _slow_test_tracker.report()
