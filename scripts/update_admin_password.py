#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update admin user password.

This script updates the existing admin user's password to the specified one.
"""

import os
import sqlite3
import sys
from getpass import getpass
from pathlib import Path
import hashlib
import secrets

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from actifix.state_paths import get_actifix_paths


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return f"{salt.hex()}${pwdhash.hex()}"


def resolve_password() -> str:
    candidate = os.getenv("ACTIFIX_ADMIN_PASSWORD")
    if candidate:
        print("Using ACTIFIX_ADMIN_PASSWORD from environment.")
        return candidate
    return getpass("Enter new admin password (or press enter to cancel): ").strip()


def update_admin_password():
    """Update the admin user's password in the database."""
    print("Updating admin user password...")
    password = resolve_password()
    if not password:
        print("No password supplied; aborting.")
        return False

    hashed_password = hash_password(password)

    print("\n" + "=" * 80)
    print("SECURITY NOTICE:")
    print("=" * 80)
    print("The password has been hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations.")
    print("The plain text password is NOT stored in the code.")
    print("Only the hashed version is stored in the database.")
    print("=" * 80)

    paths = get_actifix_paths()
    auth_db_path = Path(paths.state_dir) / "auth.db"

    if not auth_db_path.exists():
        print(f"\n✗ Auth database not found at: {auth_db_path}")
        print("   Please run the application first to initialize the database.")
        return False

    try:
        conn = sqlite3.connect(str(auth_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, username FROM auth_users WHERE user_id = 'admin'")
        result = cursor.fetchone()

        if not result:
            print("\n✗ Admin user not found in database.")
            conn.close()
            return False

        user_id, username = result
        print(f"\n✓ Found admin user: {username} (ID: {user_id})")

        cursor.execute(
            "UPDATE auth_users SET password_hash = ? WHERE user_id = 'admin'",
            (hashed_password,),
        )

        conn.commit()
        conn.close()

        print(f"\n✓ Admin password updated successfully!")
        print("\n✓ You can now log in with:")
        print("   Username: admin")
        print("   Password: (as provided)")

        return True

    except Exception as exc:
        print(f"\n✗ Failed to update admin password: {exc}")
        return False


if __name__ == "__main__":
    update_admin_password()
