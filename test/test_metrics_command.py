"""Tests for metrics command."""

import subprocess
import sys


def test_metrics_command_shows_operational_stats():
    """Test that metrics command shows operational statistics."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "metrics"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout

    # Should have header
    assert "Operational Metrics" in output

    # Should show timestamp
    assert "Generated:" in output

    # Should show ticket metrics section
    assert "Ticket Metrics" in output
    assert "Total Tickets:" in output
    assert "Open:" in output
    assert "Completed:" in output

    # Should show priority distribution
    assert "Priority Distribution" in output

    # Should show health metrics
    assert "Health Metrics" in output
    assert "System Health:" in output


def test_metrics_command_shows_percentages():
    """Test that metrics includes percentage calculations."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "metrics"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout

    # Should include percentage in priority distribution
    # Format is "P0: X (Y.Y%)"
    assert "%" in output or "Total Tickets: 0" in output
