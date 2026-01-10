#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Storage Paths Configuration

Generic path configuration for storage systems.
Provides configurable paths for data, state, logs, and caches.

Version: 1.0.0 (Generic)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class StoragePaths:
    """
    Storage path configuration.
    
    Provides centralized path management for storage systems.
    All paths are created on initialization.
    """
    
    # Base directories
    project_root: Path
    data_dir: Path
    state_dir: Path
    
    # Optional directories
    logs_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    temp_dir: Optional[Path] = None
    backup_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Create directories on initialization."""
        self.project_root = Path(self.project_root)
        self.data_dir = Path(self.data_dir)
        self.state_dir = Path(self.state_dir)
        
        # Create required directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Create optional directories if specified
        if self.logs_dir:
            self.logs_dir = Path(self.logs_dir)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        if self.cache_dir:
            self.cache_dir = Path(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if self.temp_dir:
            self.temp_dir = Path(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        if self.backup_dir:
            self.backup_dir = Path(self.backup_dir)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_data_path(self, *parts: str) -> Path:
        """Get path within data directory."""
        return self.data_dir.joinpath(*parts)
    
    def get_state_path(self, *parts: str) -> Path:
        """Get path within state directory."""
        return self.state_dir.joinpath(*parts)
    
    def get_log_path(self, *parts: str) -> Path:
        """Get path within logs directory."""
        if not self.logs_dir:
            raise ValueError("Logs directory not configured")
        return self.logs_dir.joinpath(*parts)
    
    def get_cache_path(self, *parts: str) -> Path:
        """Get path within cache directory."""
        if not self.cache_dir:
            raise ValueError("Cache directory not configured")
        return self.cache_dir.joinpath(*parts)
    
    def get_temp_path(self, *parts: str) -> Path:
        """Get path within temp directory."""
        if not self.temp_dir:
            raise ValueError("Temp directory not configured")
        return self.temp_dir.joinpath(*parts)
    
    def get_backup_path(self, *parts: str) -> Path:
        """Get path within backup directory."""
        if not self.backup_dir:
            raise ValueError("Backup directory not configured")
        return self.backup_dir.joinpath(*parts)


def configure_storage_paths(
    project_root: Optional[Path] = None,
    data_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
    temp_dir: Optional[Path] = None,
    backup_dir: Optional[Path] = None,
    env_prefix: str = "STORAGE",
) -> StoragePaths:
    """
    Configure storage paths from parameters or environment variables.
    
    Environment variables (with default prefix "STORAGE"):
    - {prefix}_PROJECT_ROOT: Project root directory
    - {prefix}_DATA_DIR: Data directory
    - {prefix}_STATE_DIR: State directory
    - {prefix}_LOGS_DIR: Logs directory (optional)
    - {prefix}_CACHE_DIR: Cache directory (optional)
    - {prefix}_TEMP_DIR: Temp directory (optional)
    - {prefix}_BACKUP_DIR: Backup directory (optional)
    
    Args:
        project_root: Project root (default: cwd)
        data_dir: Data directory (default: {project_root}/data)
        state_dir: State directory (default: {project_root}/.state)
        logs_dir: Logs directory (optional)
        cache_dir: Cache directory (optional)
        temp_dir: Temp directory (optional)
        backup_dir: Backup directory (optional)
        env_prefix: Prefix for environment variables
        
    Returns:
        Configured StoragePaths
    """
    # Determine project root
    if project_root is None:
        project_root = Path(os.environ.get(
            f"{env_prefix}_PROJECT_ROOT",
            os.getcwd()
        ))
    project_root = Path(project_root).resolve()
    
    # Determine data directory
    if data_dir is None:
        data_dir = os.environ.get(
            f"{env_prefix}_DATA_DIR",
            str(project_root / "data")
        )
    
    # Determine state directory
    if state_dir is None:
        state_dir = os.environ.get(
            f"{env_prefix}_STATE_DIR",
            str(project_root / ".state")
        )
    
    # Optional directories
    if logs_dir is None:
        logs_dir_env = os.environ.get(f"{env_prefix}_LOGS_DIR")
        if logs_dir_env:
            logs_dir = logs_dir_env
    
    if cache_dir is None:
        cache_dir_env = os.environ.get(f"{env_prefix}_CACHE_DIR")
        if cache_dir_env:
            cache_dir = cache_dir_env
    
    if temp_dir is None:
        temp_dir_env = os.environ.get(f"{env_prefix}_TEMP_DIR")
        if temp_dir_env:
            temp_dir = temp_dir_env
    
    if backup_dir is None:
        backup_dir_env = os.environ.get(f"{env_prefix}_BACKUP_DIR")
        if backup_dir_env:
            backup_dir = backup_dir_env
    
    return StoragePaths(
        project_root=project_root,
        data_dir=Path(data_dir),
        state_dir=Path(state_dir),
        logs_dir=Path(logs_dir) if logs_dir else None,
        cache_dir=Path(cache_dir) if cache_dir else None,
        temp_dir=Path(temp_dir) if temp_dir else None,
        backup_dir=Path(backup_dir) if backup_dir else None,
    )


# Global paths instance
_storage_paths: Optional[StoragePaths] = None


def get_storage_paths() -> StoragePaths:
    """
    Get the global storage paths instance.
    
    Configures with defaults if not explicitly initialized.
    """
    global _storage_paths
    if _storage_paths is None:
        _storage_paths = configure_storage_paths()
    return _storage_paths


def set_storage_paths(paths: StoragePaths) -> None:
    """Set the global storage paths instance."""
    global _storage_paths
    _storage_paths = paths


def reset_storage_paths() -> None:
    """Reset the global storage paths to None."""
    global _storage_paths
    _storage_paths = None
