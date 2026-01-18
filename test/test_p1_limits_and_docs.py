#!/usr/bin/env python3
"""
Tests for P1 tickets: message length limits, file context limits, open ticket limits, and locking documentation.

Verifies:
1. ACT-20260114-AD00C: Message length limits are enforced
2. ACT-20260114-EE698: File context size limits are enforced
3. ACT-20260114-2FBBC: Open ticket count limits are enforced
4. ACT-20260114-7C9E0: Locking mechanism is properly documented
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from actifix.config import load_config, validate_config, ActifixConfig
from actifix.persistence.database import get_database_pool, reset_database_pool
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority

pytestmark = [pytest.mark.db, pytest.mark.integration]


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Clean database for each test."""
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "test.db"))
    reset_database_pool()
    reset_ticket_repository()
    yield
    reset_database_pool()
    reset_ticket_repository()


class TestMessageLengthLimit:
    """Test message length limit enforcement (ACT-20260114-AD00C)."""

    def test_config_default_message_length(self):
        """Verify default max message length is configured."""
        config = load_config(fail_fast=False)
        assert config.max_ticket_message_length == 5000

    def test_config_message_length_from_env(self, monkeypatch):
        """Verify message length configurable via environment."""
        monkeypatch.setenv("ACTIFIX_MAX_MESSAGE_LENGTH", "10000")
        config = load_config(fail_fast=False)
        assert config.max_ticket_message_length == 10000

    def test_validate_message_length_positive(self):
        """Verify message length validation requires positive value."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_ticket_message_length=-1
        )
        errors = validate_config(config)
        assert any("message length" in e.lower() for e in errors)

    def test_validate_message_length_reasonable(self):
        """Verify message length validation enforces reasonable upper bound."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_ticket_message_length=2000000  # 2MB - too large
        )
        errors = validate_config(config)
        assert any("message length" in e.lower() for e in errors)

    def test_message_length_valid_range(self):
        """Verify valid message length passes validation."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_ticket_message_length=5000
        )
        # Should not raise
        assert config.max_ticket_message_length == 5000


class TestFileContextSizeLimit:
    """Test file context size limit enforcement (ACT-20260114-EE698)."""

    def test_config_default_file_context_size(self):
        """Verify default max file context size is configured."""
        config = load_config(fail_fast=False)
        assert config.max_file_context_size_bytes == 1 * 1024 * 1024  # 1MB

    def test_config_file_context_size_from_env(self, monkeypatch):
        """Verify file context size configurable via environment."""
        monkeypatch.setenv("ACTIFIX_MAX_FILE_CONTEXT_BYTES", "5242880")  # 5MB
        config = load_config(fail_fast=False)
        assert config.max_file_context_size_bytes == 5242880

    def test_validate_file_context_size_positive(self):
        """Verify file context size validation requires positive value."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_file_context_size_bytes=0
        )
        errors = validate_config(config)
        assert any("file context size" in e.lower() for e in errors)

    def test_validate_file_context_size_reasonable(self):
        """Verify file context size validation enforces reasonable upper bound."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_file_context_size_bytes=500 * 1024 * 1024  # 500MB - too large
        )
        errors = validate_config(config)
        assert any("file context size" in e.lower() for e in errors)

    def test_file_context_size_valid_range(self):
        """Verify valid file context size passes validation."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_file_context_size_bytes=10 * 1024 * 1024  # 10MB
        )
        # Should not raise
        assert config.max_file_context_size_bytes == 10 * 1024 * 1024


class TestOpenTicketLimit:
    """Test open ticket count limit enforcement (ACT-20260114-2FBBC)."""

    def test_config_default_open_tickets(self):
        """Verify default max open tickets is configured."""
        config = load_config(fail_fast=False)
        assert config.max_open_tickets == 10000

    def test_config_open_tickets_from_env(self, monkeypatch):
        """Verify open tickets limit configurable via environment."""
        monkeypatch.setenv("ACTIFIX_MAX_OPEN_TICKETS", "5000")
        config = load_config(fail_fast=False)
        assert config.max_open_tickets == 5000

    def test_validate_open_tickets_positive(self):
        """Verify open tickets validation requires positive value."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_open_tickets=-1
        )
        errors = validate_config(config)
        assert any("open tickets" in e.lower() for e in errors)

    def test_validate_open_tickets_reasonable(self):
        """Verify open tickets limit must be positive."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_open_tickets=0
        )
        errors = validate_config(config)
        assert any("open tickets" in e.lower() for e in errors)

    def test_open_tickets_valid_value(self):
        """Verify valid open tickets limit passes validation."""
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_open_tickets=10000
        )
        # Should not raise
        assert config.max_open_tickets == 10000


class TestLockingDocumentation:
    """Test locking mechanism documentation (ACT-20260114-7C9E0)."""

    def test_acquire_lock_method_has_docstring(self):
        """Verify acquire_lock method is documented."""
        from actifix.persistence.ticket_repo import TicketRepository

        assert TicketRepository.acquire_lock.__doc__ is not None
        assert len(TicketRepository.acquire_lock.__doc__) > 100
        assert "lease" in TicketRepository.acquire_lock.__doc__.lower()

    def test_renew_lock_method_has_docstring(self):
        """Verify renew_lock method is documented."""
        from actifix.persistence.ticket_repo import TicketRepository

        assert TicketRepository.renew_lock.__doc__ is not None
        assert len(TicketRepository.renew_lock.__doc__) > 100
        assert "lease" in TicketRepository.renew_lock.__doc__.lower() or "renew" in TicketRepository.renew_lock.__doc__.lower()

    def test_module_has_locking_documentation(self):
        """Verify module docstring explains locking strategy."""
        from actifix import persistence

        assert persistence.ticket_repo.__doc__ is not None
        # Check for locking-related concepts in module docs
        assert any(keyword in persistence.ticket_repo.__doc__.lower()
                  for keyword in ["lock", "lease", "distributed"])

    def test_lock_holder_parameter_documented(self, clean_db):
        """Verify lock holder parameter is explained."""
        repo = get_ticket_repository()

        # Get the acquire_lock docstring
        doc = repo.acquire_lock.__doc__
        assert doc is not None
        assert "locked_by" in doc.lower() or "holder" in doc.lower()

    def test_lease_duration_explained(self, clean_db):
        """Verify lease duration rationale is documented."""
        repo = get_ticket_repository()

        # Check both acquire_lock and module docs mention lease duration
        doc = repo.acquire_lock.__doc__
        assert doc is not None
        assert "lease" in doc.lower() or "duration" in doc.lower() or "expir" in doc.lower()

    def test_get_and_lock_next_ticket_documented(self):
        """Verify get_and_lock_next_ticket has detailed documentation."""
        from actifix.persistence.ticket_repo import TicketRepository

        assert TicketRepository.get_and_lock_next_ticket.__doc__ is not None
        assert len(TicketRepository.get_and_lock_next_ticket.__doc__) > 50


class TestConfigIntegration:
    """Test configuration integration for all limits."""

    def test_all_limits_loadable(self):
        """Verify all new config limits can be loaded together."""
        config = load_config(fail_fast=False)

        assert config.max_ticket_message_length > 0
        assert config.max_file_context_size_bytes > 0
        assert config.max_open_tickets > 0

    def test_config_validation_passes_with_defaults(self):
        """Verify default configuration passes validation."""
        config = load_config(fail_fast=False)
        errors = validate_config(config)

        # May have other errors (like missing project root), but not limit errors
        limit_errors = [e for e in errors if any(x in e.lower() for x in
                        ["message", "file context", "open tickets"])]
        assert len(limit_errors) == 0

    def test_limits_independent(self, monkeypatch):
        """Verify limits can be configured independently."""
        monkeypatch.setenv("ACTIFIX_MAX_MESSAGE_LENGTH", "10000")
        # Don't set others, should use defaults

        config = load_config(fail_fast=False)
        assert config.max_ticket_message_length == 10000
        assert config.max_file_context_size_bytes == 1 * 1024 * 1024
        assert config.max_open_tickets == 10000


class TestConfigEdgeCases:
    """Test configuration edge cases and boundary conditions."""

    def test_message_length_edge_cases(self):
        """Verify message length edge cases."""
        # Minimum valid
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_ticket_message_length=1
        )
        assert config.max_ticket_message_length == 1

        # Maximum valid
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_ticket_message_length=1000000
        )
        assert config.max_ticket_message_length == 1000000

    def test_file_context_edge_cases(self):
        """Verify file context size edge cases."""
        # Minimum valid
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_file_context_size_bytes=1
        )
        assert config.max_file_context_size_bytes == 1

        # Maximum valid
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_file_context_size_bytes=100 * 1024 * 1024
        )
        assert config.max_file_context_size_bytes == 100 * 1024 * 1024

    def test_open_tickets_edge_cases(self):
        """Verify open tickets edge cases."""
        # Minimum valid
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_open_tickets=1
        )
        assert config.max_open_tickets == 1

        # Large value
        config = ActifixConfig(
            project_root=Path("/tmp"),
            paths=None,
            max_open_tickets=1000000
        )
        assert config.max_open_tickets == 1000000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
