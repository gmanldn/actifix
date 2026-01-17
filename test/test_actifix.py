"""
Tests for Actifix package.
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestActifixPaths:
    """Tests for state_paths module."""
    
    def test_get_actifix_paths_default(self):
        from actifix.state_paths import get_actifix_paths
        
        paths = get_actifix_paths()
        assert paths.base_dir.name == "actifix"
        assert paths.rollup_file.name == "ACTIFIX.md"
    
    def test_get_actifix_paths_custom(self):
        from actifix.state_paths import get_actifix_paths

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "custom"
            paths = get_actifix_paths(base_dir=base)
            # Compare resolved paths to handle symlink resolution (e.g., /var -> /private/var on macOS)
            assert paths.base_dir == base.resolve()


class TestLogUtils:
    """Tests for log_utils module."""
    
    def test_atomic_write(self):
        from actifix.log_utils import atomic_write
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            atomic_write(path, "Hello, World!")
            assert path.read_text() == "Hello, World!"
    
    def test_trim_to_line_boundary(self):
        from actifix.log_utils import trim_to_line_boundary
        
        content = "line1\nline2\nline3\n"
        # Should not trim if under limit
        result = trim_to_line_boundary(content, 1000)
        assert result == content
        
        # Should trim at line boundary
        result = trim_to_line_boundary(content, 10)
        assert result.endswith("\n")


class TestRaiseAF:
    """Tests for raise_af module."""
    
    def test_generate_ticket_id(self):
        from actifix.raise_af import generate_ticket_id
        
        ticket_id = generate_ticket_id()
        assert ticket_id.startswith("ACT-")
        assert len(ticket_id) == 18  # ACT-YYYYMMDD-XXXXXX
    
    def test_generate_duplicate_guard(self):
        from actifix.raise_af import generate_duplicate_guard
        
        guard = generate_duplicate_guard("test/test_runner.py:10", "error message")
        assert guard.startswith("ACTIFIX-")
        
        # Same input should give same guard
        guard2 = generate_duplicate_guard("test/test_runner.py:10", "error message")
        assert guard == guard2
        
        # Different input should give different guard
        guard3 = generate_duplicate_guard("test/test_runner.py:20", "different error")
        assert guard != guard3
    
    def test_record_error(self, monkeypatch):
        from actifix.raise_af import record_error
        from actifix.state_paths import get_actifix_paths
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "data" / "actifix.db"
            monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
            paths = get_actifix_paths(base_dir=Path(tmpdir) / "actifix")
            
            entry = record_error(
                error_type="TestError",
                message="Test error message",
                source="test_actifix.py:100",
                priority="P2",
                paths=paths,
            )
            
            assert entry is not None
            assert entry.error_type == "TestError"
            assert entry.priority == "P2"
            from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
            from actifix.persistence.database import reset_database_pool

            try:
                repo = get_ticket_repository()
                stored = repo.get_ticket(entry.ticket_id)
                assert stored is not None
                assert stored["message"] == "Test error message"
                assert stored["priority"] == "P2"
                assert os.environ["ACTIFIX_DB_PATH"] == str(db_path)
            finally:
                reset_database_pool()
                reset_ticket_repository()


class TestDoAF:
    """Tests for do_af module."""
    
    def test_get_ticket_stats_empty(self):
        from actifix.do_af import get_ticket_stats
        from actifix.state_paths import get_actifix_paths
        
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = get_actifix_paths(base_dir=Path(tmpdir) / "actifix")
            
            stats = get_ticket_stats(paths)
            assert stats["open"] == 0
            assert stats["completed"] == 0


class TestHealth:
    """Tests for health module."""
    
    def test_get_health(self):
        from actifix.health import get_health
        from actifix.state_paths import get_actifix_paths, init_actifix_files
        
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = get_actifix_paths(base_dir=Path(tmpdir) / "actifix")
            init_actifix_files(paths)
            
            health = get_health(paths)
            assert health.status in ["OK", "WARNING", "ERROR", "SLA_BREACH"]
            assert health.open_tickets == 0


class TestIntegration:
    """Integration tests."""
    
    def test_full_workflow(self):
        from actifix import record_error, get_health
        from actifix.do_af import get_open_tickets, mark_ticket_complete
        from actifix.state_paths import get_actifix_paths
        
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = get_actifix_paths(base_dir=Path(tmpdir) / "actifix")
            
            # Record an error
            entry = record_error(
                error_type="IntegrationError",
                message="Integration test error",
                source="integration.py:50",
                priority="P1",
                paths=paths,
            )
            
            assert entry is not None
            
            # Check health
            health = get_health(paths)
            assert health.open_tickets == 1
            
            # Get open tickets
            tickets = get_open_tickets(paths)
            assert len(tickets) == 1
            assert tickets[0].ticket_id == entry.ticket_id
            
            # Mark complete
            success = mark_ticket_complete(
                entry.ticket_id,
                completion_notes="Fixed critical issue in integration test workflow",
                test_steps="Ran full integration test suite",
                test_results="All integration tests passed successfully",
                summary="Fixed in integration test",
                paths=paths,
            )
            assert success
            
            # Verify completed
            health = get_health(paths)
            assert health.open_tickets == 0
