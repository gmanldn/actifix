#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup admin user with hashed password.

This script creates an admin user with a pre-hashed password for secure access.
"""

import os
import sys
from getpass import getpass
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from actifix.security.auth import get_user_manager, AuthRole, get_token_manager


def resolve_password() -> str:
    """Prompt for a password or read from env var."""
    candidate = os.getenv("ACTIFIX_ADMIN_PASSWORD")
    if candidate:
        print("Using ACTIFIX_ADMIN_PASSWORD from environment.")
        return candidate
    return getpass("Enter admin password (or press enter to cancel): ").strip()


def setup_admin_user():
    """Create admin user with hashed password."""
    print("Setting up admin user...")
    password = resolve_password()
    if not password:
        print("No password supplied; aborting.")
        return None

    user_manager = get_user_manager()

    try:
        existing_user = user_manager.get_user("admin")
        if existing_user:
            print(f"\n⚠️  Admin user already exists: {existing_user.username}")
            print(f"   Roles: {[r.value for r in existing_user.roles]}")
            print(f"   Active: {existing_user.is_active}")
            return None
    except Exception:
        pass

    try:
        user = user_manager.create_user(
            user_id="admin",
            username="admin",
            password=password,
            roles={AuthRole.ADMIN},
        )

        token_manager = get_token_manager()
        _, token = token_manager.create_token(user.user_id)

        print(f"\n✓ Admin user created successfully!")
        print(f"   User ID: {user.user_id}")
        print(f"   Username: {user.username}")
        print(f"   Roles: {[r.value for r in user.roles]}")
        print(f"   Token: {token}")
        print(f"\n✓ You can now log in with:")
        print(f"   Username: admin")
        print(f"   Password: (as provided)")
        print(f"   Token: {token}")

        return token

    except Exception as exc:
        print(f"\n✗ Failed to create admin user: {exc}")
        return None


if __name__ == "__main__":
    setup_admin_user()
