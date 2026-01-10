#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State paths management for Actifix.

Manages state directories and file paths for the Actifix system,
ensuring consistent storage locations across different environments.

Version: 2.0.0 (Generic)
"""

import os
from pathlib import Path


def get_actifix_state_dir() -> Path:
    """
    Get the Actifix state directory for temporary files and queues.
    
    Uses environment variable ACTIFIX_STATE_DIR if set,
    otherwise uses a .actifix directory in the project root.
    
    Returns:
        Path to the state directory
    """
    # Check for environment override
    env_state_dir = os.getenv("ACTIFIX_STATE_DIR")
    if env_state_dir:
        state_dir = Path(env_state_dir)
    else:
        # Default to .actifix in project root
        project_root = Path.cwd()
        state_dir = project_root / ".actifix"
    
    # Ensure directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    return state_dir


def get_actifix_data_dir() -> Path:
    """
    Get the main Actifix data directory.
    
    This is where ACTIFIX.md, ACTIFIX-LIST.md, etc. are stored.
    
    Returns:
        Path to the data directory
    """
    # Check for environment override
    env_data_dir = os.getenv("ACTIFIX_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    
    # Default to actifix/ in project root
    project_root = Path.cwd()
    return project_root / "actifix"


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root
    """
    return Path.cwd()


def get_logs_dir() -> Path:
    """
    Get the logs directory.
    
    Returns:
        Path to the logs directory
    """
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
