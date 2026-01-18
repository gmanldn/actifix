#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cleanup Configuration and Settings

Centralized configuration for automatic ticket cleanup policies.
"""

import os
from typing import Optional


class CleanupConfig:
    """Configuration for automatic ticket cleanup."""

    def __init__(
        self,
        enabled: bool = True,
        retention_days: int = 90,
        test_ticket_retention_days: int = 7,
        auto_complete_test_tickets: bool = True,
        run_on_health_check: bool = False,
        min_hours_between_runs: int = 24,
    ):
        """
        Initialize cleanup configuration.

        Args:
            enabled: Enable automatic cleanup.
            retention_days: Days to keep regular completed tickets (default: 90).
            test_ticket_retention_days: Days to keep test/automation tickets (default: 7).
            auto_complete_test_tickets: Auto-complete open test tickets (default: True).
            run_on_health_check: Run cleanup during health checks (default: False).
            min_hours_between_runs: Minimum hours between cleanup runs (default: 24).
        """
        self.enabled = enabled
        self.retention_days = retention_days
        self.test_ticket_retention_days = test_ticket_retention_days
        self.auto_complete_test_tickets = auto_complete_test_tickets
        self.run_on_health_check = run_on_health_check
        self.min_hours_between_runs = min_hours_between_runs

    @classmethod
    def from_env(cls) -> 'CleanupConfig':
        """
        Create cleanup config from environment variables.

        Environment variables:
            ACTIFIX_CLEANUP_ENABLED: Enable/disable cleanup (default: true)
            ACTIFIX_RETENTION_DAYS: Days to keep completed tickets (default: 90)
            ACTIFIX_TEST_RETENTION_DAYS: Days to keep test tickets (default: 7)
            ACTIFIX_AUTO_COMPLETE_TESTS: Auto-complete test tickets (default: true)
            ACTIFIX_CLEANUP_ON_HEALTH: Run cleanup during health checks (default: false)
            ACTIFIX_CLEANUP_MIN_HOURS: Min hours between runs (default: 24)

        Returns:
            CleanupConfig instance.
        """
        def get_bool(key: str, default: bool) -> bool:
            val = os.environ.get(key, '').lower()
            if val in ('true', '1', 'yes', 'on'):
                return True
            elif val in ('false', '0', 'no', 'off'):
                return False
            return default

        def get_int(key: str, default: int) -> int:
            try:
                return int(os.environ.get(key, str(default)))
            except (ValueError, TypeError):
                return default

        return cls(
            enabled=get_bool('ACTIFIX_CLEANUP_ENABLED', True),
            retention_days=get_int('ACTIFIX_RETENTION_DAYS', 90),
            test_ticket_retention_days=get_int('ACTIFIX_TEST_RETENTION_DAYS', 7),
            auto_complete_test_tickets=get_bool('ACTIFIX_AUTO_COMPLETE_TESTS', True),
            run_on_health_check=get_bool('ACTIFIX_CLEANUP_ON_HEALTH', False),
            min_hours_between_runs=get_int('ACTIFIX_CLEANUP_MIN_HOURS', 24),
        )

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'enabled': self.enabled,
            'retention_days': self.retention_days,
            'test_ticket_retention_days': self.test_ticket_retention_days,
            'auto_complete_test_tickets': self.auto_complete_test_tickets,
            'run_on_health_check': self.run_on_health_check,
            'min_hours_between_runs': self.min_hours_between_runs,
        }


# Global default config
_default_config: Optional[CleanupConfig] = None


def get_cleanup_config() -> CleanupConfig:
    """
    Get the global cleanup configuration.

    This loads from environment variables on first call.

    Returns:
        CleanupConfig instance.
    """
    global _default_config
    if _default_config is None:
        _default_config = CleanupConfig.from_env()
    return _default_config


def set_cleanup_config(config: CleanupConfig) -> None:
    """
    Set the global cleanup configuration.

    Args:
        config: CleanupConfig instance to use globally.
    """
    global _default_config
    _default_config = config
