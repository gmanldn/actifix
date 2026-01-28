#!/usr/bin/env python3
"""Local automation helper for DoAF tickets.

Runs lint/tests, bumps the backend/frontend version, rebuilds assets, and
commits/pushes the sanitized changes for a single automation ticket. Chain this
from a completion hook or run manually when processing an automation ticket
locally.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT / "pyproject.toml"
VERSION_PATTERN = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"', re.MULTILINE)


def run_command(cmd: Sequence[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env or os.environ,
    )
    return result.stdout.strip()


def get_version_from_pyproject() -> str:
    content = PYPROJECT_PATH.read_text()
    match = VERSION_PATTERN.search(content)
    if not match:
        raise RuntimeError("pyproject.toml missing version")
    return match.group("version")


def set_version_in_pyproject(new_version: str) -> None:
    content = PYPROJECT_PATH.read_text()
    updated = VERSION_PATTERN.sub(f'version = "{new_version}"', content)
    PYPROJECT_PATH.write_text(updated)


def bump_patch_version(current: str) -> str:
    parts = current.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"Unsupported version format: {current}")
    major, minor, patch = map(int, parts)
    return f"{major}.{minor}.{patch + 1}"


def assert_raise_af_gate() -> None:
    if os.environ.get("ACTIFIX_CHANGE_ORIGIN") != "raise_af":
        raise RuntimeError("Set ACTIFIX_CHANGE_ORIGIN=raise_af before running automation")


def ensure_clean_worktree() -> None:
    status = run_command(["git", "status", "--porcelain"])  # noqa: F821
    if status.strip():
        raise RuntimeError("Working tree must be clean before running automation script")


def main() -> int:
    parser = argparse.ArgumentParser(description="DoAF automation helper")
    parser.add_argument("--ticket", required=True, help="Ticket ID for the automation run")
    parser.add_argument(
        "--tests",
        nargs="+",
        default=["python3", "-m", "pytest", "test/test_do_af_flow.py"],
        help="Test command to run",
    )
    parser.add_argument(
        "--commit-msg",
        help="Custom commit message (default: chore(do_af): automation (<ticket>))",
    )
    args = parser.parse_args()

    assert_raise_af_gate()
    ensure_clean_worktree()

    print("Fetching latest develop...")
    run_command(["git", "fetch", "origin", "develop"])

    local_version = get_version_from_pyproject()
    remote_pyproject = run_command(["git", "show", "origin/develop:pyproject.toml"])
    remote_match = VERSION_PATTERN.search(remote_pyproject)
    if not remote_match:
        raise RuntimeError("Remote pyproject missing version")
    remote_version = remote_match.group("version")

    if remote_version != local_version:
        raise RuntimeError(
            f"Remote version {remote_version} differs from local {local_version}; sync before bumping."
        )

    for test_cmd in [args.tests]:
        print(f"Running tests: {' '.join(test_cmd)}")
        run_command(test_cmd)

    new_version = bump_patch_version(local_version)
    print(f"Bumping version: {local_version} -> {new_version}")
    set_version_in_pyproject(new_version)

    print("Rebuilding frontend assets...")
    run_command(["python3", "scripts/build_frontend.py"])

    print("Staging updated artifacts...")
    run_command(["git", "add", "pyproject.toml", "actifix-frontend/index.html", "actifix-frontend/app.js", "scripts/do_af_local_automation.py", "docs/DEVELOPMENT.md", "docs/FRAMEWORK_OVERVIEW.md", "docs/INDEX.md"])

    commit_msg = args.commit_msg or f"chore(do_af): automation ({args.ticket})"
    print(f"Committing: {commit_msg}")
    run_command(["git", "commit", "-m", commit_msg])

    print("Pushing to develop...")
    run_command(["git", "push", "origin", "develop"])

    print("Automation completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())