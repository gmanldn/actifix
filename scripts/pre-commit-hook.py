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
import re

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

def _read_version_from_pyproject(pyproject_path: Path) -> str | None:
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\\s*=\\s*\"([^\"]+)\"', content, re.MULTILINE)
    return match.group(1) if match else None

def _read_version_from_init(init_path: Path) -> str | None:
    content = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\\s*=\\s*\"([^\"]+)\"', content, re.MULTILINE)
    return match.group(1) if match else None

def _read_asset_version(index_path: Path) -> str | None:
    content = index_path.read_text(encoding="utf-8")
    match = re.search(r'ACTIFIX_ASSET_VERSION\\s*=\\s*\"([^\"]+)\"', content)
    return match.group(1) if match else None

def check_version_consistency() -> bool:
    """Ensure project versions are consistent before commit."""
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = repo_root / "pyproject.toml"
    init_file = repo_root / "src" / "actifix" / "__init__.py"
    frontend_index = repo_root / "actifix-frontend" / "index.html"

    if not pyproject.exists() or not init_file.exists():
        return True

    pyproject_version = _read_version_from_pyproject(pyproject)
    init_version = _read_version_from_init(init_file)
    asset_version = _read_asset_version(frontend_index) if frontend_index.exists() else None

    mismatches = []
    if not pyproject_version:
        mismatches.append("pyproject.toml version missing")
    if not init_version:
        mismatches.append("src/actifix/__init__.py __version__ missing")
    if pyproject_version and init_version and pyproject_version != init_version:
        mismatches.append(f"pyproject.toml ({pyproject_version}) != __init__.py ({init_version})")
    if asset_version and pyproject_version and asset_version != pyproject_version:
        mismatches.append(f"actifix-frontend/index.html ({asset_version}) != pyproject.toml ({pyproject_version})")

    if mismatches:
        print("✗ Version mismatch detected:")
        for issue in mismatches:
            print(f"  - {issue}")
        return False

    print("✓ Version consistency check passed")
    return True

def main():
    """Main pre-commit hook logic."""
    staged_files = get_staged_files()

    if not staged_files or staged_files == [""]:
        print("✓ No staged files - skipping pre-commit tests")
        return 0

    if not check_version_consistency():
        return 1

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
