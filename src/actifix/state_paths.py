#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State paths management for Actifix.

Provides a single, deterministic source of truth for all Actifix file and
directory locations. Mirrors the Pokertool-style layout by ensuring the ticket
list, rollup, audit log, and test logs are always created together.

Version: 2.1.0 (Generic)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class ActifixPaths:
    """Resolved Actifix path configuration."""
    
    project_root: Path
    base_dir: Path
    state_dir: Path
    logs_dir: Path
    
    list_file: Path
    rollup_file: Path
    log_file: Path
    aflog_file: Path
    fallback_queue_file: Path
    
    quarantine_dir: Path
    test_logs_dir: Path
    
    @property
    def all_artifacts(self) -> List[Path]:
        """Return all core artifacts that must exist for health checks."""
        return [
            self.list_file,
            self.rollup_file,
            self.log_file,
            self.aflog_file,
        ]


def _resolve_project_root(project_root: Optional[Path] = None) -> Path:
    """Resolve the project root, honoring ACTIFIX_PROJECT_ROOT override."""
    return Path(
        project_root
        or os.environ.get("ACTIFIX_PROJECT_ROOT", Path.cwd())
    ).resolve()


def _build_paths(
    project_root: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
) -> ActifixPaths:
    """Construct an ActifixPaths instance from overrides and environment."""
    resolved_root = _resolve_project_root(project_root)
    
    resolved_base = (
        Path(base_dir)
        if base_dir is not None
        else Path(os.environ.get("ACTIFIX_DATA_DIR", resolved_root / "actifix")).resolve()
    )
    
    resolved_state = (
        Path(state_dir)
        if state_dir is not None
        else Path(os.environ.get("ACTIFIX_STATE_DIR", resolved_root / ".actifix")).resolve()
    )
    
    resolved_logs = (
        Path(logs_dir)
        if logs_dir is not None
        else Path(os.environ.get("ACTIFIX_LOGS_DIR", resolved_root / "logs")).resolve()
    )
    
    return ActifixPaths(
        project_root=resolved_root,
        base_dir=resolved_base,
        state_dir=resolved_state,
        logs_dir=resolved_logs,
        list_file=resolved_base / "ACTIFIX-LIST.md",
        rollup_file=resolved_base / "ACTIFIX.md",
        log_file=resolved_base / "ACTIFIX-LOG.md",
        aflog_file=resolved_base / "AFLog.txt",
        fallback_queue_file=resolved_state / "actifix_fallback_queue.json",
        quarantine_dir=resolved_state / "quarantine",
        test_logs_dir=resolved_state / "test_logs",
    )


def ensure_actifix_dirs(paths: ActifixPaths) -> None:
    """Create all required directories for the provided paths."""
    paths.base_dir.mkdir(parents=True, exist_ok=True)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.quarantine_dir.mkdir(parents=True, exist_ok=True)
    paths.test_logs_dir.mkdir(parents=True, exist_ok=True)


def init_actifix_files(paths: Optional[ActifixPaths] = None) -> ActifixPaths:
    """
    Ensure all Actifix directories and files exist with default content.
    
    Returns:
        ActifixPaths used for initialization.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    ensure_actifix_dirs(paths)
    
    if not paths.list_file.exists():
        paths.list_file.write_text(
            "# ACTIFIX Ticket List\n\n"
            "## Active Items\n\n"
            "_No active items_\n\n"
            "## Completed Items\n\n"
            "_No completed items_\n",
            encoding="utf-8",
        )
    
    if not paths.rollup_file.exists():
        paths.rollup_file.write_text(
            "# ACTIFIX Error Rollup\n\n"
            "Most recent issues will appear here.\n",
            encoding="utf-8",
        )
    
    if not paths.log_file.exists():
        paths.log_file.write_text("# ACTIFIX Log\n", encoding="utf-8")
    
    if not paths.aflog_file.exists():
        paths.aflog_file.write_text("", encoding="utf-8")
    
    return paths


def get_actifix_paths(
    project_root: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
) -> ActifixPaths:
    """
    Get the ActifixPaths instance for the current environment.
    
    Paths are re-evaluated on every call so environment overrides are honored.
    """
    return _build_paths(project_root, base_dir, state_dir, logs_dir)


def reset_actifix_paths() -> None:
    """Reset cached paths (useful for tests)."""
    # No-op retained for backward compatibility.
    return None


def get_actifix_state_dir() -> Path:
    """Shortcut to the Actifix state directory."""
    paths = get_actifix_paths()
    ensure_actifix_dirs(paths)
    return paths.state_dir


def get_actifix_data_dir() -> Path:
    """Shortcut to the Actifix data directory."""
    paths = get_actifix_paths()
    ensure_actifix_dirs(paths)
    return paths.base_dir


def get_project_root() -> Path:
    """Shortcut to the project root."""
    return get_actifix_paths().project_root


def get_logs_dir() -> Path:
    """Shortcut to the logs directory."""
    paths = get_actifix_paths()
    ensure_actifix_dirs(paths)
    return paths.logs_dir
