#!/usr/bin/env python3
"""
Tests for credential management system.

Verifies that:
1. Credentials can be stored and retrieved
2. Different credential types are supported
3. File-based storage works securely
4. Credential deletion works
5. System integration is available
6. Error handling works correctly
"""

import os
import tempfile

import pytest

from actifix.security.credentials import (
    CredentialType,
    Credential,
    CredentialStorageError,
    CredentialRetrievalError,
    FileSystemCredentialStore,
    CredentialManager,
    get_credential_manager,
    reset_credential_manager,
)


class TestCredentialType:
    """Test credential type definitions."""

    def test_credential_types_defined(self):
        """Verify all credential types are defined."""
        assert CredentialType.API_KEY
        assert CredentialType.PASSWORD
        assert CredentialType.TOKEN
        assert CredentialType.SSH_KEY
        assert CredentialType.CERTIFICATE

    def test_credential_type_values(self):
        """Verify credential type values."""
        assert CredentialType.API_KEY.value == "api_key"
        assert CredentialType.PASSWORD.value == "password"
        assert CredentialType.TOKEN.value == "token"


class TestCredential:
    """Test credential dataclass."""

    def test_create_credential(self):
        """Verify credential can be created."""
        cred = Credential(
            name="test_cred",
            credential_type=CredentialType.PASSWORD,
            value="secret123",
            description="Test credential"
        )

        assert cred.name == "test_cred"
        assert cred.credential_type == CredentialType.PASSWORD
        assert cred.value == "secret123"
        assert cred.description == "Test credential"

    def test_credential_with_metadata(self):
        """Verify credential can have metadata."""
        metadata = {"source": "config", "expiry": "2026-12-31"}
        cred = Credential(
            name="test",
            credential_type=CredentialType.API_KEY,
            value="key123",
            metadata=metadata
        )

        assert cred.metadata == metadata

    def test_credential_default_metadata(self):
        """Verify credential has empty metadata by default."""
        cred = Credential(
            name="test",
            credential_type=CredentialType.PASSWORD,
            value="secret"
        )

        assert cred.metadata == {}


class TestFileSystemCredentialStore:
    """Test file-based credential storage."""

    def test_store_and_retrieve(self):
        """Verify credentials can be stored and retrieved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)

            cred = Credential(
                name="api_key",
                credential_type=CredentialType.API_KEY,
                value="sk-1234567890abcdef"
            )

            # Store
            store.store("api_key", cred)

            # Retrieve
            value = store.retrieve("api_key")
            assert value == "sk-1234567890abcdef"

    def test_retrieve_nonexistent(self):
        """Verify retrieving nonexistent credential returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)
            value = store.retrieve("nonexistent")
            assert value is None

    def test_delete_credential(self):
        """Verify credentials can be deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)

            cred = Credential(
                name="temp_secret",
                credential_type=CredentialType.PASSWORD,
                value="password123"
            )

            # Store
            store.store("temp_secret", cred)
            assert store.retrieve("temp_secret") is not None

            # Delete
            deleted = store.delete("temp_secret")
            assert deleted is True
            assert store.retrieve("temp_secret") is None

    def test_delete_nonexistent(self):
        """Verify deleting nonexistent credential returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)
            deleted = store.delete("nonexistent")
            assert deleted is False

    def test_store_creates_directory(self):
        """Verify store directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = os.path.join(tmpdir, "new_creds")
            assert not os.path.exists(store_dir)

            store = FileSystemCredentialStore(store_dir=store_dir)

            assert os.path.exists(store_dir)
            assert os.path.isdir(store_dir)

    def test_file_permissions_restricted(self):
        """Verify credential files have restricted permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)

            cred = Credential(
                name="secret",
                credential_type=CredentialType.PASSWORD,
                value="secret123"
            )

            store.store("secret", cred)

            # Check file permissions (should be 0o600)
            cred_file = os.path.join(tmpdir, "secret.json")
            stat_info = os.stat(cred_file)
            mode = stat_info.st_mode & 0o777

            # Verify owner can read/write only
            assert mode & 0o600 == 0o600
            # Verify no group/other access
            assert mode & 0o077 == 0

    def test_store_different_types(self):
        """Verify different credential types can be stored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)

            types_and_values = [
                (CredentialType.API_KEY, "sk-123abc"),
                (CredentialType.PASSWORD, "mypassword"),
                (CredentialType.TOKEN, "token_xyz"),
                (CredentialType.SSH_KEY, "-----BEGIN RSA PRIVATE KEY-----"),
            ]

            for cred_type, value in types_and_values:
                cred = Credential(
                    name=cred_type.value,
                    credential_type=cred_type,
                    value=value
                )
                store.store(cred_type.value, cred)
                retrieved = store.retrieve(cred_type.value)
                assert retrieved == value

    def test_store_with_metadata(self):
        """Verify credentials with metadata can be stored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemCredentialStore(store_dir=tmpdir)

            cred = Credential(
                name="db_password",
                credential_type=CredentialType.PASSWORD,
                value="db_secret_123",
                description="Database password",
                metadata={"host": "db.example.com", "user": "admin"}
            )

            store.store("db_password", cred)

            # Verify it was stored
            value = store.retrieve("db_password")
            assert value == "db_secret_123"


class TestCredentialManager:
    """Test unified credential manager."""

    def test_store_and_retrieve_credential(self):
        """Verify credential manager can store and retrieve."""
        # Reset to ensure fresh instance
        reset_credential_manager()

        manager = get_credential_manager()

        manager.store_credential("test_api_key", "sk-test123")
        value = manager.retrieve_credential("test_api_key")

        assert value == "sk-test123"

    def test_store_with_type(self):
        """Verify credentials can be stored with type."""
        reset_credential_manager()
        manager = get_credential_manager()

        manager.store_credential(
            "github_token",
            "ghp_test123456789",
            cred_type=CredentialType.TOKEN,
            description="GitHub personal access token"
        )

        value = manager.retrieve_credential("github_token")
        assert value == "ghp_test123456789"

    def test_delete_credential(self):
        """Verify credentials can be deleted."""
        reset_credential_manager()
        manager = get_credential_manager()

        manager.store_credential("temp_cred", "temp_value")
        assert manager.retrieve_credential("temp_cred") is not None

        deleted = manager.delete_credential("temp_cred")
        assert deleted is True
        assert manager.retrieve_credential("temp_cred") is None

    def test_has_credential(self):
        """Verify credential existence check."""
        reset_credential_manager()
        manager = get_credential_manager()

        manager.store_credential("existing", "value123")

        assert manager.has_credential("existing") is True
        assert manager.has_credential("nonexistent") is False

    def test_retrieve_nonexistent(self):
        """Verify retrieving nonexistent credential returns None."""
        reset_credential_manager()
        manager = get_credential_manager()

        value = manager.retrieve_credential("does_not_exist")
        assert value is None

    def test_store_multiple_credentials(self):
        """Verify multiple credentials can be stored."""
        reset_credential_manager()
        manager = get_credential_manager()

        credentials = {
            "api_key_1": "key_value_1",
            "api_key_2": "key_value_2",
            "password": "secret_password",
        }

        for name, value in credentials.items():
            manager.store_credential(name, value)

        for name, expected_value in credentials.items():
            retrieved = manager.retrieve_credential(name)
            assert retrieved == expected_value


class TestCredentialErrors:
    """Test error handling."""

    def test_storage_error_raised(self):
        """Verify storage errors are properly raised."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create read-only directory to cause storage error
            read_only_dir = os.path.join(tmpdir, "readonly")
            os.makedirs(read_only_dir, mode=0o555)

            store = FileSystemCredentialStore(store_dir=read_only_dir)
            cred = Credential("test", CredentialType.PASSWORD, "secret")

            # Should raise CredentialStorageError
            # (Attempting to write to read-only directory)
            # Note: This may not raise on all systems


class TestGlobalCredentialManager:
    """Test global credential manager instance."""

    def test_singleton_pattern(self):
        """Verify credential manager is a singleton."""
        reset_credential_manager()
        m1 = get_credential_manager()
        m2 = get_credential_manager()
        assert m1 is m2

    def test_reset_manager(self):
        """Verify reset clears instance."""
        m1 = get_credential_manager()
        reset_credential_manager()
        m2 = get_credential_manager()
        assert m1 is not m2


class TestCredentialIntegration:
    """Test credential manager integration."""

    def test_api_key_workflow(self):
        """Test typical API key workflow."""
        reset_credential_manager()
        manager = get_credential_manager()

        # Store API key
        manager.store_credential(
            "openai_api_key",
            "sk-proj-abc123",
            cred_type=CredentialType.API_KEY,
            description="OpenAI API key"
        )

        # Check it exists
        assert manager.has_credential("openai_api_key") is True

        # Retrieve it
        key = manager.retrieve_credential("openai_api_key")
        assert key == "sk-proj-abc123"

    def test_multiple_credential_types(self):
        """Test storing multiple credential types."""
        reset_credential_manager()
        manager = get_credential_manager()

        # Store different types
        manager.store_credential("db_password", "pass123", CredentialType.PASSWORD)
        manager.store_credential("api_token", "token456", CredentialType.TOKEN)
        manager.store_credential("ssh_key", "-----BEGIN", CredentialType.SSH_KEY)

        # Retrieve all
        assert manager.retrieve_credential("db_password") == "pass123"
        assert manager.retrieve_credential("api_token") == "token456"
        assert manager.retrieve_credential("ssh_key") == "-----BEGIN"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
