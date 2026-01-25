"""
Tests for completion hook execution.
"""

import os
import stat
import tempfile
from pathlib import Path
import pytest

from actifix.completion_hooks import (
    execute_completion_hooks,
    _execute_hook,
    _prepare_hook_env,
)


def test_prepare_hook_env():
    """Test environment preparation for hooks."""
    ticket = {
        "id": "ACT-123",
        "priority": "P1",
        "error_type": "ValueError",
        "source": "test.py:42",
        "status": "Completed",
        "message": "Test error",
    }

    env = _prepare_hook_env(ticket)

    assert env["ACTIFIX_TICKET_ID"] == "ACT-123"
    assert env["ACTIFIX_TICKET_PRIORITY"] == "P1"
    assert env["ACTIFIX_TICKET_ERROR_TYPE"] == "ValueError"
    assert env["ACTIFIX_TICKET_SOURCE"] == "test.py:42"
    assert env["ACTIFIX_TICKET_STATUS"] == "Completed"
    assert "ACTIFIX_TICKET_JSON" in env
    assert "ACT-123" in env["ACTIFIX_TICKET_JSON"]


def test_execute_hook_success():
    """Test successful hook execution."""
    # Create a simple test script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Hook executed'\n")
        f.write("echo \"Ticket: $ACTIFIX_TICKET_ID\"\n")
        f.write("exit 0\n")
        script_path = f.name

    try:
        # Make script executable
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR)

        ticket = {"id": "ACT-456", "priority": "P2"}
        success, stdout, stderr = _execute_hook(script_path, ticket)

        assert success is True
        assert "Hook executed" in stdout
        assert "ACT-456" in stdout
    finally:
        os.unlink(script_path)


def test_execute_hook_failure():
    """Test hook execution with non-zero exit code."""
    # Create a failing test script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Error occurred' >&2\n")
        f.write("exit 1\n")
        script_path = f.name

    try:
        # Make script executable
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR)

        ticket = {"id": "ACT-789"}
        success, stdout, stderr = _execute_hook(script_path, ticket)

        assert success is False
        assert "Error occurred" in stderr
    finally:
        os.unlink(script_path)


def test_execute_hook_timeout():
    """Test hook execution timeout."""
    # Create a script that sleeps too long
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\n")
        f.write("sleep 60\n")
        script_path = f.name

    try:
        # Make script executable
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR)

        ticket = {"id": "ACT-999"}
        success, stdout, stderr = _execute_hook(script_path, ticket, timeout_seconds=1)

        assert success is False
        assert "timeout" in stderr.lower()
    finally:
        os.unlink(script_path)


def test_execute_hook_nonexistent():
    """Test hook execution with nonexistent script."""
    ticket = {"id": "ACT-111"}
    success, stdout, stderr = _execute_hook("/nonexistent/script.sh", ticket)

    assert success is False
    assert "not found" in stderr.lower()


def test_execute_hook_not_executable():
    """Test hook execution with non-executable script."""
    # Create a non-executable test script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\necho 'test'\n")
        script_path = f.name

    try:
        # Ensure it's NOT executable
        os.chmod(script_path, stat.S_IRUSR | stat.S_IWUSR)

        ticket = {"id": "ACT-222"}
        success, stdout, stderr = _execute_hook(script_path, ticket)

        assert success is False
        assert "not executable" in stderr.lower()
    finally:
        os.unlink(script_path)


def test_execute_completion_hooks_no_config():
    """Test hook execution with no hooks configured."""
    ticket = {"id": "ACT-333"}
    results = execute_completion_hooks(ticket)

    assert results["hooks_run"] == 0
    assert results["hooks_succeeded"] == 0
    assert results["hooks_failed"] == 0


def test_execute_completion_hooks_multiple():
    """Test execution of multiple hooks."""
    # Create two test scripts
    scripts = []
    for i in range(2):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
            f.write("#!/bin/bash\n")
            f.write(f"echo 'Hook {i}'\n")
            f.write("exit 0\n")
            os.chmod(f.name, os.stat(f.name).st_mode | stat.S_IXUSR)
            scripts.append(f.name)

    try:
        # Mock config to return our test scripts
        from actifix.config import ActifixConfig, set_config, get_actifix_paths
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=get_actifix_paths(),
            completion_hook_scripts=",".join(scripts),
            completion_hooks_enabled=True,
        )
        set_config(config)

        ticket = {"id": "ACT-444", "priority": "P1"}
        results = execute_completion_hooks(ticket)

        assert results["hooks_run"] == 2
        assert results["hooks_succeeded"] == 2
        assert results["hooks_failed"] == 0
    finally:
        for script in scripts:
            os.unlink(script)
        from actifix.config import reset_config
        reset_config()


def test_execute_completion_hooks_with_failures():
    """Test hook execution with some failures."""
    # Create one success and one failure script
    scripts = []

    # Success script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\necho 'success'\nexit 0\n")
        os.chmod(f.name, os.stat(f.name).st_mode | stat.S_IXUSR)
        scripts.append(f.name)

    # Failure script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
        f.write("#!/bin/bash\necho 'failed' >&2\nexit 1\n")
        os.chmod(f.name, os.stat(f.name).st_mode | stat.S_IXUSR)
        scripts.append(f.name)

    try:
        # Mock config to return our test scripts
        from actifix.config import ActifixConfig, set_config, get_actifix_paths
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=get_actifix_paths(),
            completion_hook_scripts=",".join(scripts),
            completion_hooks_enabled=True,
        )
        set_config(config)

        ticket = {"id": "ACT-555", "priority": "P2"}
        results = execute_completion_hooks(ticket)

        assert results["hooks_run"] == 2
        assert results["hooks_succeeded"] == 1
        assert results["hooks_failed"] == 1
        assert len(results["failures"]) == 1
        assert "failed" in results["failures"][0]["stderr"]
    finally:
        for script in scripts:
            os.unlink(script)
        from actifix.config import reset_config
        reset_config()
