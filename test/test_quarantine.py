"""
Comprehensive tests for Actifix quarantine system.
Tests error quarantine, ticket isolation, and recovery mechanisms.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from actifix.quarantine import (
    generate_quarantine_id,
    quarantine_content,
    quarantine_file,
    list_quarantine,
    remove_quarantine,
    get_quarantine_count,
    QuarantineEntry,
)
from actifix.state_paths import get_actifix_paths, init_actifix_files


class TestQuarantineIdGeneration:
    """Test quarantine ID generation."""
    
    def test_generate_quarantine_id_format(self):
        """Test quarantine ID has correct format."""
        qid = generate_quarantine_id()
        
        assert qid.startswith("quarantine_")
        assert len(qid) > len("quarantine_")
    
    def test_generate_quarantine_id_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_quarantine_id() for _ in range(10)]
        
        assert len(ids) == len(set(ids))
    
    def test_generate_quarantine_id_contains_timestamp(self):
        """Test ID contains timestamp components."""
        qid = generate_quarantine_id()
        
        # Should contain date components
        assert any(c.isdigit() for c in qid)


class TestQuarantineContent:
    """Test content quarantine functionality."""
    
    def test_quarantine_content_basic(self, tmp_path):
        """Test basic content quarantine."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        content = "Test content"
        source = "test.py"
        reason = "Test reason"
        
        entry = quarantine_content(content, source, reason, paths)
        
        assert entry.original_source == source
        assert entry.reason == reason
        assert entry.content == content
        assert entry.file_path.exists()
    
    def test_quarantine_content_writes_file(self, tmp_path):
        """Test that quarantine writes a file."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("Test", "source", "reason", paths)
        
        assert entry.file_path.exists()
        content = entry.file_path.read_text()
        assert "Test" in content
        assert "source" in content
        assert "reason" in content
    
    def test_quarantine_content_includes_metadata(self, tmp_path):
        """Test quarantine file includes all metadata."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("Content", "src.py", "Bad format", paths)
        
        content = entry.file_path.read_text()
        assert "Entry ID" in content
        assert "Source" in content
        assert "Reason" in content
        assert "Quarantined At" in content
        assert "Recovery Notes" in content
    
    def test_quarantine_content_uses_default_paths(self, tmp_path, monkeypatch):
        """Test quarantine with default paths."""
        monkeypatch.chdir(tmp_path)
        paths = get_actifix_paths()
        init_actifix_files(paths)
        
        entry = quarantine_content("Test", "source", "reason")
        
        assert entry is not None
        assert entry.file_path.exists()
    
    def test_quarantine_content_logs_event(self, tmp_path):
        """Test that quarantine logs an event."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        quarantine_content("Test", "source", "reason", paths)
        
        # Check AFLog was written
        assert paths.aflog_file.exists()
        log_content = paths.aflog_file.read_text()
        assert "CONTENT_QUARANTINED" in log_content


class TestQuarantineFile:
    """Test file quarantine functionality."""
    
    def test_quarantine_file_basic(self, tmp_path):
        """Test basic file quarantine."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        entry = quarantine_file(test_file, "Bad file", paths)
        
        assert entry is not None
        assert entry.original_source == str(test_file)
        assert entry.content == "Test content"
    
    def test_quarantine_file_nonexistent(self, tmp_path):
        """Test quarantine of non-existent file."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        nonexistent = tmp_path / "does_not_exist.txt"
        
        entry = quarantine_file(nonexistent, "reason", paths)
        
        assert entry is None
    
    def test_quarantine_file_creates_backup(self, tmp_path):
        """Test that file quarantine creates backup."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")
        
        entry = quarantine_file(test_file, "reason", paths)
        
        # Check backup file exists
        backup_files = list(paths.quarantine_dir.glob(f"{entry.entry_id}_original*"))
        assert len(backup_files) > 0


class TestListQuarantine:
    """Test listing quarantine entries."""
    
    def test_list_quarantine_empty(self, tmp_path):
        """Test listing empty quarantine."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entries = list_quarantine(paths)
        
        assert entries == []
    
    def test_list_quarantine_single_entry(self, tmp_path):
        """Test listing single quarantine entry."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        quarantine_content("Test", "source", "reason", paths)
        
        entries = list_quarantine(paths)
        
        assert len(entries) == 1
        assert entries[0].content == "Test"
    
    def test_list_quarantine_multiple_entries(self, tmp_path):
        """Test listing multiple quarantine entries."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        for i in range(5):
            quarantine_content(f"Content {i}", f"source{i}", "reason", paths)
        
        entries = list_quarantine(paths)
        
        assert len(entries) == 5
    
    def test_list_quarantine_sorted_by_date(self, tmp_path):
        """Test that quarantine list is sorted by date (newest first)."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        # Create entries with slight delays
        import time
        for i in range(3):
            quarantine_content(f"Content {i}", f"source{i}", "reason", paths)
            time.sleep(0.01)
        
        entries = list_quarantine(paths)
        
        # Check dates are descending
        for i in range(len(entries) - 1):
            assert entries[i].quarantined_at >= entries[i + 1].quarantined_at
    
    def test_list_quarantine_parses_metadata(self, tmp_path):
        """Test that list_quarantine correctly parses metadata."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("Test content", "test_source.py", "Malformed", paths)
        
        entries = list_quarantine(paths)
        
        assert len(entries) == 1
        assert entries[0].original_source == "test_source.py"
        assert entries[0].reason == "Malformed"
        assert entries[0].content == "Test content"


class TestRemoveQuarantine:
    """Test quarantine removal."""
    
    def test_remove_quarantine_success(self, tmp_path):
        """Test successful quarantine removal."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("Test", "source", "reason", paths)
        
        result = remove_quarantine(entry.entry_id, paths)
        
        assert result is True
        assert not entry.file_path.exists()
    
    def test_remove_quarantine_nonexistent(self, tmp_path):
        """Test removing non-existent quarantine entry."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        result = remove_quarantine("nonexistent_id", paths)
        
        assert result is False
    
    def test_remove_quarantine_removes_backup(self, tmp_path):
        """Test that removal also removes backup files."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")
        
        entry = quarantine_file(test_file, "reason", paths)
        
        remove_quarantine(entry.entry_id, paths)
        
        # Check no backup files remain
        backup_files = list(paths.quarantine_dir.glob(f"{entry.entry_id}_original*"))
        assert len(backup_files) == 0
    
    def test_remove_quarantine_logs_event(self, tmp_path):
        """Test that remove logs an event."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("Test", "source", "reason", paths)
        
        # Clear log
        paths.aflog_file.write_text("")
        
        remove_quarantine(entry.entry_id, paths)
        
        log_content = paths.aflog_file.read_text()
        assert "QUARANTINE_REMOVED" in log_content


class TestGetQuarantineCount:
    """Test quarantine count functionality."""
    
    def test_get_quarantine_count_zero(self, tmp_path):
        """Test count with no quarantine entries."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        count = get_quarantine_count(paths)
        
        assert count == 0
    
    def test_get_quarantine_count_multiple(self, tmp_path):
        """Test count with multiple entries."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        for i in range(7):
            quarantine_content(f"Content {i}", f"source{i}", "reason", paths)
        
        count = get_quarantine_count(paths)
        
        assert count == 7
    
    def test_get_quarantine_count_no_directory(self, tmp_path):
        """Test count when quarantine directory doesn't exist."""
        paths = get_actifix_paths(project_root=tmp_path)
        # Don't initialize files
        
        count = get_quarantine_count(paths)
        
        assert count == 0




class TestQuarantineEdgeCases:
    """Edge case tests for quarantine system."""
    
    def test_quarantine_empty_content(self, tmp_path):
        """Test quarantining empty content."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        entry = quarantine_content("", "source", "Empty content", paths)
        
        assert entry.content == ""
        assert entry.file_path.exists()
    
    def test_quarantine_large_content(self, tmp_path):
        """Test quarantining large content."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        large_content = "x" * 100000
        entry = quarantine_content(large_content, "source", "Large", paths)
        
        assert entry.content == large_content
        assert entry.file_path.exists()
    
    def test_quarantine_special_characters(self, tmp_path):
        """Test quarantining content with special characters."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        
        special_content = "Test\n\t\r\x00Special™"
        entry = quarantine_content(special_content, "source", "Special", paths)
        
        entries = list_quarantine(paths)
        assert len(entries) == 1
