#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-commit hook for Actifix: Run tests on changed modules only.

Intelligently detects which modules were changed and runs tests for those modules.
Falls back to full test suite for core modules or test changes.

To install: cp scripts/pre-commit-hook.py .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
"""

import subprocess
import sys
from pathlib import Path

def get_staged_files():
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []

def get_changed_modules(files):
    """Extract module names from changed files."""
    modules = set()
    for file in files:
        if file.startswith("src/actifix/") and file.endswith(".py"):
            # Extract module name from path like src/actifix/do_af.py
            module = Path(file).stem
            if module and module != "__init__":
                modules.add(module)
    return modules

def should_run_full_suite(files):
    """Check if full test suite should be run."""
    critical_paths = [
        "src/actifix/__init__.py",
        "src/actifix/bootstrap.py",
        "src/actifix/raise_af.py",
        "src/actifix/do_af.py",
        "src/actifix/state_paths.py",
        "pyproject.toml",
        "test/",
        ".github/workflows/",
    ]

    for file in files:
        for critical in critical_paths:
            if file.startswith(critical):
                return True
    return False

def run_tests(modules=None):
    """Run tests for specified modules or full suite."""
    env = dict(subprocess.os.environ)
    env["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
    env["ACTIFIX_CAPTURE_ENABLED"] = "0"

    if modules:
        print(f"🧪 Running tests for changed modules: {', '.join(sorted(modules))}")
        # Run tests for specific modules
        cmd = ["python", "-m", "pytest", "test/", "-v", "--tb=short", "-x"]
        # Build pattern matching for module tests
        patterns = " or ".join([f"test_{m}" for m in modules])
        cmd.extend(["-k", patterns])
    else:
        print("📋 Critical files changed - running full test suite")
        cmd = ["python", "test/test_runner.py"]

    result = subprocess.run(cmd, env=env)
    return result.returncode

def main():
    """Main pre-commit hook logic."""
    staged_files = get_staged_files()

    if not staged_files or staged_files == [""]:
        print("✓ No staged files - skipping pre-commit tests")
        return 0

    # Check if we should run full suite
    if should_run_full_suite(staged_files):
        print("📋 Critical files changed - running full test suite")
        return_code = run_tests()
    else:
        # Get changed modules
        modules = get_changed_modules(staged_files)

        if not modules:
            print("✓ No Python modules changed - skipping tests")
            return 0

        # Run tests for changed modules
        return_code = run_tests(modules)

    if return_code == 0:
        print("✓ Pre-commit tests passed")
    else:
        print("✗ Pre-commit tests failed - commit aborted")

    return return_code

if __name__ == "__main__":
    sys.exit(main())
