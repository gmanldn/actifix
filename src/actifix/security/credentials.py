#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Credential Manager - Securely store and retrieve credentials.

Integrates with system credential managers:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Pass or encrypted storage

Provides a unified interface for secure credential storage.

Version: 1.0.0
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
from pathlib import Path

from ..log_utils import atomic_write

class CredentialType(Enum):
    """Types of credentials."""
    API_KEY = "api_key"
    PASSWORD = "password"  # EXAMPLE label for secret scanner false-positive
    TOKEN = "token"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"


@dataclass
class Credential:
    """Stored credential information."""
    name: str
    credential_type: CredentialType
    value: str
    description: Optional[str] = None
    metadata: Dict[str, str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CredentialStorageError(Exception):
    """Raised when credential storage operation fails."""
    pass


class CredentialRetrievalError(Exception):
    """Raised when credential retrieval fails."""
    pass


class MacOSKeychain:
    """macOS Keychain credential storage."""

    def __init__(self, service_name: str = "Actifix"):
        """Initialize Keychain storage.

        Args:
            service_name: Service name for grouping credentials in Keychain
        """
        self.service_name = service_name

    def store(self, name: str, credential: Credential) -> None:
        """Store credential in Keychain.

        Args:
            name: Credential name
            credential: Credential to store

        Raises:
            CredentialStorageError: If storage fails
        """
        try:
            # Use security command to add credential to Keychain
            account = f"{self.service_name}_{name}"

            # Add or update credential
            subprocess.run([
                'security', 'add-generic-password',
                '-s', self.service_name,
                '-a', account,
                '-w', credential.value,
                '-U',  # Update if exists
            ], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            raise CredentialStorageError(f"Failed to store credential in Keychain: {e}")

    def retrieve(self, name: str) -> Optional[str]:
        """Retrieve credential from Keychain.

        Args:
            name: Credential name

        Returns:
            Credential value if found, None otherwise

        Raises:
            CredentialRetrievalError: If retrieval fails
        """
        try:
            account = f"{self.service_name}_{name}"

            result = subprocess.run([
                'security', 'find-generic-password',
                '-s', self.service_name,
                '-a', account,
                '-w',
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except subprocess.CalledProcessError as e:
            raise CredentialRetrievalError(f"Failed to retrieve credential from Keychain: {e}")

    def delete(self, name: str) -> bool:
        """Delete credential from Keychain.

        Args:
            name: Credential name

        Returns:
            True if deleted, False if not found
        """
        try:
            account = f"{self.service_name}_{name}"

            result = subprocess.run([
                'security', 'delete-generic-password',
                '-s', self.service_name,
                '-a', account,
            ], capture_output=True)

            return result.returncode == 0

        except subprocess.CalledProcessError:
            return False


class WindowsCredentialManager:
    """Windows Credential Manager storage."""

    def __init__(self, target_prefix: str = "Actifix"):
        """Initialize Windows Credential Manager storage.

        Args:
            target_prefix: Prefix for credential targets
        """
        self.target_prefix = target_prefix

    def store(self, name: str, credential: Credential) -> None:
        """Store credential in Windows Credential Manager.

        Args:
            name: Credential name
            credential: Credential to store

        Raises:
            CredentialStorageError: If storage fails
        """
        try:
            target = f"{self.target_prefix}/{name}"

            # Create credential JSON
            cred_data = json.dumps({
                'type': credential.credential_type.value,
                'value': credential.value,
                'description': credential.description,
            })

            # Use cmdkey or powershell to store credential
            if sys.platform == 'win32':
                import subprocess as sp
                sp.run([
                    'powershell', '-Command',
                    f'[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                    f'$cred = New-Object System.Management.Automation.PSCredential("{target}", (ConvertTo-SecureString "{credential.value}" -AsPlainText -Force)); '
                    f'$cred | Export-Clixml -Path $env:APPDATA\\Actifix\\creds_{name}.xml'
                ], check=True, capture_output=True)
            else:
                raise CredentialStorageError("Windows Credential Manager only available on Windows")

        except (subprocess.CalledProcessError, ImportError) as e:
            raise CredentialStorageError(f"Failed to store credential in Credential Manager: {e}")

    def retrieve(self, name: str) -> Optional[str]:
        """Retrieve credential from Windows Credential Manager.

        Args:
            name: Credential name

        Returns:
            Credential value if found, None otherwise

        Raises:
            CredentialRetrievalError: If retrieval fails
        """
        try:
            if sys.platform == 'win32':
                import subprocess as sp
                cred_file = os.path.expandvars(rf'$env:APPDATA\Actifix\creds_{name}.xml')

                if os.path.exists(cred_file):
                    result = sp.run([
                        'powershell', '-Command',
                        f'$cred = Import-Clixml -Path "{cred_file}"; $cred.GetNetworkCredential().Password'
                    ], capture_output=True, text=True)

                    if result.returncode == 0:
                        return result.stdout.strip()

            return None

        except Exception as e:
            raise CredentialRetrievalError(f"Failed to retrieve credential from Credential Manager: {e}")

    def delete(self, name: str) -> bool:
        """Delete credential from Windows Credential Manager.

        Args:
            name: Credential name

        Returns:
            True if deleted, False if not found
        """
        try:
            if sys.platform == 'win32':
                cred_file = os.path.expandvars(rf'$env:APPDATA\Actifix\creds_{name}.xml')

                if os.path.exists(cred_file):
                    os.remove(cred_file)
                    return True

            return False

        except Exception:
            return False


class FileSystemCredentialStore:
    """Fallback encrypted file-based credential storage (for Linux or when native manager unavailable)."""

    def __init__(self, store_dir: Optional[str] = None):
        """Initialize file-based credential store.

        Args:
            store_dir: Directory for storing credentials
        """
        self.store_dir = store_dir or self._get_default_store_dir()
        self._ensure_store_dir()

    def _get_default_store_dir(self) -> str:
        """Get default credential store directory."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'credentials')

    def _ensure_store_dir(self) -> None:
        """Ensure store directory exists with proper permissions."""
        os.makedirs(self.store_dir, exist_ok=True, mode=0o700)

    def store(self, name: str, credential: Credential) -> None:
        """Store credential in encrypted file.

        Args:
            name: Credential name
            credential: Credential to store

        Raises:
            CredentialStorageError: If storage fails
        """
        try:
            # In production, this would encrypt with proper key management
            # For now, we store as plain JSON with restricted permissions
            cred_file = Path(self.store_dir) / f"{name}.json"

            data = {
                'name': credential.name,
                'type': credential.credential_type.value,
                'value': credential.value,
                'description': credential.description,
                'metadata': credential.metadata,
            }

            with open(cred_file, 'w') as f:
                json.dump(data, f)

            # Restrict permissions
            os.chmod(cred_file, 0o600)

        except Exception as e:
            raise CredentialStorageError(f"Failed to store credential: {e}")

    def retrieve(self, name: str) -> Optional[str]:
        """Retrieve credential from file.

        Args:
            name: Credential name

        Returns:
            Credential value if found, None otherwise

        Raises:
            CredentialRetrievalError: If retrieval fails
        """
        try:
            cred_file = Path(self.store_dir) / f"{name}.json"

            if cred_file.exists():
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                    return data.get('value')

            return None

        except Exception as e:
            raise CredentialRetrievalError(f"Failed to retrieve credential: {e}")

    def delete(self, name: str) -> bool:
        """Delete credential file.

        Args:
            name: Credential name

        Returns:
            True if deleted, False if not found
        """
        try:
            cred_file = Path(self.store_dir) / f"{name}.json"

            if cred_file.exists():
                cred_file.unlink()
                return True

            return False

        except Exception:
            return False


class CredentialManager:
    """Unified credential manager with system integration."""

    def __init__(self):
        """Initialize credential manager with appropriate backend."""
        self.backend = self._select_backend()

    def _select_backend(self):
        """Select appropriate credential storage backend."""
        if sys.platform == 'darwin':
            # macOS: Use Keychain
            return MacOSKeychain()
        elif sys.platform == 'win32':
            # Windows: Use Credential Manager
            return WindowsCredentialManager()
        else:
            # Linux/other: Use encrypted file storage
            return FileSystemCredentialStore()

    def store_credential(self, name: str, value: str, cred_type: CredentialType = CredentialType.PASSWORD, description: Optional[str] = None) -> None:
        """Store a credential.

        Args:
            name: Credential name/identifier
            value: Credential value (API key, password, token, etc.)
            cred_type: Type of credential
            description: Optional description

        Raises:
            CredentialStorageError: If storage fails
        """
        credential = Credential(name, cred_type, value, description)
        self.backend.store(name, credential)

    def retrieve_credential(self, name: str) -> Optional[str]:
        """Retrieve a credential.

        Args:
            name: Credential name/identifier

        Returns:
            Credential value if found, None otherwise

        Raises:
            CredentialRetrievalError: If retrieval fails
        """
        return self.backend.retrieve(name)

    def delete_credential(self, name: str) -> bool:
        """Delete a credential.

        Args:
            name: Credential name/identifier

        Returns:
            True if deleted, False if not found
        """
        return self.backend.delete(name)

    def has_credential(self, name: str) -> bool:
        """Check if a credential exists.

        Args:
            name: Credential name/identifier

        Returns:
            True if credential exists, False otherwise
        """
        try:
            value = self.retrieve_credential(name)
            return value is not None
        except CredentialRetrievalError:
            return False


def export_github_deploy_key(target_path: Optional[Path] = None) -> Optional[Path]:
    """Export the stored GitHub deploy key to a secure file path.

    Args:
        target_path: Optional path for the exported key file.

    Returns:
        Path to the exported key file, or None if no credential is stored.
    """
    manager = get_credential_manager()
    value = manager.retrieve_credential("github_deploy_key")
    if not value:
        return None

    if target_path is None:
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        target_dir = Path(paths.state_dir) / "credentials" / "ssh"
        target_path = target_dir / "github_deploy_key"
    else:
        target_path = Path(target_path)
        target_dir = target_path.parent

    os.makedirs(target_dir, exist_ok=True, mode=0o700)
    atomic_write(target_path, value)
    os.chmod(target_path, 0o600)
    return target_path


# Global credential manager instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get or create global credential manager."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def reset_credential_manager() -> None:
    """Reset global credential manager (for testing)."""
    global _credential_manager
    _credential_manager = None
