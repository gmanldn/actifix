#!/usr/bin/env python3
"""
Root folder structure validation tests.

Ensures the project root remains clean with only allowed files.
Uses actifix to record violations.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Allowed files in project root (non-hidden)
ALLOWED_ROOT_FILES = {
    # Core project files
    "pyproject.toml",
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "CHANGELOG.md",
    # User-requested root scripts
    "start.py",
    "start_50_tasks.py",
    "test.py",
    "bounce.py",
}

# Allowed directories in project root (non-hidden)
ALLOWED_ROOT_DIRS = {
    "src",           # Source code
    "test",          # Tests
    "docs",          # Documentation
    "actifix",       # Actifix data directory
    "actifix-frontend",  # Frontend
    "logs",          # Log files
    "data",          # Data files
    "test_logs",     # Structured test logs
}

# Hidden items are always allowed (e.g., .git, .venv, .actifix)
# Generated files that are acceptable
ALLOWED_GENERATED = {
    ".coverage",
    ".DS_Store",
}


class TestRootFolderStructure:
    """Validate root folder contains only allowed items."""

    def test_no_unexpected_files_in_root(self):
        """Root should only contain allowed files."""
        unexpected = []

        for item in ROOT.iterdir():
            name = item.name

            # Skip hidden files/dirs
            if name.startswith("."):
                continue

            # Check files
            if item.is_file():
                if name not in ALLOWED_ROOT_FILES:
                    unexpected.append(f"file: {name}")

        if unexpected:
            # Record with actifix if available
            try:
                from actifix.raise_af import record_error
                record_error(
                    message=f"Unexpected files in root: {unexpected}",
                    source="test/test_root_structure.py",
                    error_type="StructureViolation",
                )
            except ImportError:
                pass

            pytest.fail(
                f"Unexpected files in project root: {unexpected}\n"
                f"Allowed files: {sorted(ALLOWED_ROOT_FILES)}\n"
                f"Keep root lean—move docs to docs/ and code into src/"
            )

    def test_no_unexpected_directories_in_root(self):
        """Root should only contain allowed directories."""
        unexpected = []

        for item in ROOT.iterdir():
            name = item.name

            # Skip hidden dirs
            if name.startswith("."):
                continue

            # Check directories
            if item.is_dir():
                if name not in ALLOWED_ROOT_DIRS and name != "__pycache__":
                    unexpected.append(f"dir: {name}")

        if unexpected:
            try:
                from actifix.raise_af import record_error
                record_error(
                    message=f"Unexpected directories in root: {unexpected}",
                    source="test/test_root_structure.py",
                    error_type="StructureViolation",
                )
            except ImportError:
                pass

            pytest.fail(
                f"Unexpected directories in project root: {unexpected}\n"
                f"Allowed directories: {sorted(ALLOWED_ROOT_DIRS)}"
            )

    def test_docs_in_docs_folder(self):
        """Documentation should be in docs/ not root."""
        misplaced = []
        doc_patterns = ["QUICK", "INSTALL", "DEVELOP", "GUIDE", "TUTORIAL"]

        for item in ROOT.iterdir():
            if item.is_file() and item.suffix == ".md":
                name = item.name
                # Skip allowed root docs
                if name in ALLOWED_ROOT_FILES:
                    continue
                # Check for doc patterns
                for pattern in doc_patterns:
                    if pattern in name.upper():
                        misplaced.append(name)
                        break

        if misplaced:
            try:
                from actifix.raise_af import record_error
                record_error(
                    message=f"Docs should be in docs/: {misplaced}",
                    source="test/test_root_structure.py",
                    error_type="StructureViolation",
                )
            except ImportError:
                pass

            pytest.fail(
                f"Documentation found in root that should be in docs/: {misplaced}"
            )

    def test_architecture_docs_location(self):
        """Architecture docs should be in docs/architecture/."""
        arch_dir = ROOT / "docs" / "architecture"
        assert arch_dir.exists(), "docs/architecture/ directory must exist"

        required_files = ["MODULES.md", "MAP.yaml", "DEPGRAPH.json"]
        missing = [f for f in required_files if not (arch_dir / f).exists()]

        if missing:
            pytest.fail(f"Missing architecture docs in docs/architecture/: {missing}")

        # Ensure old Arch/ doesn't exist
        old_arch = ROOT / "Arch"
        if old_arch.exists():
            try:
                from actifix.raise_af import record_error
                record_error(
                    message="Old Arch/ directory still exists, should be docs/architecture/",
                    source="test/test_root_structure.py",
                    error_type="StructureViolation",
                )
            except ImportError:
                pass

            pytest.fail("Old Arch/ directory exists - should be moved to docs/architecture/")


class TestFolderPurpose:
    """Validate each folder contains appropriate content."""

    def test_scripts_directory_absent(self):
        """Legacy scripts/ directory should not return."""
        scripts_dir = ROOT / "scripts"
        if scripts_dir.exists():
            try:
                from actifix.raise_af import record_error
                record_error(
                    message="Legacy scripts/ directory exists but should be removed",
                    source="test/test_root_structure.py",
                    error_type="StructureViolation",
                )
            except ImportError:
                pass

            pytest.fail("Legacy scripts/ directory detected; remove deprecated scripts")

    def test_docs_contains_markdown(self):
        """docs/ should primarily contain markdown and related files."""
        docs_dir = ROOT / "docs"
        if not docs_dir.exists():
            pytest.skip("docs/ directory does not exist")

        allowed_extensions = {".md", ".yaml", ".yml", ".json", ".txt", ".rst"}

        def check_dir(d: Path, violations: list):
            for item in d.iterdir():
                if item.is_dir():
                    check_dir(item, violations)
                elif item.is_file():
                    if item.suffix.lower() not in allowed_extensions and not item.name.startswith("."):
                        violations.append(str(item.relative_to(docs_dir)))

        violations = []
        check_dir(docs_dir, violations)

        if violations:
            pytest.fail(f"Non-documentation files in docs/: {violations}")
