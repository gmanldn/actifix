#!/usr/bin/env python3
"""
Guardrail tests for legacy setup scripts.

Ensures no leftover setup.py bootstrap scripts remain now that the legacy
scripts/ folder has been removed.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def test_no_setup_scripts_present():
    """Legacy setup scripts should stay removed."""
    legacy_paths = [
        ROOT / "setup.py",
        ROOT / "scripts" / "setup.py",
    ]
    present = [str(p.relative_to(ROOT)) for p in legacy_paths if p.exists()]

    if present:
        try:
            from actifix.raise_af import record_error
            record_error(
                message=f"Legacy setup scripts should be removed: {present}",
                source="test/test_setup.py",
                error_type="StructureViolation",
            )
        except ImportError:
            pass

        pytest.fail(f"Legacy setup scripts detected: {present}")


def test_bootstrap_creates_ticket_db(tmp_path, monkeypatch):
    """Bootstrap should initialize the ticket database for new users."""
    db_path = tmp_path / "data" / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    from actifix.bootstrap import bootstrap
    from actifix.persistence.database import reset_database_pool

    try:
        bootstrap(project_root=tmp_path)
        assert db_path.exists()
    finally:
        reset_database_pool()
