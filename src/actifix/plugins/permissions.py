#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plugin Permission Model - Restrict plugin system access.

Implements a capability-based permission system where plugins
must explicitly declare and be granted permissions for:
- File system access (read, write, delete)
- Network access (HTTP, DNS)
- System command execution
- Environment variable access
- Database access
- Process management

Version: 1.0.0
"""

import os
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Set, Optional, List
from pathlib import Path


class PermissionLevel(Enum):
    """Permission severity levels."""
    CRITICAL = "critical"    # System access, arbitrary code execution
    HIGH = "high"            # File access, network, process management
    MEDIUM = "medium"        # Limited file access, environment variables
    LOW = "low"              # Read-only operations


@dataclass
class Permission:
    """Single permission that a plugin can request."""

    name: str                 # e.g., "fs_read", "network_http"
    description: str          # Human-readable description
    level: PermissionLevel    # Severity level
    resource: Optional[str] = None  # Specific resource (e.g., "/tmp" for fs operations)

    def __hash__(self):
        return hash((self.name, self.resource))

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return self.name == other.name and self.resource == other.resource


class PermissionRegistry:
    """Registry of all available permissions."""

    # File system permissions
    FS_READ = Permission(
        name="fs_read",
        description="Read files from filesystem",
        level=PermissionLevel.MEDIUM
    )
    FS_WRITE = Permission(
        name="fs_write",
        description="Write/modify files on filesystem",
        level=PermissionLevel.HIGH
    )
    FS_DELETE = Permission(
        name="fs_delete",
        description="Delete files from filesystem",
        level=PermissionLevel.CRITICAL
    )
    FS_EXECUTE = Permission(
        name="fs_execute",
        description="Execute files (scripts, binaries)",
        level=PermissionLevel.CRITICAL
    )

    # Network permissions
    NETWORK_HTTP = Permission(
        name="network_http",
        description="Make HTTP/HTTPS requests",
        level=PermissionLevel.HIGH
    )
    NETWORK_DNS = Permission(
        name="network_dns",
        description="Perform DNS lookups",
        level=PermissionLevel.MEDIUM
    )
    NETWORK_SOCKET = Permission(
        name="network_socket",
        description="Create raw network sockets",
        level=PermissionLevel.CRITICAL
    )

    # System permissions
    SYS_EXEC = Permission(
        name="sys_exec",
        description="Execute system commands",
        level=PermissionLevel.CRITICAL
    )
    SYS_ENV = Permission(
        name="sys_env",
        description="Read environment variables",
        level=PermissionLevel.MEDIUM
    )
    SYS_PROCESS = Permission(
        name="sys_process",
        description="Manage processes (spawn, kill, etc)",
        level=PermissionLevel.CRITICAL
    )

    # Database permissions
    DB_READ = Permission(
        name="db_read",
        description="Read from database",
        level=PermissionLevel.MEDIUM
    )
    DB_WRITE = Permission(
        name="db_write",
        description="Write to database",
        level=PermissionLevel.HIGH
    )
    DB_ADMIN = Permission(
        name="db_admin",
        description="Administer database (schema, users)",
        level=PermissionLevel.CRITICAL
    )

    # Logging permissions
    LOGGING = Permission(
        name="logging",
        description="Write to application logs",
        level=PermissionLevel.LOW
    )

    # Plugin management permissions
    PLUGIN_LOAD = Permission(
        name="plugin_load",
        description="Load other plugins",
        level=PermissionLevel.HIGH
    )
    PLUGIN_UNLOAD = Permission(
        name="plugin_unload",
        description="Unload other plugins",
        level=PermissionLevel.HIGH
    )

    # All available permissions
    ALL_PERMISSIONS = {
        FS_READ, FS_WRITE, FS_DELETE, FS_EXECUTE,
        NETWORK_HTTP, NETWORK_DNS, NETWORK_SOCKET,
        SYS_EXEC, SYS_ENV, SYS_PROCESS,
        DB_READ, DB_WRITE, DB_ADMIN,
        LOGGING,
        PLUGIN_LOAD, PLUGIN_UNLOAD,
    }

    # Default safe permissions (minimum needed for basic operation)
    DEFAULT_SAFE_PERMISSIONS = {
        FS_READ,
        LOGGING,
        DB_READ,
    }

    # Dangerous permissions that require explicit approval
    DANGEROUS_PERMISSIONS = {
        FS_DELETE, FS_EXECUTE,
        NETWORK_SOCKET,
        SYS_EXEC, SYS_PROCESS,
        DB_ADMIN,
        PLUGIN_LOAD, PLUGIN_UNLOAD,
    }


class PermissionDeniedError(PermissionError):
    """Raised when a plugin lacks required permission."""

    def __init__(self, plugin_name: str, permission: Permission):
        self.plugin_name = plugin_name
        self.permission = permission
        super().__init__(
            f"Plugin '{plugin_name}' lacks permission: {permission.name} "
            f"({permission.description})"
        )


@dataclass
class PluginPermissionConfig:
    """Permission configuration for a single plugin."""

    plugin_name: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'plugin_name': self.plugin_name,
            'permissions': [p.name for p in self.permissions],
            'description': self.description,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PluginPermissionConfig':
        """Reconstruct from dictionary."""
        permissions = set()
        for perm_name in data.get('permissions', []):
            # Find permission by name
            for perm in PermissionRegistry.ALL_PERMISSIONS:
                if perm.name == perm_name:
                    permissions.add(perm)
                    break

        return cls(
            plugin_name=data['plugin_name'],
            permissions=permissions,
            description=data.get('description', ''),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
        )


class PermissionManager:
    """Manages plugin permissions and enforces access control."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize permission manager.

        Args:
            config_file: Path to JSON file with permission configs
        """
        self.config_file = config_file or self._get_default_config_file()
        self.permissions: Dict[str, PluginPermissionConfig] = {}
        self._load_config()

    def _get_default_config_file(self) -> str:
        """Get default config file path."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'plugin_permissions.json')

    def _load_config(self) -> None:
        """Load permissions from config file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for plugin_data in data.get('plugins', []):
                        config = PluginPermissionConfig.from_dict(plugin_data)
                        self.permissions[config.plugin_name] = config
        except (json.JSONDecodeError, IOError):
            # Start with empty permissions if file doesn't exist or is invalid
            pass

    def _save_config(self) -> None:
        """Save permissions to config file."""
        try:
            config_data = {
                'plugins': [
                    config.to_dict()
                    for config in self.permissions.values()
                ]
            }

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except IOError:
            # Failure to persist shouldn't break operation
            pass

    def register_plugin(
        self,
        plugin_name: str,
        requested_permissions: Set[Permission],
        description: str = ""
    ) -> None:
        """Register a plugin with its requested permissions.

        Args:
            plugin_name: Name of the plugin
            requested_permissions: Set of permissions the plugin needs
            description: Description of what the plugin does
        """
        config = PluginPermissionConfig(
            plugin_name=plugin_name,
            permissions=requested_permissions,
            description=description,
        )
        self.permissions[plugin_name] = config
        self._save_config()

    def approve_permission(
        self,
        plugin_name: str,
        permission: Permission,
        approved_by: str = "admin"
    ) -> None:
        """Approve a permission for a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to approve
            approved_by: User/system approving the permission
        """
        if plugin_name not in self.permissions:
            self.permissions[plugin_name] = PluginPermissionConfig(plugin_name)

        config = self.permissions[plugin_name]
        config.permissions.add(permission)
        config.approved_by = approved_by

        from datetime import datetime, timezone
        config.approved_at = datetime.now(timezone.utc).isoformat()

        self._save_config()

    def revoke_permission(self, plugin_name: str, permission: Permission) -> None:
        """Revoke a permission from a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to revoke
        """
        if plugin_name in self.permissions:
            self.permissions[plugin_name].permissions.discard(permission)
            self._save_config()

    def check_permission(self, plugin_name: str, permission: Permission) -> None:
        """Check if plugin has required permission.

        Args:
            plugin_name: Name of the plugin
            permission: Required permission

        Raises:
            PermissionDeniedError: If plugin lacks permission
        """
        if plugin_name not in self.permissions:
            raise PermissionDeniedError(plugin_name, permission)

        config = self.permissions[plugin_name]
        if permission not in config.permissions:
            raise PermissionDeniedError(plugin_name, permission)

    def has_permission(self, plugin_name: str, permission: Permission) -> bool:
        """Check if plugin has permission without raising error.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to check

        Returns:
            True if plugin has permission, False otherwise
        """
        try:
            self.check_permission(plugin_name, permission)
            return True
        except PermissionDeniedError:
            return False

    def get_plugin_permissions(self, plugin_name: str) -> Set[Permission]:
        """Get all permissions for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Set of permissions the plugin has
        """
        if plugin_name in self.permissions:
            return self.permissions[plugin_name].permissions.copy()
        return set()

    def get_required_approvals(self, plugin_name: str) -> Set[Permission]:
        """Get dangerous permissions that require approval.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Set of dangerous permissions the plugin has
        """
        permissions = self.get_plugin_permissions(plugin_name)
        return permissions & PermissionRegistry.DANGEROUS_PERMISSIONS


# Global permission manager instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Get or create the global permission manager."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def reset_permission_manager() -> None:
    """Reset the global permission manager (for testing)."""
    global _permission_manager
    _permission_manager = None
