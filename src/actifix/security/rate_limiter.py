#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rate Limiter - Prevent abuse of external AI provider APIs.

Implements token bucket rate limiting with:
- Per-provider limits (API calls per time window)
- Configurable time windows (minute, hour, day)
- Thread-safe enforcement
- Persistent state tracking
- Detailed logging of violations

Version: 1.0.0
"""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


@dataclass
class RateLimitConfig:
    """Configuration for a single provider's rate limit."""

    provider_name: str  # e.g., "openai", "claude_api"
    calls_per_minute: int  # Max calls in a minute
    calls_per_hour: int  # Max calls in an hour
    calls_per_day: int  # Max calls in a 24-hour period
    enabled: bool = True  # Whether this limit is enforced


@dataclass
class APICall:
    """Record of a single API call for tracking."""

    provider: str
    timestamp: datetime  # When the call was made
    success: bool  # Whether the call succeeded
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None


class RateLimiter:
    """
    Thread-safe rate limiter for AI provider API calls.

    Uses token bucket algorithm to enforce rate limits.
    Tracks calls in memory and persists to database.
    """

    # Default rate limits (conservative to avoid abuse)
    DEFAULT_LIMITS: Dict[str, RateLimitConfig] = {
        'openai': RateLimitConfig(
            provider_name='openai',
            calls_per_minute=3,      # 3 calls per minute (180/hour)
            calls_per_hour=30,       # 30 calls per hour
            calls_per_day=200,       # 200 calls per day
        ),
        'claude_api': RateLimitConfig(
            provider_name='claude_api',
            calls_per_minute=5,      # 5 calls per minute (more generous)
            calls_per_hour=50,       # 50 calls per hour
            calls_per_day=300,       # 300 calls per day
        ),
        'claude_local': RateLimitConfig(
            provider_name='claude_local',
            calls_per_minute=10,     # Local Claude has no API limits
            calls_per_hour=200,
            calls_per_day=2000,
            enabled=False,  # Disabled - local has no limits
        ),
        'ollama': RateLimitConfig(
            provider_name='ollama',
            calls_per_minute=10,     # Local Ollama has no API limits
            calls_per_hour=200,
            calls_per_day=2000,
            enabled=False,  # Disabled - local has no limits
        ),
    }

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the rate limiter.

        Args:
            db_path: Path to SQLite database for tracking calls
        """
        self.db_path = db_path or self._get_default_db_path()
        self.lock = threading.RLock()
        self.call_history: Dict[str, list] = {}  # In-memory cache
        self.limits = self.DEFAULT_LIMITS.copy()
        self._init_database()

    def _get_default_db_path(self) -> str:
        """Get default database path for rate limiting data."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'rate_limits.db')

    def _init_database(self) -> None:
        """Initialize database for rate limit tracking."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # Create rate limit tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    error TEXT,
                    CHECK (provider IN ('openai', 'claude_api', 'claude_local', 'ollama'))
                )
            ''')

            # Create index for efficient queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_api_calls_provider_timestamp
                ON api_calls(provider, timestamp)
            ''')

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            # Database errors shouldn't block operation
            pass

    def set_limit(self, provider: str, config: RateLimitConfig) -> None:
        """Update rate limit configuration for a provider.

        Args:
            provider: Provider name (e.g., 'openai')
            config: New rate limit configuration
        """
        with self.lock:
            self.limits[provider] = config

    def check_rate_limit(self, provider: str) -> None:
        """Check if a call to a provider would exceed rate limits.

        Args:
            provider: Provider name (e.g., 'openai')

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        with self.lock:
            # Get the provider's configuration
            config = self.limits.get(provider)

            if not config or not config.enabled:
                return  # No limit or limit disabled

            now = datetime.now(timezone.utc)

            # Count calls in each time window
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            calls_in_minute = self._count_calls_since(provider, minute_ago)
            calls_in_hour = self._count_calls_since(provider, hour_ago)
            calls_in_day = self._count_calls_since(provider, day_ago)

            # Check limits
            if calls_in_minute >= config.calls_per_minute:
                raise RateLimitError(
                    f"Rate limit exceeded for {provider}: "
                    f"{calls_in_minute}/{config.calls_per_minute} calls in last minute"
                )

            if calls_in_hour >= config.calls_per_hour:
                raise RateLimitError(
                    f"Rate limit exceeded for {provider}: "
                    f"{calls_in_hour}/{config.calls_per_hour} calls in last hour"
                )

            if calls_in_day >= config.calls_per_day:
                raise RateLimitError(
                    f"Rate limit exceeded for {provider}: "
                    f"{calls_in_day}/{config.calls_per_day} calls in last 24 hours"
                )

    def record_call(
        self,
        provider: str,
        success: bool,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Record an API call for rate limiting tracking.

        Args:
            provider: Provider name
            success: Whether the call succeeded
            tokens_used: Number of tokens used (if applicable)
            cost_usd: Cost in USD (if applicable)
            error: Error message if failed
        """
        with self.lock:
            now = datetime.now(timezone.utc)

            call = APICall(
                provider=provider,
                timestamp=now,
                success=success,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                error=error,
            )

            # Update in-memory cache
            if provider not in self.call_history:
                self.call_history[provider] = []
            self.call_history[provider].append(call)

            # Persist to database
            self._persist_call(call)

            # Clean up old records (older than 24 hours)
            self._cleanup_old_records()

    def get_usage_stats(self, provider: str) -> Dict[str, int]:
        """Get usage statistics for a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary with usage stats
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            stats = {
                'provider': provider,
                'calls_last_minute': self._count_calls_since(provider, minute_ago),
                'calls_last_hour': self._count_calls_since(provider, hour_ago),
                'calls_last_day': self._count_calls_since(provider, day_ago),
                'successful_calls': self._count_successful_calls(provider),
                'failed_calls': self._count_failed_calls(provider),
            }

            # Add limit information if available
            config = self.limits.get(provider)
            if config:
                stats['limit_minute'] = config.calls_per_minute
                stats['limit_hour'] = config.calls_per_hour
                stats['limit_day'] = config.calls_per_day

            return stats

    def _count_calls_since(self, provider: str, since: datetime) -> int:
        """Count calls since a specific time."""
        if provider not in self.call_history:
            return 0

        count = 0
        for call in self.call_history[provider]:
            if call.timestamp >= since:
                count += 1

        return count

    def _count_successful_calls(self, provider: str) -> int:
        """Count successful calls for a provider."""
        if provider not in self.call_history:
            return 0

        return sum(1 for call in self.call_history[provider] if call.success)

    def _count_failed_calls(self, provider: str) -> int:
        """Count failed calls for a provider."""
        if provider not in self.call_history:
            return 0

        return sum(1 for call in self.call_history[provider] if not call.success)

    def _persist_call(self, call: APICall) -> None:
        """Persist a call record to database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO api_calls
                (provider, timestamp, success, tokens_used, cost_usd, error)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                call.provider,
                call.timestamp.isoformat(),
                call.success,
                call.tokens_used,
                call.cost_usd,
                call.error,
            ))

            conn.commit()
            conn.close()
        except sqlite3.Error:
            # Database persistence failure shouldn't block operation
            pass

    def _cleanup_old_records(self) -> None:
        """Remove API call records older than 24 hours."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM api_calls WHERE timestamp < ?
            ''', (cutoff,))

            conn.commit()
            conn.close()

            # Also clean up in-memory cache
            with self.lock:
                for provider in self.call_history:
                    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=1)
                    self.call_history[provider] = [
                        call for call in self.call_history[provider]
                        if call.timestamp >= cutoff_dt
                    ]

        except sqlite3.Error:
            pass


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter

    if _rate_limiter is None:
        with _limiter_lock:
            if _rate_limiter is None:
                _rate_limiter = RateLimiter()

    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (for testing)."""
    global _rate_limiter
    with _limiter_lock:
        _rate_limiter = None
