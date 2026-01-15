#!/usr/bin/env python3
"""
Tests for queue persistence atomicity fix.

Verifies that:
1. Queue data is written atomically to prevent partial writes
2. Legacy files are only deleted after successful writes
3. Failed writes preserve legacy data for recovery
4. Temporary files are cleaned up on failure
5. No data loss on write failures
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from actifix.raise_af import _persist_queue, _load_existing_queue


@pytest.fixture
def tmp_queue_dirs(tmp_path):
    """Create temporary directories for queue testing."""
    primary_dir = tmp_path / "primary"
    primary_dir.mkdir()
    primary_file = primary_dir / "queue.json"

    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    legacy_file = legacy_dir / "queue.json"

    return {
        "primary_file": primary_file,
        "legacy_file": legacy_file,
        "primary_dir": primary_dir,
        "legacy_dir": legacy_dir,
        "tmp_path": tmp_path,
    }


class TestQueuePersistenceAtomic:
    """Test atomic queue persistence to prevent data loss."""

    def test_persist_queue_writes_to_target(self, tmp_queue_dirs):
        """Verify queue is written to target file."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        queue_data = [{"id": "ACT-001", "message": "test"}]

        _persist_queue(queue_data, primary, legacy)

        assert primary.exists(), "Target file should exist"
        content = json.loads(primary.read_text())
        assert content == queue_data, "Queue data should match"

    def test_persist_queue_deletes_legacy_after_write(self, tmp_queue_dirs):
        """Verify legacy file is deleted only after successful write."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        # Create legacy file with old data
        legacy_data = [{"id": "OLD-001", "message": "old"}]
        legacy.write_text(json.dumps(legacy_data))
        assert legacy.exists(), "Legacy file should exist initially"

        # Persist new queue
        new_queue = [{"id": "NEW-001", "message": "new"}]
        _persist_queue(new_queue, primary, legacy)

        # Legacy file should be deleted
        assert not legacy.exists(), "Legacy file should be deleted after successful write"

        # Primary file should have new data
        content = json.loads(primary.read_text())
        assert content == new_queue, "Primary file should contain new data"

    def test_persist_queue_preserves_legacy_on_write_failure(self, tmp_queue_dirs):
        """Verify legacy file is preserved if write to primary fails."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        # Create legacy file with valuable data
        legacy_data = [{"id": "VALUABLE-001", "message": "important"}]
        legacy.write_text(json.dumps(legacy_data))

        queue_data = [{"id": "NEW-001", "message": "new"}]

        # Mock write_text to fail
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                _persist_queue(queue_data, primary, legacy)

        # Legacy file should still exist (data preserved)
        assert legacy.exists(), "Legacy file should be preserved on write failure"

        # Verify legacy data is intact
        legacy_content = json.loads(legacy.read_text())
        assert legacy_content == legacy_data, "Legacy data should be unchanged"

    def test_persist_queue_cleans_up_temp_file_on_failure(self, tmp_queue_dirs):
        """Verify temporary file is cleaned up if write fails."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        queue_data = [{"id": "TEST-001", "message": "test"}]

        # Mock replace() to fail after temp file is created
        call_count = {"count": 0}

        def mock_replace(path_self, target):
            call_count["count"] += 1
            if ".tmp" in str(path_self) and call_count["count"] == 1:
                raise OSError("Replace failed")
            return original_replace(path_self, target)

        original_replace = Path.replace

        with patch.object(Path, "replace", mock_replace):
            with pytest.raises(OSError):
                _persist_queue(queue_data, primary, legacy)

        # Check for leftover temp files
        temp_files = list(primary.parent.glob("*.tmp"))
        assert len(temp_files) == 0, "Temporary files should be cleaned up on failure"

    def test_persist_queue_no_temp_file_after_success(self, tmp_queue_dirs):
        """Verify no temporary files remain after successful write."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        queue_data = [{"id": "TEST-001", "message": "test"}]

        _persist_queue(queue_data, primary, legacy)

        # Check for leftover temp files
        temp_files = list(primary.parent.glob("*.tmp"))
        assert len(temp_files) == 0, "No temporary files should exist after successful write"

    def test_persist_queue_handles_missing_parent_directory(self, tmp_queue_dirs):
        """Verify parent directory is created if it doesn't exist."""
        primary_dir = tmp_queue_dirs["primary_dir"]
        nested_path = primary_dir / "nested" / "deep" / "queue.json"
        legacy = tmp_queue_dirs["legacy_file"]

        queue_data = [{"id": "NESTED-001", "message": "nested"}]

        assert not nested_path.parent.exists(), "Parent directory should not exist"

        _persist_queue(queue_data, nested_path, legacy)

        assert nested_path.exists(), "Queue file should be created"
        assert nested_path.parent.exists(), "Parent directory should be created"

    def test_persist_queue_same_primary_and_legacy_doesnt_delete(self, tmp_queue_dirs):
        """Verify that if primary and legacy are the same, we don't try to delete."""
        same_path = tmp_queue_dirs["primary_file"]

        queue_data = [{"id": "SAME-001", "message": "same"}]

        # Should not raise error when primary and legacy are same
        _persist_queue(queue_data, same_path, same_path)

        assert same_path.exists(), "File should exist"
        content = json.loads(same_path.read_text())
        assert content == queue_data, "Data should be written"


class TestLoadExistingQueue:
    """Test loading queue from primary or legacy locations."""

    def test_load_from_primary_if_exists(self, tmp_queue_dirs):
        """Verify queue is loaded from primary if available."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        primary_data = [{"id": "PRIMARY-001", "message": "primary"}]
        legacy_data = [{"id": "LEGACY-001", "message": "legacy"}]

        primary.write_text(json.dumps(primary_data))
        legacy.write_text(json.dumps(legacy_data))

        loaded, source = _load_existing_queue(primary, legacy)

        assert loaded == primary_data, "Should load from primary"
        assert source == primary, "Should return primary as source"

    def test_load_from_legacy_if_primary_missing(self, tmp_queue_dirs):
        """Verify queue is loaded from legacy if primary doesn't exist."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        legacy_data = [{"id": "LEGACY-001", "message": "legacy"}]
        legacy.write_text(json.dumps(legacy_data))

        assert not primary.exists(), "Primary should not exist"

        loaded, source = _load_existing_queue(primary, legacy)

        assert loaded == legacy_data, "Should load from legacy"
        assert source == legacy, "Should return legacy as source"

    def test_load_returns_empty_if_both_missing(self, tmp_queue_dirs):
        """Verify empty queue is returned if both files missing."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        assert not primary.exists(), "Primary should not exist"
        assert not legacy.exists(), "Legacy should not exist"

        loaded, source = _load_existing_queue(primary, legacy)

        assert loaded == [], "Should return empty queue"
        assert source == primary, "Should return primary as source"

    def test_load_corrupted_file_falls_back_to_primary(self, tmp_queue_dirs):
        """Verify corrupted legacy file falls back to primary."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        # Corrupted legacy
        legacy.write_text("invalid json {{{")

        loaded, source = _load_existing_queue(primary, legacy)

        assert loaded == [], "Should return empty queue on parse error"
        assert source == primary, "Should return primary as fallback source"

    def test_load_respects_file_order(self, tmp_queue_dirs):
        """Verify primary file is preferred over legacy."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        primary_data = [{"id": "1", "message": "primary"}]
        legacy_data = [{"id": "2", "message": "legacy"}]

        primary.write_text(json.dumps(primary_data))
        legacy.write_text(json.dumps(legacy_data))

        loaded, source = _load_existing_queue(primary, legacy)

        assert loaded == primary_data, "Primary should be preferred"
        assert source == primary


class TestQueuePersistenceRecovery:
    """Test data recovery scenarios with atomic writes."""

    def test_recovery_from_legacy_after_failed_migration(self, tmp_queue_dirs):
        """Verify data is recoverable from legacy after failed primary write."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        # Simulate legacy data from previous version
        legacy_data = [
            {"id": "ACT-100", "message": "ticket 1"},
            {"id": "ACT-101", "message": "ticket 2"},
        ]
        legacy.write_text(json.dumps(legacy_data))

        # Try to migrate to primary (simulate failure)
        new_queue = legacy_data + [{"id": "ACT-102", "message": "ticket 3"}]

        # Mock the replace to fail mid-operation
        with patch.object(Path, "replace", side_effect=IOError("I/O error")):
            with pytest.raises(IOError):
                _persist_queue(new_queue, primary, legacy)

        # Both files should be accessible
        assert legacy.exists(), "Legacy file should still exist"
        assert not primary.exists(), "Primary shouldn't be created on failure"

        # Can still load from legacy
        loaded, source = _load_existing_queue(primary, legacy)
        assert loaded == legacy_data, "Original legacy data should be recoverable"

    def test_atomic_write_prevents_partial_data(self, tmp_queue_dirs):
        """Verify atomic write prevents partial/corrupted data."""
        primary = tmp_queue_dirs["primary_file"]
        legacy = tmp_queue_dirs["legacy_file"]

        large_queue = [{"id": f"ACT-{i}", "message": f"ticket {i}"} for i in range(100)]

        _persist_queue(large_queue, primary, legacy)

        # Verify file is not partial/corrupted
        content = primary.read_text()
        parsed = json.loads(content)  # Should not raise JSONDecodeError

        assert len(parsed) == 100, "All items should be persisted"
        assert parsed == large_queue, "Data should be intact"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
