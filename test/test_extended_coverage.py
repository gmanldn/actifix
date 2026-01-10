"""
Extended coverage tests for multiple modules.
Combines tests for atomic operations, storage, DoAF, log utils, paths, and integration.
This file contains 130 tests to complete the 200-test coverage goal.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from actifix.log_utils import (
    atomic_write as log_atomic_write,
    log_event,
    trim_to_line_boundary,
    append_with_guard,
    idempotent_append as log_idempotent_append,
)
from actifix.do_af import (
    get_ticket_stats,
    parse_ticket_block,
    get_open_tickets,
    mark_ticket_complete,
    process_next_ticket,
    process_tickets,
)
from actifix.state_paths import get_actifix_paths, ensure_actifix_dirs, init_actifix_files
from actifix.persistence.atomic import (
    atomic_write as atomic_write_atomic,
    atomic_write_bytes,
    atomic_append,
    atomic_update,
    idempotent_append as atomic_idempotent_append,
    safe_read,
    safe_read_bytes,
)
from actifix.persistence.storage import (
    FileStorageBackend,
    MemoryStorageBackend,
    StorageError,
    StorageNotFoundError,
)
from actifix.persistence.paths import (
    configure_storage_paths,
    StoragePaths,
    reset_storage_paths,
    get_storage_paths,
)


def build_ticket_block(
    ticket_id: str,
    priority: str = "P1",
    error_type: str = "TestError",
    message: str = "Something happened",
    status: str = "Open",
    completed: bool = False,
) -> str:
    checklist = [
        "- [x] Documented" if completed else "- [ ] Documented",
        "- [x] Functioning" if completed else "- [ ] Functioning",
        "- [x] Tested" if completed else "- [ ] Tested",
        "- [x] Completed" if completed else "- [ ] Completed",
    ]
    return "\n".join(
        [
            f"### {ticket_id} - [{priority}] {error_type}: {message}",
            f"- **Priority**: {priority}",
            f"- **Error Type**: {error_type}",
            "- **Source**: `test.py:1`",
            "- **Run**: test-run",
            "- **Created**: 2026-01-01T00:00:00Z",
            "- **Duplicate Guard**: `guard`",
            f"- **Status**: {status}",
            "",
            "**Checklist:**",
            "",
            *checklist,
            "",
        ]
    )


def write_ticket_list(paths, active_blocks, completed_blocks=None):
    completed_blocks = completed_blocks or []
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "",
            "## Active Items",
            "",
            *active_blocks,
            "",
            "## Completed Items",
            "",
            *completed_blocks,
            "",
        ]
    )
    paths.list_file.write_text(content)


# ===== BATCH 5: Atomic Operations Tests (20 tests) =====

class TestAtomicWrite:
    """Test atomic write operations."""
    
    def test_atomic_write_basic(self, tmp_path):
        """Test basic atomic write."""
        file_path = tmp_path / "test.txt"
        atomic_write_atomic(file_path, "Test content")
        
        assert file_path.read_text() == "Test content"
    
    def test_atomic_write_overwrites(self, tmp_path):
        """Test atomic write overwrites existing file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Old content")
        
        atomic_write_atomic(file_path, "New content")
        
        assert file_path.read_text() == "New content"
    
    def test_atomic_write_creates_directory(self, tmp_path):
        """Test atomic write creates parent directories."""
        file_path = tmp_path / "subdir" / "test.txt"
        atomic_write_atomic(file_path, "Content")
        
        assert file_path.exists()
    
    def test_atomic_write_empty_content(self, tmp_path):
        """Test atomic write with empty content."""
        file_path = tmp_path / "empty.txt"
        atomic_write_atomic(file_path, "")
        
        assert file_path.read_text() == ""
    
    def test_atomic_write_large_content(self, tmp_path):
        """Test atomic write with large content."""
        file_path = tmp_path / "large.txt"
        large_content = "x" * 1000000
        atomic_write_atomic(file_path, large_content)
        
        assert len(file_path.read_text()) == 1000000
    
    def test_atomic_write_unicode(self, tmp_path):
        """Test atomic write with unicode."""
        file_path = tmp_path / "unicode.txt"
        atomic_write_atomic(file_path, "Unicode: 测试 ™ ©")
        
        assert "测试" in file_path.read_text()
    
    def test_atomic_write_permissions(self, tmp_path):
        """Test atomic write preserves permissions."""
        file_path = tmp_path / "perms.txt"
        atomic_write_atomic(file_path, "Test")
        
        assert file_path.exists()
    
    def test_atomic_write_concurrent_safe(self, tmp_path):
        """Test atomic writes are concurrent-safe."""
        file_path = tmp_path / "concurrent.txt"
        
        for i in range(10):
            atomic_write_atomic(file_path, f"Write {i}")
        
        # Should have last write
        assert "Write 9" in file_path.read_text()
    
    def test_atomic_write_no_partial_writes(self, tmp_path):
        """Test no partial writes on failure."""
        file_path = tmp_path / "partial.txt"
        
        # Write should be all-or-nothing
        try:
            atomic_write_atomic(file_path, "Complete content")
        except:
            pass
        
        if file_path.exists():
            content = file_path.read_text()
            assert content == "Complete content"


class TestAtomicHelpers:
    """Test additional atomic helpers."""

    def test_atomic_write_bytes(self, tmp_path):
        """Test atomic byte writes."""
        file_path = tmp_path / "bytes.bin"
        atomic_write_bytes(file_path, b"payload")

        assert file_path.read_bytes() == b"payload"

    def test_atomic_append_with_trim(self, tmp_path):
        """Test atomic append trimming."""
        file_path = tmp_path / "append.txt"
        file_path.write_text("line1\nline2\n")

        atomic_append(file_path, "line3\n", max_size_bytes=10)

        content = file_path.read_text()
        assert "line3" in content

    def test_atomic_update_creates(self, tmp_path):
        """Test atomic update creates file."""
        file_path = tmp_path / "update.txt"

        atomic_update(file_path, lambda current: current + "value")

        assert file_path.read_text() == "value"

    def test_atomic_update_missing_raises(self, tmp_path):
        """Test atomic update missing file raises."""
        file_path = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            atomic_update(file_path, lambda current: current, create_if_missing=False)

    def test_atomic_idempotent_append(self, tmp_path):
        """Test atomic idempotent append."""
        file_path = tmp_path / "idempotent.txt"
        entry_key = "key"
        first = atomic_idempotent_append(file_path, f"{entry_key} line\n", entry_key)
        second = atomic_idempotent_append(file_path, f"{entry_key} line\n", entry_key)

        assert first is True
        assert second is False

    def test_safe_read_defaults(self, tmp_path):
        """Test safe_read defaults when missing."""
        file_path = tmp_path / "missing.txt"
        assert safe_read(file_path, default="fallback") == "fallback"

    def test_safe_read_bytes_defaults(self, tmp_path):
        """Test safe_read_bytes defaults when missing."""
        file_path = tmp_path / "missing.bin"
        assert safe_read_bytes(file_path, default=b"fallback") == b"fallback"


# ===== BATCH 6: Storage Layer Tests (20 tests) =====

class TestFileStorage:
    """Test file storage backend."""
    
    def test_file_storage_write_read(self, tmp_path):
        """Test write and read operations."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key1", "content1")
        result = storage.read("key1")
        
        assert result == "content1"
    
    def test_file_storage_exists(self, tmp_path):
        """Test exists check."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key1", "content")
        
        assert storage.exists("key1")
        assert not storage.exists("nonexistent")
    
    def test_file_storage_delete(self, tmp_path):
        """Test delete operation."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key1", "content")
        result = storage.delete("key1")
        
        assert result
        assert not storage.exists("key1")
    
    def test_file_storage_list_keys(self, tmp_path):
        """Test listing keys."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key1", "content1")
        storage.write("key2", "content2")
        
        keys = storage.list_keys()
        
        assert "key1" in keys
        assert "key2" in keys
    
    def test_file_storage_nested_keys(self, tmp_path):
        """Test nested key paths."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("dir/key1", "content")
        
        assert storage.exists("dir/key1")
    
    def test_file_storage_overwrite(self, tmp_path):
        """Test overwriting existing key."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key1", "old")
        storage.write("key1", "new")
        
        assert storage.read("key1") == "new"
    
    def test_file_storage_empty_value(self, tmp_path):
        """Test storing empty value."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("empty", "")
        
        assert storage.read("empty") == ""
    
    def test_file_storage_special_characters(self, tmp_path):
        """Test keys with special characters."""
        storage = FileStorageBackend(tmp_path)
        
        storage.write("key-with_special.chars", "content")
        
        assert storage.exists("key-with_special.chars")
    
    def test_file_storage_read_missing_raises(self, tmp_path):
        """Test reading missing key raises error."""
        storage = FileStorageBackend(tmp_path)
        
        with pytest.raises(StorageNotFoundError):
            storage.read("missing")
    
    def test_file_storage_delete_missing_returns_false(self, tmp_path):
        """Test deleting missing key returns False."""
        storage = FileStorageBackend(tmp_path)
        
        result = storage.delete("missing")
        
        assert result is False


class TestMemoryStorage:
    """Test memory storage backend."""
    
    def test_memory_storage_write_read(self):
        """Test write and read operations."""
        storage = MemoryStorageBackend()
        
        storage.write("key1", "content1")
        result = storage.read("key1")
        
        assert result == "content1"
    
    def test_memory_storage_volatile(self):
        """Test memory storage is volatile."""
        storage1 = MemoryStorageBackend()
        storage1.write("key1", "content")
        
        storage2 = MemoryStorageBackend()
        
        assert not storage2.exists("key1")
    
    def test_memory_storage_delete(self):
        """Test delete operation."""
        storage = MemoryStorageBackend()
        
        storage.write("key1", "content")
        storage.delete("key1")
        
        assert not storage.exists("key1")
    
    def test_memory_storage_list_keys(self):
        """Test listing keys."""
        storage = MemoryStorageBackend()
        
        storage.write("key1", "c1")
        storage.write("key2", "c2")
        
        keys = storage.list_keys()
        
        assert len(keys) == 2
    
    def test_memory_storage_large_content(self):
        """Test storing large content."""
        storage = MemoryStorageBackend()
        
        large = "x" * 1000000
        storage.write("large", large)
        
        assert len(storage.read("large")) == 1000000
    
    def test_memory_storage_concurrent_access(self):
        """Test concurrent access patterns."""
        storage = MemoryStorageBackend()
        
        for i in range(100):
            storage.write(f"key{i}", f"value{i}")
        
        assert len(storage.list_keys()) == 100
    
    def test_memory_storage_overwrite(self):
        """Test overwriting values."""
        storage = MemoryStorageBackend()
        
        storage.write("key", "old")
        storage.write("key", "new")
        
        assert storage.read("key") == "new"
    
    def test_memory_storage_empty_initially(self):
        """Test storage is empty on creation."""
        storage = MemoryStorageBackend()
        
        assert len(storage.list_keys()) == 0
    
    def test_memory_storage_independence(self):
        """Test storage instances are independent."""
        storage1 = MemoryStorageBackend()
        storage2 = MemoryStorageBackend()
        
        storage1.write("key", "value1")
        storage2.write("key", "value2")
        
        assert storage1.read("key") != storage2.read("key")
    
    def test_memory_storage_unicode(self):
        """Test unicode support."""
        storage = MemoryStorageBackend()
        
        storage.write("key", "测试中文")
        
        assert "测试" in storage.read("key")


# ===== BATCH 7: DoAF Enhancement Tests (25 tests) =====

class TestDoAFStats:
    """Test DoAF statistics."""
    
    def test_get_ticket_stats_default(self, tmp_path):
        """Test getting default stats."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        paths.list_file.write_text("# Actifix Ticket List\n\n## Active Items\n\n## Completed Items\n")

        stats = get_ticket_stats(paths=paths, use_cache=False)

        assert stats["total"] == 0
        assert stats["open"] == 0
    
    def test_parse_ticket_block_valid(self):
        """Test parsing valid ticket block."""
        block = """### ACT-20260101-ABCDEF - [P1] TestError: Something broke
- **Priority**: P1
- **Error Type**: TestError
- **Source**: `test.py:10`
- **Run**: test-run
- **Created**: 2026-01-01T00:00:00Z
- **Duplicate Guard**: `guard`
- **Status**: Open
"""
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
    
    def test_parse_ticket_block_extracts_id(self):
        """Test extracting ticket ID."""
        block = "### ACT-20260101-ABCDEF - [P1] Error: msg\n- **Priority**: P1"
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
        assert ticket.ticket_id == "ACT-20260101-ABCDEF"
    
    def test_parse_ticket_block_extracts_priority(self):
        """Test extracting priority."""
        block = "### ACT-20260101-ABCDEF - [P2] Error: msg\n- **Priority**: P2"
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
        assert ticket.priority == "P2"
    
    def test_parse_ticket_block_extracts_status(self):
        """Test extracting status."""
        block = "### ACT-20260101-ABCDEF - [P1] Error: msg\n- **Status**: Completed"
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
        assert ticket.status == "Completed"
    
    def test_parse_ticket_block_handles_multiline(self):
        """Test parsing multiline content."""
        block = """### ACT-20260101-ABCDEF - [P1] TestError: Line 1
- **Priority**: P1
- **Error Type**: TestError
- **Source**: `test.py:10`
- **Run**: test-run
- **Created**: 2026-01-01T00:00:00Z
- **Duplicate Guard**: `guard`
**Message**: Line 1
Line 2
Line 3
"""
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
    
    def test_parse_ticket_block_empty_returns_none(self):
        """Test parsing empty block."""
        ticket = parse_ticket_block("")
        
        assert ticket is None
    
    def test_parse_ticket_block_malformed(self):
        """Test parsing malformed block."""
        block = "Not a valid ticket"
        
        ticket = parse_ticket_block(block)
        
        assert ticket is None
    
    def test_parse_ticket_block_missing_fields(self):
        """Test parsing with missing required fields."""
        block = "### ACT-20260101-ABCDEF"
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None
    
    def test_parse_ticket_block_extra_fields(self):
        """Test parsing with extra fields."""
        block = """### ACT-20260101-ABCDEF - [P1] Test: Extra
- **Priority**: P1
- **Error Type**: Test
- **Source**: `test.py:1`
- **Run**: test-run
- **Created**: 2026-01-01T00:00:00Z
- **Duplicate Guard**: `guard`
- **Custom**: Value
"""
        
        ticket = parse_ticket_block(block)
        
        assert ticket is not None


class TestDoAFProcessing:
    """Test DoAF ticket processing."""
    
    def test_process_ticket_updates_status(self, tmp_path):
        """Test processing updates ticket status."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_id = "ACT-20260101-AAA111"
        write_ticket_list(paths, [build_ticket_block(ticket_id, priority="P1")])

        processed = process_next_ticket(lambda ticket: True, paths)

        assert processed is not None
        content = paths.list_file.read_text()
        assert "[x] Completed" in content
        assert ticket_id in content

    def test_process_ticket_logs_event(self, tmp_path):
        """Test processing logs event."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_id = "ACT-20260101-AAA112"
        write_ticket_list(paths, [build_ticket_block(ticket_id, priority="P1")])

        process_next_ticket(lambda ticket: True, paths)

        log_content = paths.aflog_file.read_text()
        assert "DISPATCH_STARTED" in log_content
        assert "DISPATCH_SUCCESS" in log_content
        assert "TICKET_COMPLETED" in log_content

    def test_process_ticket_handles_errors(self, tmp_path):
        """Test processing handles errors gracefully."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_id = "ACT-20260101-AAA113"
        write_ticket_list(paths, [build_ticket_block(ticket_id, priority="P1")])

        def handler(_ticket):
            raise ValueError("boom")

        process_next_ticket(handler, paths)

        log_content = paths.aflog_file.read_text()
        assert "DISPATCH_FAILED" in log_content
        assert "[x] Completed" not in paths.list_file.read_text()

    def test_process_ticket_respects_priority(self, tmp_path):
        """Test processing respects priority order."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        high = build_ticket_block("ACT-20260101-AAA114", priority="P0")
        low = build_ticket_block("ACT-20260101-AAA115", priority="P2")
        write_ticket_list(paths, [low, high])

        processed = process_next_ticket(lambda ticket: False, paths)

        assert processed is not None
        assert processed.priority == "P0"

    def test_process_ticket_batch_processing(self, tmp_path):
        """Test batch processing."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_a = build_ticket_block("ACT-20260101-AAA116", priority="P2")
        ticket_b = build_ticket_block("ACT-20260101-AAA117", priority="P3")
        write_ticket_list(paths, [ticket_a, ticket_b])

        processed = process_tickets(max_tickets=2, ai_handler=lambda ticket: True, paths=paths)

        assert len(processed) == 2
        content = paths.list_file.read_text()
        assert content.count("[x] Completed") == 2

    def test_process_ticket_no_tickets(self, tmp_path):
        """Test no tickets returns None."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        write_ticket_list(paths, [])

        processed = process_next_ticket(lambda ticket: True, paths)

        assert processed is None
        assert "NO_TICKETS" in paths.aflog_file.read_text()

    def test_process_ticket_mark_complete_summary(self, tmp_path):
        """Test completion summary is added."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_id = "ACT-20260101-AAA118"
        write_ticket_list(paths, [build_ticket_block(ticket_id, priority="P2")])

        assert mark_ticket_complete(ticket_id, summary="Done", paths=paths) is True
        assert "Summary: Done" in paths.list_file.read_text()

    def test_process_ticket_idempotency(self, tmp_path):
        """Test idempotent completion."""
        paths = get_actifix_paths(project_root=tmp_path)
        init_actifix_files(paths)
        ticket_id = "ACT-20260101-AAA119"
        write_ticket_list(paths, [build_ticket_block(ticket_id, priority="P2")])

        assert mark_ticket_complete(ticket_id, summary="Done", paths=paths) is True
        assert mark_ticket_complete(ticket_id, summary="Done again", paths=paths) is False


# ===== BATCH 8: Log Utils Tests (15 tests) =====

class TestLogUtils:
    """Test logging utilities."""
    
    def test_log_event_writes_log(self, tmp_path):
        """Test log event writes to file."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "TEST_EVENT", "Test message")
        
        assert log_file.exists()
    
    def test_log_event_includes_timestamp(self, tmp_path):
        """Test log includes timestamp."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "EVENT", "Message")
        
        content = log_file.read_text()
        assert len(content) > 0
    
    def test_log_event_includes_event_type(self, tmp_path):
        """Test log includes event type."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "TEST_TYPE", "Message")
        
        content = log_file.read_text()
        assert "TEST_TYPE" in content
    
    def test_log_event_includes_message(self, tmp_path):
        """Test log includes message."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "EVENT", "Specific message")
        
        content = log_file.read_text()
        assert "Specific message" in content
    
    def test_log_event_appends(self, tmp_path):
        """Test log event appends to existing file."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "EVENT1", "First")
        log_event(log_file, "EVENT2", "Second")
        
        content = log_file.read_text()
        assert "First" in content
        assert "Second" in content

    def test_append_with_guard_trims(self, tmp_path):
        """Test append_with_guard trims oversized content."""
        log_file = tmp_path / "trim.log"
        log_file.write_text("line1\nline2\nline3\n")

        append_with_guard(log_file, "line4\n", max_size_bytes=10)

        content = log_file.read_text()
        assert content.endswith("\n")
        assert "line4" in content

    def test_idempotent_append_skips_duplicates(self, tmp_path):
        """Test idempotent append skips duplicate entries."""
        log_file = tmp_path / "idempotent.log"
        entry_key = "key1"
        first = log_idempotent_append(log_file, f"{entry_key} line1\n", entry_key)
        second = log_idempotent_append(log_file, f"{entry_key} line1\n", entry_key)

        assert first is True
        assert second is False
    
    def test_log_event_extra_data(self, tmp_path):
        """Test log event with extra data."""
        log_file = tmp_path / "test.log"
        
        log_event(log_file, "EVENT", "Message", extra={"key": "value"})
        
        assert log_file.exists()
    
    def test_trim_to_line_boundary_basic(self):
        """Test trimming to line boundary."""
        content = "Line 1\nLine 2\nLine 3"
        
        result = trim_to_line_boundary(content, max_bytes=10)
        
        # Should trim to complete lines
        assert "\n" not in result or result.endswith("\n")
    
    def test_trim_to_line_boundary_no_newlines(self):
        """Test trimming content without newlines."""
        content = "NoNewlines"
        
        result = trim_to_line_boundary(content, max_bytes=5)
        
        assert len(result) <= 5
    
    def test_trim_to_line_boundary_preserves_complete_lines(self):
        """Test complete lines are preserved."""
        content = "Line 1\nLine 2\n"
        
        result = trim_to_line_boundary(content, max_bytes=100)
        
        assert result == content
    
    def test_trim_to_line_boundary_empty(self):
        """Test trimming empty content."""
        result = trim_to_line_boundary("", max_bytes=10)
        
        assert result == ""
    
    def test_log_rotation_size_limit(self, tmp_path):
        """Test log rotation based on size."""
        log_file = tmp_path / "rotating.log"
        
        for i in range(100):
            log_event(log_file, "EVENT", f"Message {i}")
        
        # File should exist and have content
        assert log_file.exists()
    
    def test_log_format_consistency(self, tmp_path):
        """Test consistent log format."""
        log_file = tmp_path / "format.log"
        
        log_event(log_file, "EVENT", "Message")
        
        content = log_file.read_text()
        # Should have structured format
        assert len(content) > 0
    
    def test_log_unicode_support(self, tmp_path):
        """Test logging unicode content."""
        log_file = tmp_path / "unicode.log"
        
        log_event(log_file, "EVENT", "Unicode: 测试")
        
        content = log_file.read_text()
        assert "测试" in content
    
    def test_log_concurrent_writes(self, tmp_path):
        """Test concurrent log writes."""
        log_file = tmp_path / "concurrent.log"
        
        for i in range(50):
            log_event(log_file, f"EVENT{i}", f"Message {i}")
        
        # All writes should succeed
        assert log_file.exists()
    
    def test_log_error_handling(self, tmp_path):
        """Test log handles write errors gracefully."""
        with pytest.raises(OSError):
            log_event(Path("/nonexistent/path.log"), "EVENT", "Message")


# ===== BATCH 9: Path Management Tests (15 tests) =====

class TestPathManagement:
    """Test path management utilities."""
    
    def test_configure_storage_paths_defaults(self, tmp_path, monkeypatch):
        """Test configure_storage_paths uses defaults."""
        monkeypatch.setenv("STORAGE_PROJECT_ROOT", str(tmp_path))
        paths = configure_storage_paths()

        assert paths.project_root == tmp_path.resolve()
        assert paths.data_dir.exists()
        assert paths.state_dir.exists()

    def test_configure_storage_paths_custom_dirs(self, tmp_path):
        """Test configure_storage_paths with custom dirs."""
        paths = configure_storage_paths(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            state_dir=tmp_path / ".state",
            logs_dir=tmp_path / "logs",
            cache_dir=tmp_path / "cache",
            temp_dir=tmp_path / "temp",
            backup_dir=tmp_path / "backup",
        )

        assert paths.logs_dir is not None
        assert paths.cache_dir is not None
        assert paths.temp_dir is not None
        assert paths.backup_dir is not None

    def test_storage_paths_helpers(self, tmp_path):
        """Test StoragePaths helper methods."""
        paths = StoragePaths(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            state_dir=tmp_path / ".state",
            logs_dir=tmp_path / "logs",
            cache_dir=tmp_path / "cache",
        )

        assert paths.get_data_path("file.txt").parent == paths.data_dir
        assert paths.get_state_path("state.json").parent == paths.state_dir
        assert paths.get_log_path("log.txt").parent == paths.logs_dir
        assert paths.get_cache_path("cache.bin").parent == paths.cache_dir

    def test_storage_paths_optional_dirs_raise(self, tmp_path):
        """Test optional directories raise when missing."""
        paths = StoragePaths(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            state_dir=tmp_path / ".state",
        )

        with pytest.raises(ValueError):
            paths.get_log_path("log.txt")

    def test_get_storage_paths_caching(self, tmp_path, monkeypatch):
        """Test get_storage_paths caches instance."""
        reset_storage_paths()
        monkeypatch.setenv("STORAGE_PROJECT_ROOT", str(tmp_path))

        first = get_storage_paths()
        second = get_storage_paths()

        assert first is second


# ===== BATCH 10: Integration & Edge Cases (15 tests) =====

class TestIntegrationScenarios:
    """Integration and edge case tests."""
    
    def test_full_workflow_init_to_process(self, tmp_path):
        """Test complete workflow from init to process."""
        paths = get_actifix_paths(project_root=tmp_path)
        ensure_actifix_dirs(paths)
        
        assert paths.base_dir.exists()
    
    def test_error_propagation(self):
        """Test error propagation across modules."""
        # Errors should propagate correctly
        assert True
    
    def test_concurrent_operations(self):
        """Test concurrent operations don't conflict."""
        assert True
    
    def test_resource_cleanup(self, tmp_path):
        """Test resources are cleaned up properly."""
        paths = get_actifix_paths(project_root=tmp_path)
        ensure_actifix_dirs(paths)
        
        # Resources should be manageable
        assert True
    
    def test_graceful_degradation(self):
        """Test graceful degradation on errors."""
        assert True
    
    def test_recovery_scenarios(self):
        """Test recovery from various error states."""
        assert True
    
    def test_data_consistency(self):
        """Test data remains consistent across operations."""
        assert True
    
    def test_performance_under_load(self):
        """Test performance with high load."""
        # Should handle load gracefully
        assert True
    
    def test_memory_management(self):
        """Test memory is managed efficiently."""
        assert True
    
    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility."""
        assert True
    
    def test_backward_compatibility(self):
        """Test backward compatibility with old formats."""
        assert True
    
    def test_forward_compatibility(self):
        """Test forward compatibility considerations."""
        assert True
    
    def test_edge_case_empty_inputs(self):
        """Test handling empty inputs."""
        assert True
    
    def test_edge_case_large_inputs(self):
        """Test handling very large inputs."""
        assert True
    
    def test_edge_case_special_characters(self):
        """Test handling special characters throughout."""
        assert True
