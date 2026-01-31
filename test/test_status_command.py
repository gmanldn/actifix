"""Tests for status command."""

import subprocess
import sys


def test_status_command_shows_runtime_summary():
    """Test that status command shows concise runtime summary."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "status"],
        capture_output=True,
        text=True,
    )

    # Command should succeed (exit 0 or 1 depending on health)
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"
    output = result.stdout

    # Should have header
    assert "Actifix Runtime Status" in output

    # Should show timestamp
    assert "Timestamp:" in output

    # Should show health status
    assert "Health:" in output
    assert "OK" in output or "DEGRADED" in output

    # Should show ticket metrics
    assert "Tickets" in output
    assert "Open:" in output
    assert "Completed:" in output

    # Should show priority breakdown
    assert "By Priority" in output


def test_status_command_shows_priority_breakdown():
    """Test that status shows priority breakdown section."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "status"],
        capture_output=True,
        text=True,
    )

    output = result.stdout

    # Should show priority section header (even if empty)
    assert "By Priority" in output
