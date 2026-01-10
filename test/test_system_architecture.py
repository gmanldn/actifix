#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Actifix system test architecture.
"""

import sys
from pathlib import Path
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.state_paths import (
    get_actifix_paths,
    init_actifix_files,
    reset_actifix_paths,
    ensure_actifix_dirs,
)
from actifix.testing import TestRunner
from actifix.testing.reporting import TestCycleReporter
from actifix.testing.system import build_system_tests


@pytest.fixture
def temp_paths(tmp_path):
    """Create isolated Actifix paths for testing."""
    reset_actifix_paths()
    paths = get_actifix_paths(
        base_dir=tmp_path / "actifix",
        state_dir=tmp_path / ".state",
        logs_dir=tmp_path / "logs",
    )
    ensure_actifix_dirs(paths)
    init_actifix_files(paths)
    return paths


def test_actifix_paths_initialization(temp_paths):
    """Actifix paths should create artifacts and directories."""
    for artifact in temp_paths.all_artifacts:
        assert artifact.exists()
    assert temp_paths.test_logs_dir.exists()
    assert temp_paths.quarantine_dir.exists()


def test_test_cycle_reporter_writes_log(temp_paths):
    """Reporter should emit a JSON cycle summary."""
    runner = TestRunner("reporter-test", paths=temp_paths)
    reporter = TestCycleReporter(paths=temp_paths, cycle_name="reporter-test")
    reporter.bind_to_runner(runner)
    
    runner.add_test("sample", lambda: None, description="sample", tags=["sample"])
    
    plan = runner.declare_plan()
    reporter.announce_plan(plan)
    result = runner.execute()
    reporter.record_stage("system-tests", True, {})
    log_path = reporter.write_cycle_log(plan, result)
    
    assert log_path.exists()
    content = log_path.read_text()
    assert "reporter-test" in content


def test_system_test_builder_returns_tests(temp_paths):
    """System test builder should expose generic dependency checks."""
    tests = build_system_tests(temp_paths)
    assert tests, "Expected at least one system test"
    names = [t[0] for t in tests]
    assert "python_version" in names
