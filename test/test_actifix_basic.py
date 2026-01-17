#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic tests for the generic Actifix framework.

This test file itself will be tracked by actifix during development!
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
import os
import sys

# Add src to path so we can import actifix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import actifix


@pytest.fixture
def temp_actifix_dir(monkeypatch):
    """Create temporary ACTIFIX directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    actifix_dir = temp_dir / "actifix"
    
    # Enable Actifix capture for tests
    monkeypatch.setenv(actifix.ACTIFIX_CAPTURE_ENV_VAR, "1")
    
    # Override the default directories
    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(actifix_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(temp_dir / ".actifix"))
    db_path = temp_dir / "data" / "actifix.db"
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_path))
    
    yield actifix_dir
    
    # Cleanup
    monkeypatch.delenv(actifix.ACTIFIX_CAPTURE_ENV_VAR, raising=False)
    monkeypatch.delenv("ACTIFIX_DATA_DIR", raising=False)
    monkeypatch.delenv("ACTIFIX_STATE_DIR", raising=False)
    monkeypatch.delenv("ACTIFIX_DB_PATH", raising=False)
    
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestActifixBasic:
    """Test basic Actifix functionality."""
    
    def test_bootstrap_creates_directories(self, temp_actifix_dir, monkeypatch, capsys):
        """Test that bootstrap creates necessary directories and files."""
        # Redirect print output
        actifix.bootstrap_actifix_development()
        
        # Check directories were created
        assert temp_actifix_dir.exists()
        
        # Check output
        captured = capsys.readouterr()
        assert "Bootstrapping self-development mode" in captured.out
        assert "Self-development mode active" in captured.out
    
    def test_record_error_creates_ticket(self, temp_actifix_dir, monkeypatch):
        """Test that recording an error creates a ticket."""
        # Enable capture
        actifix.enable_actifix_capture()
        
        # Record an error
        entry = actifix.record_error(
            message="Test error for actifix development",
            source="test_actifix_basic.py:test_record_error_creates_ticket", 
            run_label="actifix-testing",
            error_type="TestError",
            capture_context=False  # Skip for speed
        )
        
        assert entry is not None
        assert entry.entry_id.startswith("ACT-")
        assert entry.error_type == "TestError"
        assert entry.message == "Test error for actifix development"
        assert entry.priority == actifix.TicketPriority.P2  # Default priority
        
        # Check files and database were created
        db_path = temp_actifix_dir.parent / "data" / "actifix.db"
        assert (temp_actifix_dir / "ACTIFIX.md").exists()
        assert db_path.exists(), "Database file should exist for ticket storage"

        # Check database content
        from actifix.persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        stored = repo.get_ticket(entry.entry_id)
        assert stored is not None
        assert stored["message"] == "Test error for actifix development"
        
        rollup_content = (temp_actifix_dir / "ACTIFIX.md").read_text()
        assert entry.entry_id in rollup_content
    
    def test_duplicate_prevention(self, temp_actifix_dir, monkeypatch):
        """Test that duplicate errors are prevented."""
        actifix.enable_actifix_capture()
        
        # Record first error
        entry1 = actifix.record_error(
            message="Duplicate test error",
            source="test_module.py:42",
            run_label="test",
            error_type="DuplicateError",
            capture_context=False
        )
        
        assert entry1 is not None
        
        # Record same error again - should be blocked
        entry2 = actifix.record_error(
            message="Duplicate test error", 
            source="test_module.py:42",
            run_label="test",
            error_type="DuplicateError", 
            capture_context=False
        )
        
        assert entry2 is None  # Duplicate should be blocked
    
    def test_priority_classification(self, temp_actifix_dir, monkeypatch):
        """Test automatic priority classification."""
        actifix.enable_actifix_capture()
        
        # Test P0 (critical) 
        entry_p0 = actifix.record_error(
            message="System crash detected",
            source="core.py",
            run_label="test",
            error_type="FatalError",
            capture_context=False
        )
        assert entry_p0.priority == actifix.TicketPriority.P0
        
        # Test P1 (high)
        entry_p1 = actifix.record_error(
            message="Database connection failed",
            source="main.py", 
            run_label="test",
            error_type="DatabaseError",
            capture_context=False
        )
        assert entry_p1.priority == actifix.TicketPriority.P1
        
        # Test P3 (low)
        entry_p3 = actifix.record_error(
            message="Deprecated function used",
            source="utils.py",
            run_label="test", 
            error_type="DeprecationWarning",
            capture_context=False
        )
        assert entry_p3.priority == actifix.TicketPriority.P3
    
    def test_secret_redaction(self, temp_actifix_dir, monkeypatch):
        """Test that secrets are redacted from error messages."""
        from actifix.raise_af import redact_secrets_from_text
        
        # Test API key redaction
        text_with_secret = "Error connecting with API key sk-1234567890abcdef"
        redacted = redact_secrets_from_text(text_with_secret)
        assert "sk-1234567890abcdef" not in redacted
        assert "***API_KEY_REDACTED***" in redacted
        
        # Test password redaction  
        text_with_password = "Failed login with password=secretpassword123"
        redacted = redact_secrets_from_text(text_with_password)
        assert "secretpassword123" not in redacted
        assert "***REDACTED***" in redacted
    
    def test_capture_disabled_when_env_var_not_set(self, temp_actifix_dir, monkeypatch):
        """Test that capture is disabled when environment variable is not set."""
        # Ensure capture is disabled
        actifix.disable_actifix_capture()
        
        # Try to record error
        entry = actifix.record_error(
            message="This should not be recorded",
            source="test/test_runner.py",
            run_label="test",
            error_type="TestError"
        )
        
        assert entry is None  # Should not be recorded
        
        # Files should not be created
        assert not (temp_actifix_dir / "ACTIFIX.md").exists()
    
    def test_ensure_scaffold_creates_all_files(self, temp_actifix_dir):
        """Test that scaffold creates all required files."""
        actifix.ensure_scaffold(temp_actifix_dir)
        
        required_files = [
            "ACTIFIX.md",
            "ACTIFIX-LOG.md",
            "AFLog.txt"
        ]
        
        for filename in required_files:
            assert (temp_actifix_dir / filename).exists(), f"Missing: {filename}"
    
    def test_fallback_queue_when_db_unavailable(self, temp_actifix_dir, monkeypatch):
        """Test fallback queue when database writes fail."""
        from actifix.raise_af import record_error
        from actifix.persistence import ticket_repo
        
        state_dir = temp_actifix_dir / ".actifix_state"
        monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))

        def _raise_db():
            raise RuntimeError("db down")

        monkeypatch.setattr(ticket_repo, "get_ticket_repository", _raise_db)

        actifix.enable_actifix_capture()
        entry = record_error(
            message="Test fallback error",
            source="fallback_test.py",
            run_label="fallback-run",
            error_type="TestError",
            capture_context=False,
        )
        assert entry is not None

        queue_file = state_dir / "actifix_fallback_queue.json"
        assert queue_file.exists(), f"Missing fallback queue at {queue_file}"

        queue_content = json.loads(queue_file.read_text(encoding="utf-8"))
        assert any(item.get("entry_id") == entry.entry_id for item in queue_content)


class TestActifixSelfDevelopment:
    """Test actifix's self-development capabilities."""
    
    def test_track_development_progress(self, temp_actifix_dir, monkeypatch):
        """Test tracking development milestones."""
        actifix.enable_actifix_capture()
        
        # Track a development milestone
        actifix.track_development_progress(
            "Core error capture implemented",
            "RaiseAF.py completed with full context capture"
        )
        
        # Check that milestone was recorded
        from actifix.persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        tickets = repo.get_tickets()
        assert any("Development milestone" in ticket["message"] for ticket in tickets)
    
    def test_exception_handler_captures_errors(self, temp_actifix_dir, monkeypatch, capsys):
        """Test that the exception handler captures development errors."""
        import sys
        
        actifix.enable_actifix_capture()
        
        # Install exception handler
        original_handler = actifix.install_exception_handler()
        
        try:
            # Trigger an exception (but catch it so test doesn't fail)
            try:
                raise ValueError("Test exception for development tracking")
            except ValueError:
                # Manually call the exception handler
                import traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()
                actifix.capture_exception(exc_type, exc_value, exc_traceback)
            
            # Check that error was captured
            captured = capsys.readouterr()
            assert "Captured development error" in captured.out
            
            # Check files were created
            from actifix.persistence.ticket_repo import get_ticket_repository
            repo = get_ticket_repository()
            tickets = repo.get_tickets()
            assert any("Test exception for development tracking" in ticket["message"] for ticket in tickets)
            
        finally:
            # Restore original handler
            actifix.uninstall_exception_handler(original_handler)


def test_actifix_self_improvement():
    """
    Test that demonstrates actifix improving itself!
    
    This test intentionally creates an error to show how actifix
    can track issues in its own development.
    """
    # Enable actifix to track its own development
    actifix.bootstrap_actifix_development()
    
    # Create a development ticket for improving this test
    actifix.track_development_progress(
        "Basic test suite created",
        "Created comprehensive tests for core error capture functionality. "
        "Next: implement DoAF for ticket processing."
    )
    
    print("\n=== Actifix Self-Improvement Demo ===")
    print("Actifix has just tracked its own development progress!")
    print("Check the actifix/ directory to see the generated tickets.")
    print("This is the beginning of a self-improving system!")


if __name__ == "__main__":
    # Run the self-improvement demo
    test_actifix_self_improvement()
