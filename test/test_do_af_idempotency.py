"""
Test DoAF idempotency guard to prevent double-completing tickets.

Tests that mark_ticket_complete() skips already-completed tickets
and logs the skip event to AFLog.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path so we can import actifix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.do_af import mark_ticket_complete
from actifix.state_paths import ActifixPaths


@pytest.fixture
def temp_actifix_paths():
    """Create temporary Actifix paths for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        state_dir = base / ".actifix"
        state_dir.mkdir()
        
        paths = ActifixPaths(
            project_root=base,
            base_dir=base / "actifix",
            state_dir=state_dir,
            logs_dir=base / "logs",
            list_file=base / "actifix" / "ACTIFIX-LIST.md",
            rollup_file=base / "actifix" / "ACTIFIX.md",
            log_file=base / "actifix" / "ACTIFIX-LOG.md",
            aflog_file=base / "actifix" / "AFLog.txt",
            fallback_queue_file=state_dir / "actifix_fallback_queue.json",
            quarantine_dir=state_dir / "quarantine",
            test_logs_dir=state_dir / "test_logs",
        )
        
        # Create directories
        paths.base_dir.mkdir(parents=True, exist_ok=True)
        paths.logs_dir.mkdir(parents=True, exist_ok=True)
        
        yield paths


def test_idempotency_guard_prevents_double_completion(temp_actifix_paths):
    """Test that mark_ticket_complete skips already-completed tickets."""
    paths = temp_actifix_paths
    
    # Create initial ACTIFIX-LIST.md with a test ticket
    list_content = """# Actifix Ticket List

## Active Items

### ACT-20260101-TEST123 - [P3] Test Ticket

- **Priority**: P3
- **Error Type**: TestError
- **Source**: `test.py:50`
- **Run**: test-run
- **Created**: 2026-01-10T12:00:00Z
- **Duplicate Guard**: `TEST-test-py:50-abcd1234`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

## Completed Items

"""
    
    paths.list_file.write_text(list_content)
    paths.aflog_file.write_text("")
    
    # First call: mark as complete (should succeed)
    result1 = mark_ticket_complete(
        "ACT-20260101-TEST123",
        summary="Fixed successfully",
        paths=paths
    )
    assert result1 is True, "First mark_ticket_complete should return True"
    
    # Verify it was marked complete
    content = paths.list_file.read_text()
    assert "[x] Completed" in content, "Ticket should be marked completed"
    
    # Second call: try to mark as complete again (should be skipped by idempotency guard)
    result2 = mark_ticket_complete(
        "ACT-20260101-TEST123",
        summary="Already fixed",
        paths=paths
    )
    assert result2 is False, "Second mark_ticket_complete should return False (idempotency guard)"
    
    # Verify AFLog has skip event
    aflog_content = paths.aflog_file.read_text()
    assert "TICKET_ALREADY_COMPLETED" in aflog_content, "AFLog should have skip event"
    assert "idempotency_guard" in aflog_content, "AFLog should mention idempotency guard"


def test_idempotency_guard_logs_skip_event(temp_actifix_paths):
    """Test that idempotency guard logs skip event to AFLog."""
    paths = temp_actifix_paths
    
    # Create a ticket that's already completed
    list_content = """# Actifix Ticket List

## Active Items

### ACT-20260101-DONE456 - [P2] Already Done Ticket

- **Priority**: P2
- **Error Type**: TestError
- **Source**: `done.py:100`
- **Run**: test-run
- **Created**: 2026-01-10T12:00:00Z
- **Duplicate Guard**: `TEST-done-py:100-efgh5678`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

## Completed Items

"""
    
    paths.list_file.write_text(list_content)
    paths.aflog_file.write_text("Previous events\n")
    
    # Try to mark as complete
    result = mark_ticket_complete(
        "ACT-20260101-DONE456",
        summary="Trying to mark already-complete",
        paths=paths
    )
    assert result is False, "Should return False for already-completed ticket"
    
    # Verify skip event was logged
    aflog_content = paths.aflog_file.read_text()
    assert "TICKET_ALREADY_COMPLETED" in aflog_content
    assert "ACT-20260101-DONE456" in aflog_content
    assert "Skipped already-completed ticket" in aflog_content


def test_normal_completion_still_works(temp_actifix_paths):
    """Test that normal ticket completion still works correctly."""
    paths = temp_actifix_paths
    
    # Create initial list
    list_content = """# Actifix Ticket List

## Active Items

### ACT-20260101-NORMAL789 - [P1] Normal Ticket

- **Priority**: P1
- **Error Type**: TestError
- **Source**: `normal.py:25`
- **Run**: test-run
- **Created**: 2026-01-10T12:00:00Z
- **Duplicate Guard**: `TEST-normal-py:25-ijkl9012`

**Checklist:**

- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

## Completed Items

"""
    
    paths.list_file.write_text(list_content)
    paths.aflog_file.write_text("")
    
    # Mark as complete
    result = mark_ticket_complete(
        "ACT-20260101-NORMAL789",
        summary="Fixed normally",
        paths=paths
    )
    assert result is True, "Normal completion should succeed"
    
    # Verify all checkboxes were updated
    content = paths.list_file.read_text()
    assert "[x] Documented" in content
    assert "[x] Functioning" in content
    assert "[x] Tested" in content
    assert "[x] Completed" in content
    
    # Verify completion event was logged
    aflog_content = paths.aflog_file.read_text()
    assert "TICKET_COMPLETED" in aflog_content
    assert "ACT-20260101-NORMAL789" in aflog_content
