"""
Actifix Testing Framework - Deterministic test execution with plan verification.

Provides a testing framework that:
- Declares the full test plan before execution
- Executes exactly the declared plan
- Fails if executed test count differs from plan
- Provides deterministic, numbered progress reporting
"""

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Any

from .bootstrap import get_state, get_correlation_id
from .log_utils import log_event, atomic_write
from .state_paths import get_actifix_paths, ActifixPaths


class TestStatus(Enum):
    """Status of a test case."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """A single test case."""
    
    name: str
    func: Callable[[], Any]
    description: str = ""
    tags: list[str] = field(default_factory=list)
    timeout_seconds: float = 60.0
    
    # Execution state
    status: TestStatus = TestStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error_message: str = ""
    error_traceback: str = ""


@dataclass
class TestPlan:
    """A declared test plan."""
    
    name: str
    tests: list[TestCase]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Coverage requirements
    min_coverage_percent: float = 0.0
    critical_paths: list[str] = field(default_factory=list)
    
    # Execution state
    executed: bool = False
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0


@dataclass
class TestResult:
    """Result of executing a test plan."""
    
    plan_name: str
    total_tests: int
    executed_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    
    duration_seconds: float
    started_at: datetime
    finished_at: datetime
    
    success: bool
    failed_tests: list[str] = field(default_factory=list)
    error_tests: list[str] = field(default_factory=list)
    
    # Plan verification
    plan_matched: bool = True
    plan_mismatch_reason: str = ""


class TestRunner:
    """
    Deterministic test runner with plan verification.
    
    Usage:
        runner = TestRunner("my-tests")
        
        # Declare tests
        runner.add_test("test_one", test_one_func, "Tests one thing")
        runner.add_test("test_two", test_two_func, "Tests another")
        
        # Declare and verify plan
        plan = runner.declare_plan()
        print(f"Will run {len(plan.tests)} tests")
        
        # Execute
        result = runner.execute()
        
        if not result.success:
            print(f"Failed: {result.failed_tests}")
    """
    
    def __init__(
        self,
        name: str,
        paths: Optional[ActifixPaths] = None,
        min_coverage: float = 0.0,
    ):
        self.name = name
        self.paths = paths or get_actifix_paths()
        self.min_coverage = min_coverage
        
        self._tests: list[TestCase] = []
        self._plan: Optional[TestPlan] = None
        self._result: Optional[TestResult] = None
        
        # Progress callback
        self._progress_callback: Optional[Callable[[int, int, TestCase], None]] = None
    
    def add_test(
        self,
        name: str,
        func: Callable[[], Any],
        description: str = "",
        tags: Optional[list[str]] = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Add a test to the runner.
        
        Args:
            name: Unique test name.
            func: Test function (no arguments, raises on failure).
            description: Human-readable description.
            tags: Optional tags for filtering.
            timeout: Timeout in seconds.
        """
        # Check for duplicate
        for existing in self._tests:
            if existing.name == name:
                raise ValueError(f"Duplicate test name: {name}")
        
        test = TestCase(
            name=name,
            func=func,
            description=description,
            tags=tags or [],
            timeout_seconds=timeout,
        )
        self._tests.append(test)
    
    def set_progress_callback(
        self,
        callback: Callable[[int, int, TestCase], None],
    ) -> None:
        """
        Set callback for progress reporting.
        
        Args:
            callback: Function(current_index, total, test_case)
        """
        self._progress_callback = callback
    
    def declare_plan(
        self,
        filter_tags: Optional[list[str]] = None,
    ) -> TestPlan:
        """
        Declare the test plan before execution.
        
        This MUST be called before execute() and the plan will be
        verified during execution.
        
        Args:
            filter_tags: Optional tags to filter tests.
        
        Returns:
            TestPlan with all tests to be executed.
        """
        tests = self._tests
        
        # Filter by tags if specified
        if filter_tags:
            tests = [
                t for t in tests
                if any(tag in t.tags for tag in filter_tags)
            ]
        
        self._plan = TestPlan(
            name=self.name,
            tests=tests,
            min_coverage_percent=self.min_coverage,
        )
        
        # Log plan declaration
        log_event(
            self.paths.aflog_file,
            "TEST_PLAN_DECLARED",
            f"Test plan declared: {self.name}",
            extra={
                "total_tests": len(tests),
                "correlation_id": get_correlation_id(),
            }
        )
        
        return self._plan
    
    def execute(self) -> TestResult:
        """
        Execute the declared test plan.
        
        Returns:
            TestResult with execution details.
        
        Raises:
            RuntimeError: If plan not declared.
            RuntimeError: If executed count differs from plan.
        """
        if self._plan is None:
            raise RuntimeError(
                "Test plan not declared. Call declare_plan() first."
            )
        
        started_at = datetime.now(timezone.utc)
        total = len(self._plan.tests)
        executed = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        failed_tests = []
        error_tests = []
        
        # Log execution start
        log_event(
            self.paths.aflog_file,
            "TEST_EXECUTION_STARTED",
            f"Executing {total} tests",
            extra={"plan": self.name}
        )
        
        for index, test in enumerate(self._plan.tests):
            # Report progress
            if self._progress_callback:
                self._progress_callback(index + 1, total, test)
            else:
                print(f"[{index + 1}/{total}] {test.name}...", end=" ", flush=True)
            
            # Execute test
            test.started_at = datetime.now(timezone.utc)
            test.status = TestStatus.RUNNING
            
            try:
                start_time = time.time()
                test.func()
                test.duration_seconds = time.time() - start_time
                
                test.status = TestStatus.PASSED
                passed += 1
                
                if not self._progress_callback:
                    print(f"PASS ({test.duration_seconds:.3f}s)")
                
            except AssertionError as e:
                test.duration_seconds = time.time() - start_time
                test.status = TestStatus.FAILED
                test.error_message = str(e)
                test.error_traceback = traceback.format_exc()
                failed += 1
                failed_tests.append(test.name)
                
                if not self._progress_callback:
                    print(f"FAIL: {e}")
                
            except Exception as e:
                test.duration_seconds = time.time() - start_time
                test.status = TestStatus.ERROR
                test.error_message = str(e)
                test.error_traceback = traceback.format_exc()
                errors += 1
                error_tests.append(test.name)
                
                if not self._progress_callback:
                    print(f"ERROR: {e}")
            
            test.finished_at = datetime.now(timezone.utc)
            executed += 1
        
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()
        
        # Verify plan was fully executed
        plan_matched = True
        plan_mismatch_reason = ""
        
        if executed != total:
            plan_matched = False
            plan_mismatch_reason = (
                f"Plan declared {total} tests but only {executed} were executed"
            )
        
        # Determine success
        success = (
            plan_matched and
            failed == 0 and
            errors == 0
        )
        
        self._result = TestResult(
            plan_name=self.name,
            total_tests=total,
            executed_tests=executed,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_seconds=duration,
            started_at=started_at,
            finished_at=finished_at,
            success=success,
            failed_tests=failed_tests,
            error_tests=error_tests,
            plan_matched=plan_matched,
            plan_mismatch_reason=plan_mismatch_reason,
        )
        
        # Mark plan as executed
        self._plan.executed = True
        self._plan.passed_count = passed
        self._plan.failed_count = failed
        self._plan.skipped_count = skipped
        self._plan.error_count = errors
        
        # Log result
        log_event(
            self.paths.aflog_file,
            "TEST_EXECUTION_COMPLETED",
            f"Tests completed: {passed}/{total} passed",
            extra={
                "plan": self.name,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "duration": duration,
                "success": success,
            }
        )
        
        # Verify plan execution
        if not plan_matched:
            raise RuntimeError(
                f"Test plan verification failed: {plan_mismatch_reason}"
            )
        
        return self._result
    
    def get_result(self) -> Optional[TestResult]:
        """Get the last execution result."""
        return self._result
    
    def format_report(self) -> str:
        """Format the test result as a report string."""
        if self._result is None:
            return "No test results available."
        
        r = self._result
        lines = [
            "=" * 60,
            f"TEST REPORT: {r.plan_name}",
            "=" * 60,
            "",
            f"Status: {'SUCCESS' if r.success else 'FAILURE'}",
            f"Duration: {r.duration_seconds:.2f}s",
            f"Started: {r.started_at.isoformat()}",
            "",
            "--- Results ---",
            f"Total Tests: {r.total_tests}",
            f"Executed: {r.executed_tests}",
            f"Passed: {r.passed}",
            f"Failed: {r.failed}",
            f"Errors: {r.errors}",
            f"Skipped: {r.skipped}",
            "",
        ]
        
        if r.failed_tests:
            lines.append("--- Failed Tests ---")
            for name in r.failed_tests:
                lines.append(f"  ✗ {name}")
            lines.append("")
        
        if r.error_tests:
            lines.append("--- Error Tests ---")
            for name in r.error_tests:
                lines.append(f"  ! {name}")
            lines.append("")
        
        if not r.plan_matched:
            lines.extend([
                "--- Plan Verification Failed ---",
                f"  {r.plan_mismatch_reason}",
                "",
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def run_tests(
    name: str,
    tests: list[tuple[str, Callable[[], Any]]],
    paths: Optional[ActifixPaths] = None,
) -> TestResult:
    """
    Convenience function to run a list of tests.
    
    Args:
        name: Test suite name.
        tests: List of (name, func) tuples.
        paths: Optional paths override.
    
    Returns:
        TestResult.
    """
    runner = TestRunner(name, paths=paths)
    
    for test_name, test_func in tests:
        runner.add_test(test_name, test_func)
    
    runner.declare_plan()
    result = runner.execute()
    
    print(runner.format_report())
    
    return result


def assert_equals(actual: Any, expected: Any, message: str = "") -> None:
    """Assert two values are equal."""
    if actual != expected:
        msg = message or f"Expected {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def assert_true(value: bool, message: str = "") -> None:
    """Assert value is True."""
    if not value:
        msg = message or f"Expected True, got {value!r}"
        raise AssertionError(msg)


def assert_false(value: bool, message: str = "") -> None:
    """Assert value is False."""
    if value:
        msg = message or f"Expected False, got {value!r}"
        raise AssertionError(msg)


def assert_raises(
    exception_type: type,
    func: Callable[[], Any],
    message: str = "",
) -> None:
    """Assert that function raises specified exception."""
    try:
        func()
        msg = message or f"Expected {exception_type.__name__} to be raised"
        raise AssertionError(msg)
    except exception_type:
        pass  # Expected
    except Exception as e:
        msg = message or f"Expected {exception_type.__name__}, got {type(e).__name__}"
        raise AssertionError(msg)


def assert_contains(container: Any, item: Any, message: str = "") -> None:
    """Assert container contains item."""
    if item not in container:
        msg = message or f"Expected {container!r} to contain {item!r}"
        raise AssertionError(msg)
