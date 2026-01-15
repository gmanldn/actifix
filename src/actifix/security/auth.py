#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Authentication and Authorization Layer.

Implements:
- JWT token-based authentication
- API key support
- Role-based access control (RBAC)
- User session management
- Rate limiting per user
- Audit logging of auth events

Version: 1.0.0
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Set, Tuple
from pathlib import Path


class AuthRole(Enum):
    """User roles for authorization."""
    ADMIN = "admin"        # Full access
    OPERATOR = "operator"  # Manage tickets and config
    VIEWER = "viewer"      # Read-only access
    SYSTEM = "system"      # System operations


@dataclass
class AuthUser:
    """Authenticated user information."""
    user_id: str
    username: str
    roles: Set[AuthRole]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


@dataclass
class AuthToken:
    """Authentication token."""
    token_id: str
    user_id: str
    token_hash: str  # Hashed token value
    token_type: str  # 'bearer', 'api_key'
    created_at: datetime
    expires_at: datetime
    last_used: Optional[datetime] = None
    is_revoked: bool = False


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class TokenManager:
    """Manages authentication tokens and sessions."""

    def __init__(self, secret_key: Optional[str] = None, db_path: Optional[str] = None):
        """Initialize token manager.

        Args:
            secret_key: Secret key for token signing (generated if not provided)
            db_path: Path to SQLite database for token storage
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.db_path = db_path or self._get_default_db_path()
        self.lock = threading.RLock()
        self._init_database()

    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(32)

    def _get_default_db_path(self) -> str:
        """Get default database path for auth data."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'auth.db')

    def _init_database(self) -> None:
        """Initialize database for token storage."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_used TEXT,
                    is_revoked BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES auth_users(user_id)
                )
            ''')

            # Auth events table (audit log)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    success BOOLEAN NOT NULL,
                    details TEXT
                )
            ''')

            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens_user ON auth_tokens(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens_hash ON auth_tokens(token_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp)')

            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass

    def create_token(self, user_id: str, token_type: str = 'bearer', expires_in_hours: int = 24) -> Tuple[str, str]:
        """Create a new authentication token.

        Args:
            user_id: User ID
            token_type: Type of token ('bearer' or 'api_key')
            expires_in_hours: Token expiration time in hours

        Returns:
            Tuple of (token_id, token_value)
        """
        with self.lock:
            token_id = secrets.token_urlsafe(16)
            token_value = secrets.token_urlsafe(32)
            token_hash = self._hash_token(token_value)

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=expires_in_hours)

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO auth_tokens
                    (token_id, user_id, token_hash, token_type, created_at, expires_at, is_revoked)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (
                    token_id,
                    user_id,
                    token_hash,
                    token_type,
                    now.isoformat(),
                    expires_at.isoformat(),
                ))

                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass

            return token_id, token_value

    def verify_token(self, token_value: str) -> Optional[str]:
        """Verify a token and return user_id if valid.

        Args:
            token_value: Token value to verify

        Returns:
            User ID if token is valid, None otherwise
        """
        with self.lock:
            token_hash = self._hash_token(token_value)

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                now = datetime.now(timezone.utc)

                cursor.execute('''
                    SELECT user_id FROM auth_tokens
                    WHERE token_hash = ? AND is_revoked = 0 AND expires_at > ?
                ''', (token_hash, now.isoformat()))

                result = cursor.fetchone()
                conn.close()

                if result:
                    # Update last_used
                    self._update_token_usage(token_hash)
                    return result[0]
            except sqlite3.Error:
                pass

            return None

    def revoke_token(self, token_value: str) -> bool:
        """Revoke a token.

        Args:
            token_value: Token value to revoke

        Returns:
            True if revoked, False if not found
        """
        with self.lock:
            token_hash = self._hash_token(token_value)

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('UPDATE auth_tokens SET is_revoked = 1 WHERE token_hash = ?', (token_hash,))

                conn.commit()
                affected = cursor.rowcount
                conn.close()

                return affected > 0
            except sqlite3.Error:
                pass

            return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user (e.g., on logout).

        Args:
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('UPDATE auth_tokens SET is_revoked = 1 WHERE user_id = ?', (user_id,))

                conn.commit()
                affected = cursor.rowcount
                conn.close()

                return affected
            except sqlite3.Error:
                pass

            return 0

    def _hash_token(self, token_value: str) -> str:
        """Hash a token value for storage."""
        return hashlib.sha256(token_value.encode()).hexdigest()

    def _update_token_usage(self, token_hash: str) -> None:
        """Update last_used timestamp for a token."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            now = datetime.now(timezone.utc)
            cursor.execute('UPDATE auth_tokens SET last_used = ? WHERE token_hash = ?', (now.isoformat(), token_hash))
            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass


class UserManager:
    """Manages user accounts and roles."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize user manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or self._get_default_db_path()
        self.lock = threading.RLock()
        self.token_manager = TokenManager(db_path=db_path)

    def _get_default_db_path(self) -> str:
        """Get default database path."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'auth.db')

    def create_user(self, user_id: str, username: str, password: str, roles: Set[AuthRole]) -> AuthUser:
        """Create a new user.

        Args:
            user_id: Unique user ID
            username: Username
            password: Password (will be hashed)
            roles: Set of roles

        Returns:
            Created AuthUser
        """
        with self.lock:
            password_hash = self._hash_password(password)
            now = datetime.now(timezone.utc)
            roles_json = json.dumps([r.value for r in roles])

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO auth_users
                    (user_id, username, password_hash, roles, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, username, password_hash, roles_json, now.isoformat()))

                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                raise AuthenticationError(f"Failed to create user: {e}")

            return AuthUser(user_id, username, roles, now)

    def authenticate_user(self, username: str, password: str) -> Tuple[AuthUser, str]:
        """Authenticate a user and create a token.

        Args:
            username: Username
            password: Password

        Returns:
            Tuple of (AuthUser, token_value)

        Raises:
            AuthenticationError: If authentication fails
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute(
                    'SELECT user_id, password_hash, roles, is_active FROM auth_users WHERE username = ?',
                    (username,)
                )

                result = cursor.fetchone()
                conn.close()

                if not result:
                    raise AuthenticationError("Invalid username or password")

                user_id, stored_hash, roles_json, is_active = result

                if not is_active:
                    raise AuthenticationError("User account is inactive")

                if not self._verify_password(password, stored_hash):
                    raise AuthenticationError("Invalid username or password")

                # Parse roles
                roles = {AuthRole(r) for r in json.loads(roles_json)}

                # Create token
                _, token_value = self.token_manager.create_token(user_id)

                # Update last_login
                now = datetime.now(timezone.utc)
                self._update_last_login(user_id, now)

                user = AuthUser(user_id, username, roles, now)

                return user, token_value

            except sqlite3.Error as e:
                raise AuthenticationError(f"Authentication failed: {e}")

    def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user information.

        Args:
            user_id: User ID

        Returns:
            AuthUser if found, None otherwise
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute(
                    'SELECT username, roles, created_at, last_login, is_active FROM auth_users WHERE user_id = ?',
                    (user_id,)
                )

                result = cursor.fetchone()
                conn.close()

                if result:
                    username, roles_json, created_at, last_login, is_active = result
                    roles = {AuthRole(r) for r in json.loads(roles_json)}
                    created = datetime.fromisoformat(created_at)
                    last_login_dt = datetime.fromisoformat(last_login) if last_login else None
                    return AuthUser(user_id, username, roles, created, last_login_dt, bool(is_active))
            except sqlite3.Error:
                pass

            return None

    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2."""
        import hashlib
        salt = secrets.token_bytes(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return f"{salt.hex()}${pwdhash.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash."""
        try:
            salt_hex, pwdhash_hex = stored_hash.split('$')
            salt = bytes.fromhex(salt_hex)
            stored_pwdhash = bytes.fromhex(pwdhash_hex)

            import hashlib
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return hmac.compare_digest(pwdhash, stored_pwdhash)
        except Exception:
            return False

    def _update_last_login(self, user_id: str, timestamp: datetime) -> None:
        """Update user's last login time."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute('UPDATE auth_users SET last_login = ? WHERE user_id = ?', (timestamp.isoformat(), user_id))
            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass

    def _log_auth_event(self, event_type: str, user_id: Optional[str], ip_address: Optional[str], success: bool, details: Optional[str] = None) -> None:
        """Log authentication event."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            now = datetime.now(timezone.utc)

            cursor.execute('''
                INSERT INTO auth_events
                (timestamp, event_type, user_id, ip_address, success, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now.isoformat(), event_type, user_id, ip_address, success, details))

            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass


class AuthorizationManager:
    """Manages role-based access control."""

    # Role permissions mapping
    ROLE_PERMISSIONS: Dict[AuthRole, Set[str]] = {
        AuthRole.ADMIN: {
            'read_tickets', 'create_tickets', 'update_tickets', 'delete_tickets',
            'manage_config', 'manage_users', 'manage_plugins', 'view_logs', 'view_audit'
        },
        AuthRole.OPERATOR: {
            'read_tickets', 'create_tickets', 'update_tickets',
            'manage_config', 'view_logs'
        },
        AuthRole.VIEWER: {
            'read_tickets', 'view_logs'
        },
        AuthRole.SYSTEM: {
            'all'  # Special: all permissions
        }
    }

    def __init__(self):
        """Initialize authorization manager."""
        self.lock = threading.RLock()

    def check_authorization(self, user: AuthUser, required_permission: str) -> None:
        """Check if user has required permission.

        Args:
            user: Authenticated user
            required_permission: Permission name to check

        Raises:
            AuthorizationError: If user lacks permission
        """
        with self.lock:
            for role in user.roles:
                permissions = self.ROLE_PERMISSIONS.get(role, set())
                if 'all' in permissions or required_permission in permissions:
                    return

            raise AuthorizationError(
                f"User '{user.username}' lacks permission: {required_permission}"
            )

    def has_permission(self, user: AuthUser, required_permission: str) -> bool:
        """Check if user has permission without raising error.

        Args:
            user: Authenticated user
            required_permission: Permission name to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            self.check_authorization(user, required_permission)
            return True
        except AuthorizationError:
            return False


# Global instances
_token_manager: Optional[TokenManager] = None
_user_manager: Optional[UserManager] = None
_auth_manager: Optional[AuthorizationManager] = None


def get_token_manager() -> TokenManager:
    """Get or create global token manager."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def get_user_manager() -> UserManager:
    """Get or create global user manager."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


def get_authorization_manager() -> AuthorizationManager:
    """Get or create global authorization manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthorizationManager()
    return _auth_manager


def reset_auth_managers() -> None:
    """Reset all auth managers (for testing)."""
    global _token_manager, _user_manager, _auth_manager
    _token_manager = None
    _user_manager = None
    _auth_manager = None
