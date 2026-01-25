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

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

def get_staged_files():
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def _record_hook_error(message: str, source: str) -> None:
    try:
        sys.path.insert(0, str(SRC_ROOT))
        from actifix.raise_af import record_error, TicketPriority

        record_error(
            message=message,
            source=source,
            error_type="VersionGuardError",
            priority=TicketPriority.P2,
        )
    except Exception:
        return

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
        cmd = [sys.executable, "-m", "pytest", "test/", "-v", "--tb=short", "-x"]
        # Build pattern matching for module tests
        patterns = " or ".join([f"test_{m}" for m in modules])
        cmd.extend(["-k", patterns])
    else:
        print("📋 Critical files changed - running full test suite")
        cmd = [sys.executable, "test/test_runner.py"]

    result = subprocess.run(cmd, env=env)
    return result.returncode

def _read_version_from_pyproject(pyproject_path: Path) -> str | None:
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\\s*=\\s*\"([^\"]+)\"', content, re.MULTILINE)
    return match.group(1) if match else None


def _parse_version_tuple(version: str) -> tuple[int, int, int] | None:
    match = re.match(r"^(\\d+)\\.(\\d+)\\.(\\d+)$", version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _read_remote_version() -> str | None:
    fetch = subprocess.run(
        ["git", "fetch", "origin", "develop"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if fetch.returncode != 0:
        print(f"⚠️  Warning: git fetch failed: {fetch.stderr.strip()}")
    result = subprocess.run(
        ["git", "show", "origin/develop:pyproject.toml"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    match = re.search(r'^version\\s*=\\s*\"([^\"]+)\"', result.stdout, re.MULTILINE)
    return match.group(1) if match else None


def _write_version_to_pyproject(pyproject_path: Path, new_version: str) -> bool:
    try:
        sys.path.insert(0, str(SRC_ROOT))
        from actifix.log_utils import atomic_write
    except Exception as exc:
        print(f"✗ Failed to load atomic_write: {exc}")
        return False

    content = pyproject_path.read_text(encoding="utf-8")
    updated = re.sub(
        r'version\\s*=\\s*\"(\\d+)\\.(\\d+)\\.(\\d+)\"',
        f'version = "{new_version}"',
        content,
        count=1,
    )
    atomic_write(pyproject_path, updated)
    return True


def _sync_remote_version_guard(pyproject_path: Path) -> bool:
    local_version = _read_version_from_pyproject(pyproject_path)
    remote_version = _read_remote_version()
    if not local_version or not remote_version:
        print("✗ Unable to verify remote version; aborting commit.")
        _record_hook_error(
            "Unable to verify remote version during pre-commit guard.",
            "scripts/pre-commit-hook.py:_sync_remote_version_guard",
        )
        return False

    local_tuple = _parse_version_tuple(local_version)
    remote_tuple = _parse_version_tuple(remote_version)
    if not local_tuple or not remote_tuple:
        print("✗ Version parsing failed; aborting commit.")
        _record_hook_error(
            "Version parsing failed during pre-commit guard.",
            "scripts/pre-commit-hook.py:_sync_remote_version_guard",
        )
        return False

    if local_tuple >= remote_tuple:
        return True

    new_version = (remote_tuple[0], remote_tuple[1], remote_tuple[2] + 1)
    new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    print(
        "✗ Local version is behind origin/develop. "
        f"Updating to {new_version_str}."
    )
    if not _write_version_to_pyproject(pyproject_path, new_version_str):
        return False
    if not _run_frontend_sync():
        print("✗ Frontend sync failed after version bump")
        return False
    subprocess.run(["git", "add", str(pyproject_path)], cwd=str(REPO_ROOT))
    _stage_frontend_version_files()
    return True

def _read_asset_version(index_path: Path) -> str | None:
    content = index_path.read_text(encoding="utf-8")
    match = re.search(r'ACTIFIX_ASSET_VERSION\\s*=\\s*\"([^\"]+)\"', content)
    return match.group(1) if match else None

def _read_ui_version(app_path: Path) -> str | None:
    content = app_path.read_text(encoding="utf-8")
    # Support either quote style, allow whitespace, and avoid being overly strict.
    match = re.search(r"\\bconst\\s+UI_VERSION\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"]\\s*;", content)
    return match.group(1) if match else None


def _run_frontend_sync() -> bool:
    """Attempt to sync frontend version constants to pyproject.toml."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_frontend.py")],
        cwd=str(REPO_ROOT),
    )
    return result.returncode == 0


def _stage_frontend_version_files() -> None:
    """Stage the version-controlled frontend files that must match pyproject.toml."""
    paths = [
        REPO_ROOT / "actifix-frontend" / "index.html",
        REPO_ROOT / "actifix-frontend" / "app.js",
    ]
    existing = [str(p) for p in paths if p.exists()]
    if existing:
        subprocess.run(["git", "add", *existing], cwd=str(REPO_ROOT))


def scan_secrets_in_staged_files() -> bool:
    """Run the Actifix secrets scanner against staged files (abort commit on leaks)."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from actifix.security import scan_git_staged_files, format_scan_results

        matches = scan_git_staged_files()
        if matches:
            print("✗ Secrets detected in staged files!")
            print(format_scan_results(matches))
            return False
        print("✓ No secrets detected")
        return True
    except Exception as exc:
        # Don't silently allow potential leaks.
        print(f"✗ Secrets scan failed: {exc}")
        return False


def check_version_consistency() -> bool:
    """Ensure project versions are consistent before commit."""
    pyproject = REPO_ROOT / "pyproject.toml"
    frontend_index = REPO_ROOT / "actifix-frontend" / "index.html"
    frontend_app = REPO_ROOT / "actifix-frontend" / "app.js"

    if not pyproject.exists():
        return True

    if not _sync_remote_version_guard(pyproject):
        return False

    pyproject_version = _read_version_from_pyproject(pyproject)
    asset_version = _read_asset_version(frontend_index) if frontend_index.exists() else None
    ui_version = _read_ui_version(frontend_app) if frontend_app.exists() else None

    mismatches = []
    if not pyproject_version:
        mismatches.append("pyproject.toml version missing")
    if frontend_app.exists() and not ui_version:
        mismatches.append("actifix-frontend/app.js UI_VERSION missing")
    if asset_version and pyproject_version and asset_version != pyproject_version:
        mismatches.append(f"actifix-frontend/index.html ({asset_version}) != pyproject.toml ({pyproject_version})")
    if ui_version and pyproject_version and ui_version != pyproject_version:
        mismatches.append(f"actifix-frontend/app.js ({ui_version}) != pyproject.toml ({pyproject_version})")

    if mismatches:
        print("✗ Version mismatch detected:")
        for issue in mismatches:
            print(f"  - {issue}")
        print("→ Attempting automatic frontend version sync...")
        if not _run_frontend_sync():
            print("✗ Frontend sync failed")
            return False
        _stage_frontend_version_files()
        # Re-check after sync/staging.
        return check_version_consistency()

    print("✓ Version consistency check passed")
    return True


def check_no_binaries(staged_files):
    """Reject commits containing binary files to prevent merge conflicts in multi-agent workflows."""
    disallowed_suffixes = [
        '.db', '.db-shm', '.db-wal', '.png', '.jpg', '.jpeg', '.gif', '.bmp', 
        '.tiff', '.zip', '.tar.gz', '.exe', '.dll', '.so', '.dylib', '.pyc', '.pyd'
    ]
    for file_path in staged_files:
        suffix = Path(file_path).suffix.lower()
        if suffix in disallowed_suffixes:
            print(f"✗ Binary file staged: {file_path}")
            print("Rejecting commit containing binary files.")
            return False
    print("✓ No disallowed binary files staged")
    return True

def check_version_bumped_for_commit(staged_files) -> bool:
    """Enforce version bump policy: every commit must include a pyproject.toml bump.

    This keeps a single canonical version source (pyproject.toml) and guarantees
    the frontend cache-busting version changes whenever features change.
    """
    if not staged_files or staged_files == [""]:
        return True

    staged_set = set(staged_files)
    if "pyproject.toml" in staged_set:
        return True

    # If anything besides pyproject.toml is being committed, require a version bump.
    other_files = [p for p in staged_files if p and p != "pyproject.toml"]
    if other_files:
        print("✗ Version bump required: pyproject.toml is not staged.")
        print("  - Policy: increment pyproject.toml version after every commit")
        print("  - Fix: update pyproject.toml version and re-stage it (git add pyproject.toml)")
        return False
    return True

def main():
    """Main pre-commit hook logic."""
    staged_files = get_staged_files()

    if not staged_files or staged_files == [""]:
        print("✓ No staged files - skipping pre-commit tests")
        return 0

    print("→ Scanning for leaked secrets...")
    if not scan_secrets_in_staged_files():
        return 1

    if not check_version_bumped_for_commit(staged_files):
        return 1

    if not check_version_consistency():
        return 1

    if not check_no_binaries(staged_files):
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
