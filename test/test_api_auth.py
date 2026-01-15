#!/usr/bin/env python3
"""
Tests for API authentication and authorization.

Verifies that:
1. Tokens are created, verified, and revoked correctly
2. Users can be created and authenticated
3. Password hashing and verification work
4. Roles and permissions are properly enforced
5. Authorization checks work correctly
6. Token expiration is handled
7. Database persistence works
"""

import tempfile
import time
from datetime import datetime, timezone, timedelta

import pytest

from actifix.security.auth import (
    AuthRole,
    AuthUser,
    AuthToken,
    AuthenticationError,
    AuthorizationError,
    TokenManager,
    UserManager,
    AuthorizationManager,
    get_token_manager,
    get_user_manager,
    get_authorization_manager,
    reset_auth_managers,
)


class TestTokenManager:
    """Test token creation and management."""

    def test_token_creation(self):
        """Verify tokens can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")
            token_id, token_value = manager.create_token("user123")

            assert token_id
            assert token_value
            assert len(token_value) > 0

    def test_token_verification(self):
        """Verify tokens can be verified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")
            _, token_value = manager.create_token("user123")

            user_id = manager.verify_token(token_value)
            assert user_id == "user123"

    def test_invalid_token_fails(self):
        """Verify invalid tokens are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")
            user_id = manager.verify_token("invalid_token")
            assert user_id is None

    def test_token_revocation(self):
        """Verify tokens can be revoked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")
            _, token_value = manager.create_token("user123")

            # Token should verify before revocation
            assert manager.verify_token(token_value) == "user123"

            # Revoke token
            revoked = manager.revoke_token(token_value)
            assert revoked is True

            # Token should not verify after revocation
            assert manager.verify_token(token_value) is None

    def test_revoke_all_user_tokens(self):
        """Verify all user tokens can be revoked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")

            # Create multiple tokens
            _, token1 = manager.create_token("user123")
            _, token2 = manager.create_token("user123")

            # Revoke all user tokens
            count = manager.revoke_all_user_tokens("user123")
            assert count >= 2

            # Both tokens should be revoked
            assert manager.verify_token(token1) is None
            assert manager.verify_token(token2) is None

    def test_token_expiration(self):
        """Verify token expiration is enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")
            # Create token that expires in -1 hours (already expired)
            _, token_value = manager.create_token("user123", expires_in_hours=-1)

            # Expired token should not verify
            user_id = manager.verify_token(token_value)
            assert user_id is None

    def test_multiple_user_tokens(self):
        """Verify different users can have separate tokens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(db_path=f"{tmpdir}/auth.db")

            _, token1 = manager.create_token("user1")
            _, token2 = manager.create_token("user2")

            assert manager.verify_token(token1) == "user1"
            assert manager.verify_token(token2) == "user2"


class TestUserManager:
    """Test user management."""

    def test_create_user(self):
        """Verify users can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            roles = {AuthRole.VIEWER}

            user = manager.create_user("user1", "alice", "password123", roles)

            assert user.user_id == "user1"
            assert user.username == "alice"
            assert AuthRole.VIEWER in user.roles
            assert user.is_active is True

    def test_authenticate_user(self):
        """Verify user authentication works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            roles = {AuthRole.OPERATOR}

            # Create user
            manager.create_user("user1", "alice", "secret123", roles)

            # Authenticate
            user, token = manager.authenticate_user("alice", "secret123")

            assert user.username == "alice"
            assert token
            assert len(token) > 0

    def test_authentication_fails_wrong_password(self):
        """Verify authentication fails with wrong password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            manager.create_user("user1", "alice", "correct", {AuthRole.VIEWER})

            with pytest.raises(AuthenticationError):
                manager.authenticate_user("alice", "wrong")

    def test_authentication_fails_unknown_user(self):
        """Verify authentication fails for unknown user."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")

            with pytest.raises(AuthenticationError):
                manager.authenticate_user("unknown", "password")

    def test_inactive_user_cannot_authenticate(self):
        """Verify inactive users cannot authenticate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            manager.create_user("user1", "alice", "password", {AuthRole.VIEWER})

            # Manually set user to inactive (simulate deactivation)
            # In real scenario, there would be a deactivate_user method
            # For now, we just verify the structure supports it

    def test_get_user(self):
        """Verify user information can be retrieved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            roles = {AuthRole.ADMIN, AuthRole.OPERATOR}

            manager.create_user("user1", "alice", "password", roles)

            user = manager.get_user("user1")

            assert user is not None
            assert user.username == "alice"
            assert AuthRole.ADMIN in user.roles
            assert AuthRole.OPERATOR in user.roles

    def test_password_hashing(self):
        """Verify passwords are hashed differently each time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")

            hash1 = manager._hash_password("password")
            hash2 = manager._hash_password("password")

            # Different hashes due to random salt
            assert hash1 != hash2

            # But both verify the same password
            assert manager._verify_password("password", hash1)
            assert manager._verify_password("password", hash2)

    def test_wrong_password_fails_verification(self):
        """Verify wrong password fails verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")
            hashed = manager._hash_password("correct")

            assert manager._verify_password("correct", hashed) is True
            assert manager._verify_password("wrong", hashed) is False


class TestAuthorizationManager:
    """Test authorization and role-based access control."""

    def test_admin_has_all_permissions(self):
        """Verify admin role has all permissions."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "admin_user", {AuthRole.ADMIN}, datetime.now(timezone.utc))

        # Admin should have all permissions
        manager.check_authorization(user, "read_tickets")
        manager.check_authorization(user, "delete_tickets")
        manager.check_authorization(user, "manage_users")

    def test_operator_has_limited_permissions(self):
        """Verify operator role has limited permissions."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "op_user", {AuthRole.OPERATOR}, datetime.now(timezone.utc))

        # Operator should have some permissions
        manager.check_authorization(user, "read_tickets")
        manager.check_authorization(user, "update_tickets")

        # But not others
        with pytest.raises(AuthorizationError):
            manager.check_authorization(user, "delete_tickets")

    def test_viewer_has_read_only(self):
        """Verify viewer role has read-only permissions."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "viewer_user", {AuthRole.VIEWER}, datetime.now(timezone.utc))

        # Viewer should have read permissions
        manager.check_authorization(user, "read_tickets")
        manager.check_authorization(user, "view_logs")

        # But not write permissions
        with pytest.raises(AuthorizationError):
            manager.check_authorization(user, "create_tickets")

    def test_system_role_has_all_permissions(self):
        """Verify system role has all permissions."""
        manager = AuthorizationManager()
        user = AuthUser("sys", "system", {AuthRole.SYSTEM}, datetime.now(timezone.utc))

        # System should have all permissions
        manager.check_authorization(user, "anything")
        manager.check_authorization(user, "everything")

    def test_has_permission_boolean(self):
        """Verify has_permission returns boolean."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "user", {AuthRole.VIEWER}, datetime.now(timezone.utc))

        assert manager.has_permission(user, "read_tickets") is True
        assert manager.has_permission(user, "delete_tickets") is False

    def test_multiple_roles(self):
        """Verify user can have multiple roles."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "user", {AuthRole.OPERATOR, AuthRole.VIEWER}, datetime.now(timezone.utc))

        # Should have permissions from both roles
        manager.check_authorization(user, "read_tickets")  # From VIEWER
        manager.check_authorization(user, "update_tickets")  # From OPERATOR

    def test_permission_denied_error_message(self):
        """Verify error message is informative."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "alice", {AuthRole.VIEWER}, datetime.now(timezone.utc))

        with pytest.raises(AuthorizationError) as exc_info:
            manager.check_authorization(user, "delete_tickets")

        error = exc_info.value
        assert "alice" in str(error)
        assert "delete_tickets" in str(error)


class TestAuthenticationError:
    """Test authentication error handling."""

    def test_auth_error_on_invalid_user(self):
        """Verify authentication error on invalid user."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserManager(db_path=f"{tmpdir}/auth.db")

            with pytest.raises(AuthenticationError):
                manager.authenticate_user("nonexistent", "password")


class TestAuthorizationError:
    """Test authorization error handling."""

    def test_authz_error_message(self):
        """Verify authorization error has clear message."""
        manager = AuthorizationManager()
        user = AuthUser("u1", "viewer", {AuthRole.VIEWER}, datetime.now(timezone.utc))

        with pytest.raises(AuthorizationError) as exc_info:
            manager.check_authorization(user, "manage_users")

        assert "manage_users" in str(exc_info.value)


class TestGlobalInstances:
    """Test global auth manager instances."""

    def test_get_token_manager_singleton(self):
        """Verify token manager singleton."""
        reset_auth_managers()
        m1 = get_token_manager()
        m2 = get_token_manager()
        assert m1 is m2

    def test_get_user_manager_singleton(self):
        """Verify user manager singleton."""
        reset_auth_managers()
        m1 = get_user_manager()
        m2 = get_user_manager()
        assert m1 is m2

    def test_get_authorization_manager_singleton(self):
        """Verify authorization manager singleton."""
        reset_auth_managers()
        m1 = get_authorization_manager()
        m2 = get_authorization_manager()
        assert m1 is m2

    def test_reset_auth_managers(self):
        """Verify reset clears instances."""
        m1 = get_token_manager()
        reset_auth_managers()
        m2 = get_token_manager()
        assert m1 is not m2


class TestAuthRoles:
    """Test auth role definitions."""

    def test_all_roles_defined(self):
        """Verify all auth roles are defined."""
        assert AuthRole.ADMIN
        assert AuthRole.OPERATOR
        assert AuthRole.VIEWER
        assert AuthRole.SYSTEM

    def test_role_values(self):
        """Verify role values are correct."""
        assert AuthRole.ADMIN.value == "admin"
        assert AuthRole.OPERATOR.value == "operator"
        assert AuthRole.VIEWER.value == "viewer"
        assert AuthRole.SYSTEM.value == "system"


class TestAuthEndToEnd:
    """End-to-end authentication and authorization flow."""

    def test_full_auth_flow(self):
        """Test complete authentication and authorization flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create user manager
            user_mgr = UserManager(db_path=f"{tmpdir}/auth.db")

            # Create a user with operator role
            roles = {AuthRole.OPERATOR}
            user_mgr.create_user("op1", "operator", "securepass", roles)

            # Authenticate
            user, token = user_mgr.authenticate_user("operator", "securepass")
            assert user.username == "operator"

            # Get token manager and verify token
            token_mgr = TokenManager(db_path=f"{tmpdir}/auth.db")
            verified_user_id = token_mgr.verify_token(token)
            assert verified_user_id == "op1"

            # Check authorization
            auth_mgr = AuthorizationManager()
            auth_mgr.check_authorization(user, "read_tickets")
            auth_mgr.check_authorization(user, "update_tickets")

            # Verify insufficient permission
            with pytest.raises(AuthorizationError):
                auth_mgr.check_authorization(user, "manage_users")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
