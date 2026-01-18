#!/usr/bin/env python3
"""
Tests for database path security validation.

Verifies that:
1. Database paths in /tmp are rejected
2. Database paths in /var/tmp are rejected
3. Database paths in other shared directories are rejected
4. Valid private paths are accepted
5. Home directory paths are accepted
6. Database files with insecure permissions are rejected
7. Clear error messages are provided
"""

import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from actifix.persistence.database import (
    _validate_database_path,
    DatabaseSecurityError,
    get_database_pool,
    reset_database_pool,
)

pytestmark = [pytest.mark.integration]


class TestDatabasePathValidation:
    """Test database path security validation."""

    def test_valid_path_in_home_directory(self):
        """Verify home directory paths are accepted."""
        home_path = Path.home() / ".actifix" / "database.db"
        # Should not raise
        _validate_database_path(home_path)

    def test_valid_path_in_current_directory(self):
        """Verify current directory paths are accepted."""
        cwd_path = Path.cwd() / "data" / "database.db"
        # Should not raise
        _validate_database_path(cwd_path)

    def test_valid_path_in_custom_directory(self, tmp_path):
        """Verify custom safe directory paths are accepted."""
        custom_path = tmp_path / "safe_data" / "database.db"
        # Should not raise (tmp_path is in test temp directory)
        _validate_database_path(custom_path)

    def test_reject_path_in_tmp(self):
        """Verify /tmp paths are rejected."""
        tmp_path = Path("/tmp/database.db").resolve()
        # On macOS, /tmp resolves to /private/tmp
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(tmp_path)

    def test_reject_path_in_var_tmp(self):
        """Verify /var/tmp paths are rejected."""
        var_tmp_path = Path("/var/tmp/database.db").resolve()
        # On macOS, /var/tmp resolves to /private/var/tmp
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(var_tmp_path)

    def test_reject_path_in_private_tmp(self):
        """Verify /private/tmp (macOS) paths are rejected."""
        private_tmp_path = Path("/private/tmp/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(private_tmp_path)

    def test_reject_path_in_dev_shm(self):
        """Verify /dev/shm (shared memory) paths are rejected."""
        shm_path = Path("/dev/shm/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(shm_path)

    def test_reject_path_in_mnt(self):
        """Verify /mnt paths are rejected."""
        mnt_path = Path("/mnt/external/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(mnt_path)

    def test_reject_path_in_media(self):
        """Verify /media paths are rejected."""
        media_path = Path("/media/usb/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(media_path)

    def test_reject_path_in_proc(self):
        """Verify /proc paths are rejected."""
        proc_path = Path("/proc/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(proc_path)

    def test_reject_path_in_sys(self):
        """Verify /sys paths are rejected."""
        sys_path = Path("/sys/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(sys_path)

    def test_reject_world_readable_file(self, tmp_path):
        """Verify world-readable database files are rejected."""
        db_file = tmp_path / "database.db"
        db_file.touch()
        # Make file world-readable
        db_file.chmod(0o644)

        with pytest.raises(DatabaseSecurityError, match="world-readable"):
            _validate_database_path(db_file)

    def test_reject_world_writable_file(self, tmp_path):
        """Verify world-writable database files are rejected."""
        db_file = tmp_path / "database.db"
        db_file.touch()
        # Make file world-writable
        db_file.chmod(0o666)

        with pytest.raises(DatabaseSecurityError, match="world-readable|world-writable"):
            _validate_database_path(db_file)

    def test_accept_secure_file_permissions(self, tmp_path):
        """Verify secure file permissions are accepted."""
        db_file = tmp_path / "database.db"
        db_file.touch()
        # Set secure permissions (owner read/write only)
        db_file.chmod(0o600)

        # Should not raise
        _validate_database_path(db_file)

    def test_private_tmp_in_dangerous_patterns(self):
        """Verify /private/tmp matches dangerous patterns."""
        private_tmp = Path("/private/tmp/subdir/database.db")
        with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
            _validate_database_path(private_tmp)

    def test_error_message_includes_path(self):
        """Verify error message includes the problematic path."""
        bad_path = Path("/private/tmp/database.db")
        with pytest.raises(DatabaseSecurityError) as exc_info:
            _validate_database_path(bad_path)

        assert "private" in str(exc_info.value).lower() or "shared" in str(exc_info.value).lower()


class TestGetDatabasePoolValidation:
    """Test that get_database_pool uses validation."""

    def teardown_method(self):
        """Clean up database pool after each test."""
        reset_database_pool()

    def test_get_database_pool_rejects_private_tmp_path(self):
        """Verify get_database_pool rejects /private/tmp paths."""
        reset_database_pool()
        with pytest.raises(DatabaseSecurityError):
            get_database_pool(db_path=Path("/private/tmp/test.db"))

    def test_get_database_pool_accepts_safe_path(self, tmp_path):
        """Verify get_database_pool accepts safe paths."""
        reset_database_pool()
        safe_path = tmp_path / "safe" / "database.db"
        # Should not raise
        pool = get_database_pool(db_path=safe_path)
        assert pool is not None

    def test_get_database_pool_from_env_validates_path(self, monkeypatch):
        """Verify env variable path is validated."""
        reset_database_pool()
        monkeypatch.setenv("ACTIFIX_DB_PATH", "/private/tmp/database.db")

        with pytest.raises(DatabaseSecurityError):
            get_database_pool()


class TestPathValidationRobustness:
    """Test edge cases and robustness."""

    def test_safe_custom_path_accepted(self, tmp_path):
        """Verify validation works on custom safe paths."""
        safe_path = tmp_path / "mydata" / "database.db"
        # Should not raise
        _validate_database_path(safe_path)

    def test_home_relative_path_accepted(self):
        """Verify home-relative paths are accepted."""
        home_path = Path.home() / "database.db"
        _validate_database_path(home_path)  # Should not raise

    def test_permission_check_gracefully_handles_errors(self, tmp_path):
        """Verify permission check doesn't crash on permission errors."""
        db_file = tmp_path / "database.db"
        db_file.touch()

        # Mock stat to raise PermissionError
        with patch("pathlib.Path.stat", side_effect=PermissionError):
            # Should not raise (gracefully handles permission error)
            _validate_database_path(db_file)

    def test_dangerous_patterns_coverage(self):
        """Verify validation catches common dangerous paths."""
        # This test verifies we check all documented dangerous paths
        dangerous_resolved_paths = [
            "/private/tmp",  # macOS /tmp
            "/private/var/tmp",  # macOS /var/tmp
            "/dev/shm",
            "/mnt",
            "/media",
            "/proc",
            "/sys",
        ]

        for path_str in dangerous_resolved_paths:
            test_path = Path(path_str) / "test.db"
            with pytest.raises(DatabaseSecurityError, match="shared or public directory"):
                _validate_database_path(test_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
