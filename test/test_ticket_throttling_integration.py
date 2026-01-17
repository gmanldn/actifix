#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for ticket throttling.

Tests the end-to-end throttling behavior when creating tickets via record_error().
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

from actifix.config import ActifixConfig, get_actifix_paths
from actifix.raise_af import record_error, TicketPriority
from actifix.security.ticket_throttler import (
    TicketThrottler,
    TicketThrottleError,
    ThrottleConfig,
    reset_ticket_throttler,
)
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.persistence.database import reset_database_pool
from actifix.config import set_config, reset_config


@pytest.fixture
def temp_dir():
    """Create temporary directory for test state."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_config_with_throttling(temp_dir):
    """Create test configuration with throttling enabled."""
    paths = get_actifix_paths(project_root=temp_dir)
    config = ActifixConfig(
        project_root=temp_dir,
        paths=paths,
        ticket_throttling_enabled=True,
        max_p2_tickets_per_hour=3,  # Lower limit for testing
        max_p3_tickets_per_4h=2,
        max_p4_tickets_per_day=1,
        emergency_ticket_threshold=5,  # Lower for testing
        emergency_window_minutes=1,
    )
    set_config(config)
    yield config
    reset_config()


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Reset global state before and after each test."""
    reset_ticket_throttler()
    reset_ticket_repository()
    reset_database_pool()
    reset_config()
    yield
    reset_ticket_throttler()
    reset_ticket_repository()
    reset_database_pool()
    reset_config()


class TestP2Throttling:
    """Tests for P2 ticket throttling (max per hour)."""

    def test_p2_allows_tickets_within_limit(self, test_config_with_throttling):
        """Should allow P2 tickets up to the hourly limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create tickets up to limit (3)
        for i in range(3):
            entry = record_error(
                message=f"P2 error {i}",
                source="test.py:1",
                error_type="TestError",
                priority=TicketPriority.P2,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None, f"Should create ticket {i}"

    def test_p2_blocks_tickets_over_limit(self, test_config_with_throttling):
        """Should block P2 tickets exceeding the hourly limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create tickets up to limit (3)
        for i in range(3):
            entry = record_error(
                message=f"P2 error {i}",
                source="test.py:1",
                error_type="TestError",
                priority=TicketPriority.P2,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None

        # Next ticket should be throttled
        entry = record_error(
            message="P2 error over limit",
            source="test.py:1",
            error_type="TestError",
            priority=TicketPriority.P2,
            paths=test_config_with_throttling.paths,
        )
        assert entry is None, "Should throttle ticket exceeding limit"


class TestP3Throttling:
    """Tests for P3 ticket throttling (max per 4 hours)."""

    def test_p3_allows_tickets_within_limit(self, test_config_with_throttling):
        """Should allow P3 tickets up to the 4-hour limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create tickets up to limit (2)
        for i in range(2):
            entry = record_error(
                message=f"P3 error {i}",
                source="test.py:1",
                error_type="TestError",
                priority=TicketPriority.P3,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None, f"Should create ticket {i}"

    def test_p3_blocks_tickets_over_limit(self, test_config_with_throttling):
        """Should block P3 tickets exceeding the 4-hour limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create tickets up to limit (2)
        for i in range(2):
            entry = record_error(
                message=f"P3 error {i}",
                source="test.py:1",
                error_type="TestError",
                priority=TicketPriority.P3,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None

        # Next ticket should be throttled
        entry = record_error(
            message="P3 error over limit",
            source="test.py:1",
            error_type="TestError",
            priority=TicketPriority.P3,
            paths=test_config_with_throttling.paths,
        )
        assert entry is None, "Should throttle ticket exceeding limit"


class TestP4Throttling:
    """Tests for P4 ticket throttling (max per day)."""

    def test_p4_allows_ticket_within_limit(self, test_config_with_throttling):
        """Should allow P4 tickets up to the daily limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create ticket (limit is 1)
        entry = record_error(
            message="P4 error",
            source="test.py:1",
            error_type="TestError",
            priority=TicketPriority.P4,
            paths=test_config_with_throttling.paths,
        )
        assert entry is not None

    def test_p4_blocks_tickets_over_limit(self, test_config_with_throttling):
        """Should block P4 tickets exceeding the daily limit."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create ticket up to limit (1)
        entry = record_error(
            message="P4 error",
            source="test.py:1",
            error_type="TestError",
            priority=TicketPriority.P4,
            paths=test_config_with_throttling.paths,
        )
        assert entry is not None

        # Next ticket should be throttled
        entry = record_error(
            message="P4 error over limit",
            source="test.py:1",
            error_type="TestError",
            priority=TicketPriority.P4,
            paths=test_config_with_throttling.paths,
        )
        assert entry is None, "Should throttle ticket exceeding limit"


class TestP0P1NoThrottling:
    """Tests that P0 and P1 tickets are never throttled."""

    def test_p0_never_throttled(self, test_config_with_throttling):
        """P0 tickets should never be throttled regardless of rate."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create many P0 tickets rapidly
        for i in range(10):
            entry = record_error(
                message=f"P0 critical error {i}",
                source="test.py:1",
                error_type="CriticalError",
                priority=TicketPriority.P0,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None, f"P0 ticket {i} should never be throttled"

    def test_p1_never_throttled(self, test_config_with_throttling):
        """P1 tickets should never be throttled regardless of rate."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create many P1 tickets rapidly
        for i in range(10):
            entry = record_error(
                message=f"P1 high priority error {i}",
                source="test.py:1",
                error_type="HighPriorityError",
                priority=TicketPriority.P1,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None, f"P1 ticket {i} should never be throttled"


class TestEmergencyBrake:
    """Tests for emergency brake to prevent ticket floods."""

    def test_emergency_brake_activates(self, test_config_with_throttling):
        """Emergency brake should activate when too many tickets created rapidly."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        # Create tickets up to emergency threshold (5)
        # Mix of priorities to test cross-priority emergency brake
        priorities = [TicketPriority.P2, TicketPriority.P3, TicketPriority.P2,
                      TicketPriority.P3, TicketPriority.P2]

        for i, priority in enumerate(priorities):
            entry = record_error(
                message=f"Error {i}",
                source=f"test.py:{i}",
                error_type="TestError",
                priority=priority,
                paths=test_config_with_throttling.paths,
            )
            assert entry is not None, f"Should create ticket {i}"

        # Next ticket should trigger emergency brake (even P1)
        entry = record_error(
            message="This should be blocked by emergency brake",
            source="test.py:999",
            error_type="TestError",
            priority=TicketPriority.P1,
            paths=test_config_with_throttling.paths,
        )
        assert entry is None, "Emergency brake should block even P1 tickets"


class TestThrottlingDisabled:
    """Tests that throttling can be disabled via config."""

    def test_throttling_disabled_allows_unlimited(self, temp_dir):
        """When throttling is disabled, should allow unlimited tickets."""
        import os
        os.environ['ACTIFIX_CAPTURE_ENABLED'] = '1'

        paths = get_actifix_paths(project_root=temp_dir)
        config = ActifixConfig(
            project_root=temp_dir,
            paths=paths,
            ticket_throttling_enabled=False,  # Disabled
        )
        set_config(config)

        # Create many P2 tickets - should all succeed
        for i in range(20):
            entry = record_error(
                message=f"P2 error {i}",
                source="test.py:1",
                error_type="TestError",
                priority=TicketPriority.P2,
                paths=config.paths,
            )
            assert entry is not None, f"Should create ticket {i} when throttling disabled"
