"""
Comprehensive tests for persistence health monitoring.
Tests health checks, corruption detection, and integrity verification.
"""

import hashlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from actifix.persistence.health import (
    HealthStatus,
    check_storage_health,
    detect_corruption,
    verify_integrity,
    compute_hash,
)
from actifix.persistence.storage import StorageBackend, StorageError


class MockStorage(StorageBackend):
    """Mock storage backend for testing."""
    
    def __init__(self, fail_write=False, fail_read=False, fail_list=False, fail_delete=False):
        self.data = {}
        self.fail_write = fail_write
        self.fail_read = fail_read
        self.fail_list = fail_list
        self.fail_delete = fail_delete
    
    def write(self, key: str, content: str) -> None:
        if self.fail_write:
            raise StorageError("Write failed")
        self.data[key] = content

    def write_bytes(self, key: str, content: bytes) -> None:
        if self.fail_write:
            raise StorageError("Write failed")
        self.data[key] = content.decode("utf-8", errors="replace")
    
    def read(self, key: str) -> str:
        if self.fail_read:
            raise StorageError("Read failed")
        if key not in self.data:
            raise StorageError(f"Key not found: {key}")
        return self.data[key]

    def read_bytes(self, key: str) -> bytes:
        if self.fail_read:
            raise StorageError("Read failed")
        if key not in self.data:
            raise StorageError(f"Key not found: {key}")
        return self.data[key].encode("utf-8")
    
    def exists(self, key: str) -> bool:
        return key in self.data
    
    def delete(self, key: str) -> bool:
        if self.fail_delete:
            raise StorageError("Delete failed")
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def list_keys(self) -> list:
        if self.fail_list:
            raise StorageError("List failed")
        return list(self.data.keys())

    def size(self, key: str) -> int:
        if key not in self.data:
            raise StorageError(f"Key not found: {key}")
        return len(self.data[key].encode("utf-8"))


class TestHealthStatus:
    """Test HealthStatus dataclass."""
    
    def test_health_status_creation(self):
        """Test creating HealthStatus."""
        status = HealthStatus(
            healthy=True,
            timestamp=datetime.now(timezone.utc),
            checks={"test": True},
            errors=[],
            warnings=[],
        )
        
        assert status.healthy
        assert "test" in status.checks
    
    def test_health_status_string_healthy(self):
        """Test string representation of healthy status."""
        status = HealthStatus(
            healthy=True,
            timestamp=datetime.now(timezone.utc),
            checks={"write": True, "read": True},
            errors=[],
            warnings=[],
        )
        
        result = str(status)
        assert "HEALTHY" in result
        assert "write" in result
    
    def test_health_status_string_unhealthy(self):
        """Test string representation of unhealthy status."""
        status = HealthStatus(
            healthy=False,
            timestamp=datetime.now(timezone.utc),
            checks={"write": False},
            errors=["Write failed"],
            warnings=["Warning message"],
        )
        
        result = str(status)
        assert "UNHEALTHY" in result
        assert "Write failed" in result
        assert "Warning message" in result


class TestCheckStorageHealth:
    """Test storage health checking."""
    
    def test_check_storage_health_all_pass(self):
        """Test health check with all operations passing."""
        storage = MockStorage()
        
        result = check_storage_health(storage)
        
        assert result.healthy
        assert result.checks["write"]
        assert result.checks["read"]
        assert result.checks["list"]
        assert result.checks["delete"]
        assert len(result.errors) == 0
    
    def test_check_storage_health_write_fails(self):
        """Test health check when write fails."""
        storage = MockStorage(fail_write=True)
        
        result = check_storage_health(storage)
        
        assert not result.healthy
        assert not result.checks["write"]
        assert any("write failed" in err.lower() for err in result.errors)
    
    def test_check_storage_health_read_fails(self):
        """Test health check when read fails."""
        storage = MockStorage(fail_read=True)
        
        result = check_storage_health(storage)
        
        assert not result.healthy
        assert not result.checks["read"]
        assert any("read failed" in err.lower() for err in result.errors)
    
    def test_check_storage_health_list_fails(self):
        """Test health check when list fails."""
        storage = MockStorage(fail_list=True)
        
        result = check_storage_health(storage)
        
        assert not result.healthy
        assert not result.checks["list"]
        assert any("list failed" in err.lower() for err in result.errors)
    
    def test_check_storage_health_delete_fails(self):
        """Test health check when delete fails."""
        storage = MockStorage(fail_delete=True)
        
        result = check_storage_health(storage)
        
        assert not result.healthy
        assert not result.checks["delete"]
        assert any("delete failed" in err.lower() for err in result.errors)
    
    def test_check_storage_health_custom_test_key(self):
        """Test health check with custom test key."""
        storage = MockStorage()
        
        result = check_storage_health(storage, test_key="custom-health")
        
        assert result.healthy


class TestDetectCorruption:
    """Test corruption detection."""
    
    def test_detect_corruption_no_issues(self):
        """Test corruption detection with clean data."""
        storage = MockStorage()
        storage.write("key1", "Valid content")
        storage.write("key2", "Another valid content")
        
        result = detect_corruption(storage)
        
        assert result["checked"] == 2
        assert result["corrupted"] == 0
        assert result["unreadable"] == 0
        assert result["invalid_encoding"] == 0
    
    def test_detect_corruption_null_bytes(self):
        """Test detection of null bytes."""
        storage = MockStorage()
        storage.data["key1"] = "Content with\x00null byte"
        
        result = detect_corruption(storage)
        
        assert result["corrupted"] == 1
        assert any("null bytes" in issue.lower() for issue in result["issues"])
    
    def test_detect_corruption_unreadable(self):
        """Test detection of unreadable data."""
        storage = MockStorage()
        storage.write("key1", "valid")
        # Make one key unreadable
        storage.fail_read = True
        
        result = detect_corruption(storage, sample_keys=["key1"])
        
        assert result["unreadable"] == 1
    
    def test_detect_corruption_sample_keys(self):
        """Test corruption detection with sample keys."""
        storage = MockStorage()
        storage.write("key1", "Content 1")
        storage.write("key2", "Content 2")
        storage.write("key3", "Content 3")
        
        result = detect_corruption(storage, sample_keys=["key1", "key2"])
        
        assert result["checked"] == 2
    
    def test_detect_corruption_empty_storage(self):
        """Test corruption detection on empty storage."""
        storage = MockStorage()
        
        result = detect_corruption(storage)
        
        assert result["checked"] == 0
        assert result["corrupted"] == 0


class TestVerifyIntegrity:
    """Test data integrity verification."""
    
    def test_verify_integrity_sha256_match(self):
        """Test integrity verification with matching SHA256."""
        storage = MockStorage()
        content = "Test content"
        storage.write("key1", content)
        
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        
        result = verify_integrity(storage, "key1", expected_hash, "sha256")
        
        assert result is True
    
    def test_verify_integrity_sha256_mismatch(self):
        """Test integrity verification with mismatched SHA256."""
        storage = MockStorage()
        storage.write("key1", "Test content")
        
        wrong_hash = "0" * 64
        
        result = verify_integrity(storage, "key1", wrong_hash, "sha256")
        
        assert result is False
    
    def test_verify_integrity_md5_match(self):
        """Test integrity verification with matching MD5."""
        storage = MockStorage()
        content = "Test content"
        storage.write("key1", content)
        
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        
        result = verify_integrity(storage, "key1", expected_hash, "md5")
        
        assert result is True
    
    def test_verify_integrity_unsupported_algorithm(self):
        """Test integrity verification with unsupported algorithm."""
        storage = MockStorage()
        storage.write("key1", "Test")
        
        result = verify_integrity(storage, "key1", "hash", "invalid")
        
        assert result is False
    
    def test_verify_integrity_missing_key(self):
        """Test integrity verification with missing key."""
        storage = MockStorage()
        
        result = verify_integrity(storage, "missing", "hash", "sha256")
        
        assert result is False


class TestComputeHash:
    """Test hash computation."""
    
    def test_compute_hash_sha256(self):
        """Test SHA256 hash computation."""
        storage = MockStorage()
        content = "Test content"
        storage.write("key1", content)
        
        result = compute_hash(storage, "key1", "sha256")
        
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert result == expected
    
    def test_compute_hash_md5(self):
        """Test MD5 hash computation."""
        storage = MockStorage()
        content = "Test content"
        storage.write("key1", content)
        
        result = compute_hash(storage, "key1", "md5")
        
        expected = hashlib.md5(content.encode()).hexdigest()
        assert result == expected
    
    def test_compute_hash_missing_key(self):
        """Test hash computation with missing key."""
        storage = MockStorage()
        
        result = compute_hash(storage, "missing", "sha256")
        
        assert result is None
    
    def test_compute_hash_unsupported_algorithm(self):
        """Test hash computation with unsupported algorithm."""
        storage = MockStorage()
        storage.write("key1", "Test")
        
        result = compute_hash(storage, "key1", "invalid")
        
        assert result is None
    
    def test_compute_hash_read_error(self):
        """Test hash computation when read fails."""
        storage = MockStorage(fail_read=True)
        storage.data["key1"] = "Test"
        
        result = compute_hash(storage, "key1", "sha256")
        
        assert result is None
