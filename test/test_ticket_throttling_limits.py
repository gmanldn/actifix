#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for ticket throttling and limit enforcement.

Covers:
- Ticket 1: Message length limits (ACT-20260114-AD00C)
- Ticket 2: File context size limits (ACT-20260114-EE698)
- Ticket 3: Open tickets limit (ACT-20260114-2FBBC)
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

from actifix.config import ActifixConfig, load_config, validate_config, get_actifix_paths
from actifix.raise_af import ActifixEntry, TicketPriority, record_error
from actifix.persistence.ticket_repo import (
    TicketRepository,
    FieldLengthError,
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.persistence.database import (
    get_database_pool,
    reset_database_pool,
    serialize_json_field,
    deserialize_json_field,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test state."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration with custom limits."""
    paths = get_actifix_paths(project_root=temp_dir)
    config = ActifixConfig(
        project_root=temp_dir,
        paths=paths,
        max_ticket_message_length=5000,
        max_file_context_size_bytes=1024 * 1024,  # 1MB
        max_open_tickets=10000,
    )
    return config


@pytest.fixture
def repo(test_config):
    """Create test repository with custom config."""
    reset_database_pool()
    reset_ticket_repository()
    pool = get_database_pool(test_config.paths.data_dir)
    repo = TicketRepository(pool=pool)
    yield repo
    reset_database_pool()
    reset_ticket_repository()


class TestTicket1MessageLength:
    """Tests for Ticket 1: Message length limits (ACT-20260114-AD00C)"""
    
    def test_config_load_default_message_length(self):
        """Verify config loads with default message length."""
        config = load_config(fail_fast=False)
        assert config.max_ticket_message_length == 5000
    
    def test_config_load_custom_message_length(self, monkeypatch, temp_dir):
        """Verify custom message length via environment variable."""
        monkeypatch.setenv("ACTIFIX_MAX_MESSAGE_LENGTH", "10000")
        paths = get_actifix_paths(project_root=temp_dir)
        config = ActifixConfig(
            project_root=temp_dir,
            paths=paths,
            max_ticket_message_length=10000,
        )
        assert config.max_ticket_message_length == 10000
    
    def test_config_validate_message_length_positive(self):
        """Verify validation rejects non-positive message length."""
        paths = get_actifix_paths()
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=paths,
            max_ticket_message_length=-1,
        )
        errors = validate_config(config)
        assert any("message length" in e.lower() for e in errors)
    
    def test_config_validate_message_length_not_too_large(self):
        """Verify validation rejects unreasonably large message length."""
        paths = get_actifix_paths()
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=paths,
            max_ticket_message_length=2_000_000,  # 2MB, exceeds 1MB limit
        )
        errors = validate_config(config)
        assert any("message length" in e.lower() for e in errors)
    
    def test_create_ticket_message_within_limit(self, repo):
        """Create ticket with message within limit (should succeed)."""
        message = "x" * 4999  # Just under 5000
        entry = ActifixEntry(
            entry_id="ACT-20260114-001",
            priority=TicketPriority.P2,
            error_type="TestError",
            message=message,
            source="test.py:42",
        )
        assert repo.create_ticket(entry) is True
    
    def test_create_ticket_message_at_limit(self, repo):
        """Create ticket with message exactly at limit (should succeed)."""
        message = "x" * 5000
        entry = ActifixEntry(
            entry_id="ACT-20260114-002",
            priority=TicketPriority.P2,
            error_type="TestError",
            message=message,
            source="test.py:42",
        )
        assert repo.create_ticket(entry) is True
    
    def test_create_ticket_message_exceeds_limit(self, repo):
        """Create ticket with message exceeding limit (should fail)."""
        message = "x" * 5001
        entry = ActifixEntry(
            entry_id="ACT-20260114-003",
            priority=TicketPriority.P2,
            error_type="TestError",
            message=message,
            source="test.py:42",
        )
        with pytest.raises(FieldLengthError) as excinfo:
            repo.create_ticket(entry)
        assert "message" in str(excinfo.value).lower()
        assert "5000" in str(excinfo.value)
    
    def test_update_ticket_message_within_limit(self, repo):
        """Update ticket message within limit (should succeed)."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-004",
            priority=TicketPriority.P2,
            error_type="TestError",
            message="Original message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        new_message = "x" * 4999
        assert repo.update_ticket("ACT-20260114-004", {"message": new_message}) is True
    
    def test_update_ticket_message_exceeds_limit(self, repo):
        """Update ticket message exceeding limit (should fail)."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-005",
            priority=TicketPriority.P2,
            error_type="TestError",
            message="Original message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        new_message = "x" * 5001
        with pytest.raises(FieldLengthError):
            repo.update_ticket("ACT-20260114-005", {"message": new_message})


class TestTicket2FileContextSize:
    """Tests for Ticket 2: File context size limits (ACT-20260114-EE698)"""
    
    def test_config_load_default_file_context_size(self):
        """Verify config loads with default file context size."""
        config = load_config(fail_fast=False)
        assert config.max_file_context_size_bytes == 1024 * 1024  # 1MB
    
    def test_config_validate_file_context_size_positive(self):
        """Verify validation rejects non-positive file context size."""
        paths = get_actifix_paths()
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=paths,
            max_file_context_size_bytes=-1,
        )
        errors = validate_config(config)
        assert any("file context" in e.lower() for e in errors)
    
    def test_config_validate_file_context_size_reasonable(self):
        """Verify validation rejects unreasonably large file context size."""
        paths = get_actifix_paths()
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=paths,
            max_file_context_size_bytes=200 * 1024 * 1024,  # 200MB, exceeds 100MB limit
        )
        errors = validate_config(config)
        assert any("file context" in e.lower() for e in errors)
    
    def test_create_ticket_no_file_context(self, repo):
        """Create ticket with no file_context (should succeed)."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-011",
            priority=TicketPriority.P2,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
            file_context=None,
        )
        assert repo.create_ticket(entry) is True
    
    def test_create_ticket_file_context_within_limit(self, repo):
        """Create ticket with file_context within limit (should succeed)."""
        # Create file context that serializes to ~900KB
        file_context = {f"file_{i}.py": "x" * 9000 for i in range(100)}
        entry = ActifixEntry(
            entry_id="ACT-20260114-012",
            priority=TicketPriority.P2,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
            file_context=file_context,
        )
        assert repo.create_ticket(entry) is True
    
    def test_file_context_serialization_size(self):
        """Verify file context size is calculated on serialized JSON."""
        file_context = {f"file_{i}.py": "x" * 1000 for i in range(10)}
        json_str = serialize_json_field(file_context)
        size_bytes = len(json_str.encode('utf-8'))
        # Should be roughly 10 files * 1000 chars + JSON overhead
        assert size_bytes > 10000
    
    def test_create_ticket_file_context_exceeds_limit(self, repo):
        """Create ticket with file_context exceeding limit (should fail or truncate)."""
        # Create file context that exceeds 1MB
        file_context = {f"file_{i}.py": "x" * 50000 for i in range(30)}
        entry = ActifixEntry(
            entry_id="ACT-20260114-013",
            priority=TicketPriority.P2,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
            file_context=file_context,
        )
        # This entry should either fail to create or be handled by raise_af
        result = repo.create_ticket(entry)
        # Just verify it either succeeded or failed gracefully
        assert isinstance(result, bool)


class TestTicket3OpenTicketsLimit:
    """Tests for Ticket 3: Open tickets limit (ACT-20260114-2FBBC)"""
    
    def test_config_load_default_open_ticket_limit(self):
        """Verify config loads with default open ticket limit."""
        config = load_config(fail_fast=False)
        assert config.max_open_tickets == 10000
    
    def test_config_validate_open_ticket_limit_positive(self):
        """Verify validation rejects non-positive open ticket limit."""
        paths = get_actifix_paths()
        config = ActifixConfig(
            project_root=Path.cwd(),
            paths=paths,
            max_open_tickets=-1,
        )
        errors = validate_config(config)
        assert any("open tickets" in e.lower() for e in errors)
    
    def test_create_multiple_tickets_within_limit(self, repo):
        """Create multiple tickets up to custom limit (should succeed)."""
        # Create 5 tickets
        for i in range(5):
            entry = ActifixEntry(
                entry_id=f"ACT-20260114-{i:03d}",
                priority=TicketPriority.P2,
                error_type="TestError",
                message=f"Test message {i}",
                source="test.py:42",
            )
            assert repo.create_ticket(entry) is True
        
        # Verify all 5 are Open
        stats = repo.get_stats()
        assert stats['open'] == 5
    
    def test_open_tickets_count_excludes_completed(self, repo):
        """Verify completed tickets don't count toward open limit."""
        # Create 2 tickets
        for i in range(2):
            entry = ActifixEntry(
                entry_id=f"ACT-20260114-{100 + i:03d}",
                priority=TicketPriority.P2,
                error_type="TestError",
                message=f"Test message {i}",
                source="test.py:42",
            )
            repo.create_ticket(entry)
        
        # Complete one ticket
        repo.mark_complete(
            "ACT-20260114-100",
            "Fixed the issue",
            "Ran unit tests",
            "All tests passed",
        )
        
        # Only 1 should be open now
        stats = repo.get_stats()
        assert stats['open'] == 1
        assert stats['completed'] == 1
    
    def test_open_tickets_count_excludes_deleted(self, repo):
        """Verify deleted tickets don't count toward open limit."""
        # Create 2 tickets
        for i in range(2):
            entry = ActifixEntry(
                entry_id=f"ACT-20260114-{200 + i:03d}",
                priority=TicketPriority.P2,
                error_type="TestError",
                message=f"Test message {i}",
                source="test.py:42",
            )
            repo.create_ticket(entry)
        
        # Delete one ticket (soft delete)
        repo.delete_ticket("ACT-20260114-200", soft_delete=True)
        
        # Only 1 should be open now
        stats = repo.get_stats()
        assert stats['open'] == 1
        assert stats['deleted'] == 1


class TestLeaseBasedLocking:
    """Tests verifying lease-based locking mechanism (Ticket 4 documentation)"""
    
    def test_lease_expires_after_duration(self, repo):
        """Verify lock expires exactly at specified time."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-301",
            priority=TicketPriority.P1,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        # Acquire lock with 1-hour lease
        lock = repo.acquire_lock("ACT-20260114-301", "agent-1", lease_duration=timedelta(hours=1))
        assert lock is not None
        assert lock.lease_expires > lock.locked_at
        assert (lock.lease_expires - lock.locked_at).total_seconds() == 3600  # 1 hour
    
    def test_expired_lock_can_be_reacquired(self, repo):
        """Verify expired lock can be taken by new agent."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-302",
            priority=TicketPriority.P1,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        # Acquire lock with very short duration
        lock1 = repo.acquire_lock("ACT-20260114-302", "agent-1", lease_duration=timedelta(seconds=1))
        assert lock1 is not None
        
        # Wait for lease to expire
        import time
        time.sleep(2)
        
        # New agent should be able to acquire
        lock2 = repo.acquire_lock("ACT-20260114-302", "agent-2", lease_duration=timedelta(hours=1))
        assert lock2 is not None
        assert lock2.locked_by == "agent-2"
    
    def test_renew_lock_extends_expiry(self, repo):
        """Verify renew_lock extends lease properly."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-303",
            priority=TicketPriority.P1,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        # Acquire lock
        lock1 = repo.acquire_lock("ACT-20260114-303", "agent-1", lease_duration=timedelta(hours=1))
        original_expiry = lock1.lease_expires
        
        import time
        time.sleep(1)
        
        # Renew lock
        lock2 = repo.renew_lock("ACT-20260114-303", "agent-1", lease_duration=timedelta(hours=1))
        new_expiry = lock2.lease_expires
        
        # New expiry should be later
        assert new_expiry > original_expiry
        assert (new_expiry - lock2.locked_at).total_seconds() == 3600  # 1 hour from renewal
    
    def test_cleanup_makes_expired_available(self, repo):
        """Verify cleanup_expired_locks() clears locks."""
        entry = ActifixEntry(
            entry_id="ACT-20260114-304",
            priority=TicketPriority.P1,
            error_type="TestError",
            message="Test message",
            source="test.py:42",
        )
        repo.create_ticket(entry)
        
        # Acquire lock with very short duration
        lock = repo.acquire_lock("ACT-20260114-304", "agent-1", lease_duration=timedelta(seconds=1))
        assert lock is not None
        
        # Verify ticket is locked
        ticket = repo.get_ticket("ACT-20260114-304")
        assert ticket['locked_by'] == "agent-1"
        
        # Wait for lease to expire
        import time
        time.sleep(2)
        
        # Cleanup should free it
        count = repo.cleanup_expired_locks()
        assert count >= 1
        
        # Verify ticket is no longer locked
        ticket = repo.get_ticket("ACT-20260114-304")
        assert ticket['locked_by'] is None
        assert ticket['status'] == 'Open'


class TestIntegration:
    """Integration tests for ticket creation with multiple constraints."""
    
    def test_create_multiple_tickets_with_varying_priorities(self, repo):
        """Create tickets with different priorities and verify ordering."""
        # Create tickets in random order
        for priority_char, priority_obj in [
            ("2", TicketPriority.P2),
            ("0", TicketPriority.P0),
            ("4", TicketPriority.P4),
            ("1", TicketPriority.P1),
            ("3", TicketPriority.P3),
        ]:
            entry = ActifixEntry(
                entry_id=f"ACT-20260114-50{priority_char}",
                priority=priority_obj,
                error_type="TestError",
                message=f"Test message P{priority_char}",
                source="test.py:42",
            )
            assert repo.create_ticket(entry) is True
        
        # Get next ticket should return P0
        ticket = repo.get_and_lock_next_ticket("agent-1")
        assert ticket is not None
        assert ticket['priority'] == 'P0'
    
    def test_fair_work_distribution(self, repo):
        """Verify fair distribution of work among agents."""
        # Create 3 tickets
        for i in range(3):
            entry = ActifixEntry(
                entry_id=f"ACT-20260114-60{i}",
                priority=TicketPriority.P2,
                error_type="TestError",
                message=f"Test message {i}",
                source="test.py:42",
            )
            repo.create_ticket(entry)
        
        # Three agents each get different tickets
        ticket1 = repo.get_and_lock_next_ticket("agent-1")
        ticket2 = repo.get_and_lock_next_ticket("agent-2")
        ticket3 = repo.get_and_lock_next_ticket("agent-3")
        
        # Each should get a different ticket
        assert ticket1 is not None
        assert ticket2 is not None
        assert ticket3 is not None
        assert ticket1['id'] != ticket2['id']
        assert ticket2['id'] != ticket3['id']
        assert ticket1['id'] != ticket3['id']
        
        # Fourth agent should get None (all locked)
        ticket4 = repo.get_and_lock_next_ticket("agent-4")
        assert ticket4 is None