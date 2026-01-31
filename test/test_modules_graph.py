"""Tests for modules graph command."""

import subprocess
import sys


def test_modules_graph_renders_dependencies():
    """Test that modules graph command renders module dependencies."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "modules", "graph"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    output = result.stdout

    # Should have header
    assert "Module Dependency Graph" in output

    # Should show node/edge counts
    assert "Nodes:" in output
    assert "Edges:" in output

    # Should list at least one module
    assert "modules." in output

    # Should show dependencies
    assert "depends on:" in output or "(no dependencies" in output


def test_modules_graph_shows_bgjobs_module():
    """Test that the graph includes the bgjobs module we created."""
    result = subprocess.run(
        [sys.executable, "-m", "actifix.main", "modules", "graph"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout

    # Should show bgjobs module
    assert "modules.bgjobs" in output

    # Should show it depends on base
    if "modules.bgjobs" in output:
        # Find the bgjobs section
        lines = output.split("\n")
        in_bgjobs = False
        found_deps = False
        for line in lines:
            if "modules.bgjobs" in line and "(" in line:
                in_bgjobs = True
            elif in_bgjobs and "depends on:" in line:
                found_deps = True
            elif in_bgjobs and "modules.base" in line:
                # Found the dependency
                break
            elif in_bgjobs and line.strip() and not line.startswith(" "):
                # Moved to next module
                in_bgjobs = False

        assert found_deps, "bgjobs should have dependencies listed"
