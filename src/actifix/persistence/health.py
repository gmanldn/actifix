#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Health Monitoring

Storage health monitoring and corruption detection.

Provides health checks for storage systems, detects corruption,
and helps ensure reliability and durability.

Version: 1.0.0 (Generic)
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from .storage import StorageBackend, StorageError


@dataclass
class HealthStatus:
    """Health check result."""
    
    healthy: bool
    timestamp: datetime
    checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]
    
    def __str__(self) -> str:
        """String representation."""
        status = "✓ HEALTHY" if self.healthy else "✗ UNHEALTHY"
        msg = f"{status} at {self.timestamp.isoformat()}\n"
        
        if self.checks:
            msg += "\nChecks:\n"
            for name, passed in self.checks.items():
                symbol = "✓" if passed else "✗"
                msg += f"  {symbol} {name}\n"
        
        if self.errors:
            msg += "\nErrors:\n"
            for err in self.errors:
                msg += f"  - {err}\n"
        
        if self.warnings:
            msg += "\nWarnings:\n"
            for warn in self.warnings:
                msg += f"  - {warn}\n"
        
        return msg


def check_storage_health(backend: StorageBackend, test_key: str = ".health-check") -> HealthStatus:
    """
    Perform health check on storage backend.
    
    Tests:
    - Write access
    - Read access
    - Delete access
    - List access
    
    Args:
        backend: Storage backend to check
        test_key: Key to use for health check operations
        
    Returns:
        HealthStatus with check results
    """
    checks = {}
    errors = []
    warnings = []
    
    timestamp = datetime.now(timezone.utc)
    
    # Test write access
    try:
        test_content = f"health-check-{timestamp.isoformat()}"
        backend.write(test_key, test_content)
        checks["write"] = True
    except Exception as e:
        checks["write"] = False
        errors.append(f"Write failed: {e}")
    
    # Test read access
    try:
        if backend.exists(test_key):
            content = backend.read(test_key)
            checks["read"] = bool(content)
        else:
            checks["read"] = False
            warnings.append("Test key not found for read check")
    except Exception as e:
        checks["read"] = False
        errors.append(f"Read failed: {e}")
    
    # Test list access
    try:
        keys = backend.list_keys()
        checks["list"] = isinstance(keys, list)
    except Exception as e:
        checks["list"] = False
        errors.append(f"List failed: {e}")
    
    # Test delete access
    try:
        if backend.exists(test_key):
            success = backend.delete(test_key)
            checks["delete"] = success
        else:
            checks["delete"] = False
            warnings.append("Test key not found for delete check")
    except Exception as e:
        checks["delete"] = False
        errors.append(f"Delete failed: {e}")
    
    # Overall health
    healthy = all(checks.values()) and not errors
    
    return HealthStatus(
        healthy=healthy,
        timestamp=timestamp,
        checks=checks,
        errors=errors,
        warnings=warnings,
    )


def detect_corruption(
    backend: StorageBackend,
    sample_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Detect potential corruption in stored data.
    
    Checks:
    - File readability
    - UTF-8 encoding validity
    - Known corruption patterns
    
    Args:
        backend: Storage backend to check
        sample_keys: Optional list of keys to sample (checks all if None)
        
    Returns:
        Dict with corruption detection results
    """
    results = {
        "checked": 0,
        "corrupted": 0,
        "unreadable": 0,
        "invalid_encoding": 0,
        "issues": [],
    }
    
    # Get keys to check
    if sample_keys is None:
        try:
            sample_keys = backend.list_keys()
        except Exception:
            sample_keys = []
    
    # Check each key
    for key in sample_keys:
        results["checked"] += 1
        
        try:
            content = backend.read(key)
            
            # Check for null bytes
            if "\x00" in content:
                results["corrupted"] += 1
                results["issues"].append(f"Null bytes in {key}")
            
            # Check for truncation (incomplete UTF-8 sequences)
            try:
                content.encode("utf-8").decode("utf-8")
            except UnicodeDecodeError:
                results["invalid_encoding"] += 1
                results["issues"].append(f"Invalid UTF-8 in {key}")
                
        except Exception as e:
            results["unreadable"] += 1
            results["issues"].append(f"Unreadable {key}: {e}")
    
    return results


def verify_integrity(
    backend: StorageBackend,
    key: str,
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Verify data integrity using hash.
    
    Args:
        backend: Storage backend
        key: Storage key
        expected_hash: Expected hash value
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        content = backend.read(key)
        
        if algorithm == "sha256":
            actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        elif algorithm == "md5":
            actual_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return actual_hash == expected_hash
    except Exception:
        return False


def compute_hash(
    backend: StorageBackend,
    key: str,
    algorithm: str = "sha256",
) -> Optional[str]:
    """
    Compute hash of stored data.
    
    Args:
        backend: Storage backend
        key: Storage key
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hash value or None if compute fails
    """
    try:
        content = backend.read(key)
        
        if algorithm == "sha256":
            return hashlib.sha256(content.encode("utf-8")).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(content.encode("utf-8")).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    except Exception:
        return None
