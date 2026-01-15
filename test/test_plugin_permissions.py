#!/usr/bin/env python3
"""
Tests for plugin permission system.

Verifies that:
1. Permissions are correctly defined and categorized
2. Plugins can request permissions
3. Permissions can be approved/revoked
4. Permission checks work correctly
5. Dangerous permissions are flagged
6. Permissions are persisted
"""

import os
import json
import tempfile

import pytest

from actifix.plugins.permissions import (
    Permission,
    PermissionLevel,
    PermissionRegistry,
    PermissionDeniedError,
    PluginPermissionConfig,
    PermissionManager,
    get_permission_manager,
    reset_permission_manager,
)


class TestPermissionDefinitions:
    """Test permission definitions."""

    def test_permission_creation(self):
        """Verify permission can be created."""
        perm = Permission(
            name="test_perm",
            description="A test permission",
            level=PermissionLevel.LOW
        )
        assert perm.name == "test_perm"
        assert perm.level == PermissionLevel.LOW

    def test_permission_levels(self):
        """Verify all permission levels exist."""
        assert PermissionLevel.CRITICAL
        assert PermissionLevel.HIGH
        assert PermissionLevel.MEDIUM
        assert PermissionLevel.LOW

    def test_permission_registry_populated(self):
        """Verify permission registry has all permissions."""
        assert len(PermissionRegistry.ALL_PERMISSIONS) > 0
        assert PermissionRegistry.FS_READ in PermissionRegistry.ALL_PERMISSIONS
        assert PermissionRegistry.SYS_EXEC in PermissionRegistry.ALL_PERMISSIONS


class TestPermissionCategories:
    """Test permission categorization."""

    def test_filesystem_permissions(self):
        """Verify filesystem permissions are defined."""
        fs_perms = {
            PermissionRegistry.FS_READ,
            PermissionRegistry.FS_WRITE,
            PermissionRegistry.FS_DELETE,
            PermissionRegistry.FS_EXECUTE,
        }
        assert fs_perms.issubset(PermissionRegistry.ALL_PERMISSIONS)

    def test_network_permissions(self):
        """Verify network permissions are defined."""
        net_perms = {
            PermissionRegistry.NETWORK_HTTP,
            PermissionRegistry.NETWORK_DNS,
            PermissionRegistry.NETWORK_SOCKET,
        }
        assert net_perms.issubset(PermissionRegistry.ALL_PERMISSIONS)

    def test_system_permissions(self):
        """Verify system permissions are defined."""
        sys_perms = {
            PermissionRegistry.SYS_EXEC,
            PermissionRegistry.SYS_ENV,
            PermissionRegistry.SYS_PROCESS,
        }
        assert sys_perms.issubset(PermissionRegistry.ALL_PERMISSIONS)

    def test_database_permissions(self):
        """Verify database permissions are defined."""
        db_perms = {
            PermissionRegistry.DB_READ,
            PermissionRegistry.DB_WRITE,
            PermissionRegistry.DB_ADMIN,
        }
        assert db_perms.issubset(PermissionRegistry.ALL_PERMISSIONS)


class TestDangerousPermissions:
    """Test dangerous permission identification."""

    def test_dangerous_permissions_flagged(self):
        """Verify dangerous permissions are identified."""
        dangerous = PermissionRegistry.DANGEROUS_PERMISSIONS
        assert PermissionRegistry.FS_DELETE in dangerous
        assert PermissionRegistry.SYS_EXEC in dangerous
        assert PermissionRegistry.DB_ADMIN in dangerous

    def test_safe_permissions_not_dangerous(self):
        """Verify safe permissions aren't marked dangerous."""
        safe = PermissionRegistry.DEFAULT_SAFE_PERMISSIONS
        for perm in safe:
            assert perm not in PermissionRegistry.DANGEROUS_PERMISSIONS

    def test_default_safe_permissions(self):
        """Verify default safe permissions are minimal."""
        safe = PermissionRegistry.DEFAULT_SAFE_PERMISSIONS
        assert PermissionRegistry.FS_READ in safe
        assert PermissionRegistry.LOGGING in safe
        assert PermissionRegistry.DB_READ in safe


class TestPluginPermissionConfig:
    """Test plugin permission configuration."""

    def test_create_config(self):
        """Verify plugin config can be created."""
        perms = {
            PermissionRegistry.FS_READ,
            PermissionRegistry.LOGGING,
        }
        config = PluginPermissionConfig(
            plugin_name="test_plugin",
            permissions=perms,
            description="Test plugin"
        )
        assert config.plugin_name == "test_plugin"
        assert len(config.permissions) == 2

    def test_config_to_dict(self):
        """Verify config can be serialized."""
        perms = {PermissionRegistry.FS_READ}
        config = PluginPermissionConfig(
            plugin_name="test",
            permissions=perms
        )
        data = config.to_dict()
        assert data['plugin_name'] == "test"
        assert "fs_read" in data['permissions']

    def test_config_from_dict(self):
        """Verify config can be deserialized."""
        data = {
            'plugin_name': 'test',
            'permissions': ['fs_read', 'logging'],
            'description': 'Test plugin',
        }
        config = PluginPermissionConfig.from_dict(data)
        assert config.plugin_name == 'test'
        assert PermissionRegistry.FS_READ in config.permissions


class TestPermissionManager:
    """Test permission manager functionality."""

    def test_manager_creation(self):
        """Verify permission manager can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)
            assert manager is not None
            assert len(manager.permissions) == 0

    def test_register_plugin(self):
        """Verify plugin can be registered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            perms = {PermissionRegistry.FS_READ, PermissionRegistry.LOGGING}
            manager.register_plugin("my_plugin", perms)

            assert "my_plugin" in manager.permissions
            assert manager.permissions["my_plugin"].permissions == perms

    def test_approve_permission(self):
        """Verify permission can be approved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            manager.register_plugin("my_plugin", set())
            manager.approve_permission("my_plugin", PermissionRegistry.FS_WRITE)

            assert PermissionRegistry.FS_WRITE in manager.permissions["my_plugin"].permissions

    def test_revoke_permission(self):
        """Verify permission can be revoked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            perms = {PermissionRegistry.FS_READ}
            manager.register_plugin("my_plugin", perms)
            manager.revoke_permission("my_plugin", PermissionRegistry.FS_READ)

            assert PermissionRegistry.FS_READ not in manager.permissions["my_plugin"].permissions


class TestPermissionChecks:
    """Test permission checking."""

    def test_check_permission_succeeds(self):
        """Verify permission check succeeds when permission granted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            perms = {PermissionRegistry.FS_READ}
            manager.register_plugin("my_plugin", perms)
            manager.check_permission("my_plugin", PermissionRegistry.FS_READ)
            # Should not raise

    def test_check_permission_fails(self):
        """Verify permission check fails when permission denied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            manager.register_plugin("my_plugin", set())

            with pytest.raises(PermissionDeniedError):
                manager.check_permission("my_plugin", PermissionRegistry.FS_READ)

    def test_has_permission_method(self):
        """Verify has_permission returns boolean."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            perms = {PermissionRegistry.FS_READ}
            manager.register_plugin("my_plugin", perms)

            assert manager.has_permission("my_plugin", PermissionRegistry.FS_READ) is True
            assert manager.has_permission("my_plugin", PermissionRegistry.FS_WRITE) is False

    def test_permission_denied_error(self):
        """Verify error message is informative."""
        with pytest.raises(PermissionDeniedError) as exc_info:
            manager = PermissionManager()
            manager.check_permission("unknown", PermissionRegistry.FS_READ)

        error = exc_info.value
        assert "unknown" in str(error)
        assert "fs_read" in str(error)


class TestPermissionPersistence:
    """Test permission persistence."""

    def test_permissions_saved_to_file(self):
        """Verify permissions are saved to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"

            # Create manager and register plugin
            manager1 = PermissionManager(config_file=config_file)
            perms = {PermissionRegistry.FS_READ, PermissionRegistry.LOGGING}
            manager1.register_plugin("my_plugin", perms)

            # Create new manager from same file
            manager2 = PermissionManager(config_file=config_file)

            # Should have the same permissions
            assert "my_plugin" in manager2.permissions
            assert manager2.permissions["my_plugin"].permissions == perms

    def test_invalid_config_file_handled(self):
        """Verify invalid config file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/bad.json"

            # Create invalid JSON file
            with open(config_file, 'w') as f:
                f.write("{invalid json")

            # Should not raise, just start with empty permissions
            manager = PermissionManager(config_file=config_file)
            assert len(manager.permissions) == 0


class TestGlobalPermissionManager:
    """Test global permission manager instance."""

    def test_get_manager_singleton(self):
        """Verify get_permission_manager returns singleton."""
        reset_permission_manager()
        manager1 = get_permission_manager()
        manager2 = get_permission_manager()
        assert manager1 is manager2

    def test_reset_manager(self):
        """Verify reset_permission_manager clears instance."""
        manager1 = get_permission_manager()
        reset_permission_manager()
        manager2 = get_permission_manager()
        assert manager1 is not manager2


class TestGetRequiredApprovals:
    """Test getting required approvals for dangerous permissions."""

    def test_dangerous_permissions_identified(self):
        """Verify dangerous permissions are identified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/perms.json"
            manager = PermissionManager(config_file=config_file)

            perms = {
                PermissionRegistry.FS_READ,
                PermissionRegistry.FS_DELETE,
                PermissionRegistry.SYS_EXEC,
            }
            manager.register_plugin("risky_plugin", perms)

            required = manager.get_required_approvals("risky_plugin")
            assert PermissionRegistry.FS_DELETE in required
            assert PermissionRegistry.SYS_EXEC in required
            assert PermissionRegistry.FS_READ not in required


class TestPermissionEquality:
    """Test permission equality and hashing."""

    def test_permission_equality(self):
        """Verify permissions can be compared."""
        perm1 = PermissionRegistry.FS_READ
        perm2 = PermissionRegistry.FS_READ
        assert perm1 == perm2

    def test_permission_hashing(self):
        """Verify permissions can be used in sets."""
        perms = {
            PermissionRegistry.FS_READ,
            PermissionRegistry.FS_READ,  # Duplicate
            PermissionRegistry.LOGGING,
        }
        assert len(perms) == 2  # Deduplication works


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
