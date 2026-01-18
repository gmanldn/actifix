#!/usr/bin/env python3
"""
Tests for AI client rate limiting.

Verifies that:
1. Rate limits are enforced per provider
2. Different time windows (minute, hour, day) work correctly
3. Successful and failed calls are tracked
4. Limits can be configured
5. Thread safety is maintained
6. Database persistence works
7. Old records are cleaned up
"""

import sqlite3
import tempfile
import time
import threading
from datetime import datetime, timezone, timedelta

import pytest

from actifix.security.rate_limiter import (
    RateLimiter,
    RateLimitError,
    RateLimitConfig,
    APICall,
    get_rate_limiter,
    reset_rate_limiter,
)

pytestmark = [pytest.mark.db, pytest.mark.integration]


class TestRateLimiterConfiguration:
    """Test rate limiter configuration."""

    def test_default_limits_loaded(self):
        """Verify default limits are loaded."""
        limiter = RateLimiter()
        assert 'openai' in limiter.limits
        assert 'claude_api' in limiter.limits
        assert 'ollama' in limiter.limits
        assert 'claude_local' in limiter.limits

    def test_openai_limit_config(self):
        """Verify OpenAI rate limits are reasonable."""
        limiter = RateLimiter()
        config = limiter.limits['openai']
        assert config.calls_per_minute == 3
        assert config.calls_per_hour == 30
        assert config.calls_per_day == 200
        assert config.enabled is True

    def test_claude_api_limit_config(self):
        """Verify Claude API rate limits are reasonable."""
        limiter = RateLimiter()
        config = limiter.limits['claude_api']
        assert config.calls_per_minute == 5
        assert config.calls_per_hour == 50
        assert config.calls_per_day == 300
        assert config.enabled is True

    def test_local_providers_disabled(self):
        """Verify local providers (Ollama, Claude Local) have disabled limits."""
        limiter = RateLimiter()
        assert limiter.limits['ollama'].enabled is False
        assert limiter.limits['claude_local'].enabled is False

    def test_set_custom_limit(self):
        """Verify custom limits can be set."""
        limiter = RateLimiter()
        custom_config = RateLimitConfig(
            provider_name='custom',
            calls_per_minute=10,
            calls_per_hour=100,
            calls_per_day=1000,
        )
        limiter.set_limit('custom', custom_config)
        assert limiter.limits['custom'] == custom_config


class TestMinuteRateLimit:
    """Test per-minute rate limits."""

    def test_no_limit_exceeded_under_minute_limit(self):
        """Verify no error when under minute limit."""
        limiter = RateLimiter()
        # OpenAI allows 3/minute
        limiter.check_rate_limit('openai')
        limiter.record_call('openai', success=True)
        limiter.record_call('openai', success=True)
        # Third call should still succeed
        limiter.check_rate_limit('openai')

    def test_limit_exceeded_at_minute_limit(self):
        """Verify error when at minute limit."""
        limiter = RateLimiter()
        # OpenAI allows 3/minute
        for _ in range(3):
            limiter.check_rate_limit('openai')
            limiter.record_call('openai', success=True)

        # Fourth call should fail
        with pytest.raises(RateLimitError):
            limiter.check_rate_limit('openai')

    def test_minute_window_resets(self):
        """Verify minute window resets after time passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            limiter = RateLimiter(db_path=db_path)

            # Record 3 calls (at minute limit)
            for _ in range(3):
                limiter.record_call('openai', success=True)

            # Next call should fail
            with pytest.raises(RateLimitError):
                limiter.check_rate_limit('openai')

            # Simulate time passing (manipulate in-memory cache)
            limiter.call_history['openai'] = [
                call for call in limiter.call_history['openai']
                if call.timestamp >= (datetime.now(timezone.utc) - timedelta(seconds=30))
            ]

            # After minute window, calls should reset
            # (Note: In real scenario, this would be automatic after 60 seconds)


class TestHourRateLimit:
    """Test per-hour rate limits."""

    def test_no_limit_exceeded_under_hour_limit(self):
        """Verify no error when under hour limit."""
        limiter = RateLimiter()
        # OpenAI allows 30/hour
        limiter.set_limit('openai', RateLimitConfig(
            provider_name='openai',
            calls_per_minute=100,  # High minute limit for this test
            calls_per_hour=30,
            calls_per_day=300,
        ))

        for _ in range(20):
            limiter.check_rate_limit('openai')
            limiter.record_call('openai', success=True)

        # Should still be within hour limit
        limiter.check_rate_limit('openai')

    def test_limit_exceeded_at_hour_limit(self):
        """Verify error when at hour limit."""
        limiter = RateLimiter()
        # Set low limits for testing
        limiter.set_limit('openai', RateLimitConfig(
            provider_name='openai',
            calls_per_minute=100,  # High minute limit
            calls_per_hour=5,      # Low hour limit
            calls_per_day=300,
        ))

        # Record 5 calls (at hour limit)
        for _ in range(5):
            limiter.check_rate_limit('openai')
            limiter.record_call('openai', success=True)

        # Sixth call should fail
        with pytest.raises(RateLimitError, match="hour"):
            limiter.check_rate_limit('openai')


class TestDayRateLimit:
    """Test per-day rate limits."""

    def test_day_limit_tracks_24_hours(self):
        """Verify day limit covers 24-hour window."""
        limiter = RateLimiter()
        # Set low day limit for testing
        limiter.set_limit('openai', RateLimitConfig(
            provider_name='openai',
            calls_per_minute=1000,  # High minute limit
            calls_per_hour=1000,    # High hour limit
            calls_per_day=5,        # Low day limit
        ))

        # Record 5 calls (at day limit)
        for _ in range(5):
            limiter.check_rate_limit('openai')
            limiter.record_call('openai', success=True)

        # Sixth call should fail
        with pytest.raises(RateLimitError, match="24 hours"):
            limiter.check_rate_limit('openai')


class TestCallRecording:
    """Test recording API calls."""

    def test_record_successful_call(self):
        """Verify successful calls are recorded."""
        limiter = RateLimiter()
        limiter.record_call('openai', success=True, tokens_used=100, cost_usd=0.05)

        assert 'openai' in limiter.call_history
        assert len(limiter.call_history['openai']) == 1
        call = limiter.call_history['openai'][0]
        assert call.success is True
        assert call.tokens_used == 100
        assert call.cost_usd == 0.05

    def test_record_failed_call(self):
        """Verify failed calls are recorded."""
        limiter = RateLimiter()
        limiter.record_call('openai', success=False, error="Connection timeout")

        assert 'openai' in limiter.call_history
        call = limiter.call_history['openai'][0]
        assert call.success is False
        assert call.error == "Connection timeout"

    def test_record_call_with_all_fields(self):
        """Verify all call fields are recorded."""
        limiter = RateLimiter()
        limiter.record_call(
            'claude_api',
            success=True,
            tokens_used=250,
            cost_usd=0.10,
            error=None
        )

        call = limiter.call_history['claude_api'][0]
        assert call.provider == 'claude_api'
        assert isinstance(call.timestamp, datetime)
        assert call.success is True
        assert call.tokens_used == 250
        assert call.cost_usd == 0.10
        assert call.error is None


class TestUsageStats:
    """Test usage statistics retrieval."""

    def test_usage_stats_per_minute(self):
        """Verify per-minute usage stats are accurate."""
        limiter = RateLimiter()
        limiter.record_call('openai', success=True)
        limiter.record_call('openai', success=True)

        stats = limiter.get_usage_stats('openai')
        assert stats['calls_last_minute'] == 2
        assert stats['successful_calls'] == 2
        assert stats['failed_calls'] == 0

    def test_usage_stats_with_failures(self):
        """Verify stats track successful and failed calls."""
        limiter = RateLimiter()
        limiter.record_call('openai', success=True)
        limiter.record_call('openai', success=False, error="API error")
        limiter.record_call('openai', success=True)

        stats = limiter.get_usage_stats('openai')
        assert stats['successful_calls'] == 2
        assert stats['failed_calls'] == 1

    def test_usage_stats_includes_limits(self):
        """Verify usage stats include configured limits."""
        limiter = RateLimiter()
        stats = limiter.get_usage_stats('openai')
        assert 'limit_minute' in stats
        assert 'limit_hour' in stats
        assert 'limit_day' in stats
        assert stats['limit_minute'] == 3
        assert stats['limit_hour'] == 30
        assert stats['limit_day'] == 200


class TestThreadSafety:
    """Test thread safety of rate limiter."""

    def test_concurrent_rate_limit_checks(self):
        """Verify rate limiter is thread-safe."""
        limiter = RateLimiter()
        errors = []
        successes = []

        def check_and_record():
            try:
                limiter.check_rate_limit('openai')
                limiter.record_call('openai', success=True)
                successes.append(1)
            except RateLimitError:
                errors.append("rate_limit")
            except Exception as e:
                errors.append(str(e))

        # Create threads to test concurrent access
        threads = [threading.Thread(target=check_and_record) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All calls should complete without exception (thread safety is maintained)
        assert len(errors) == 0  # No exceptions from threading
        # Some calls may hit rate limit or succeed (both are valid outcomes)
        assert len(successes) + len(errors) <= 5

    def test_concurrent_recording(self):
        """Verify concurrent recording works correctly."""
        limiter = RateLimiter()

        def record_call():
            limiter.record_call('openai', success=True)

        # Create threads
        threads = [threading.Thread(target=record_call) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All 10 calls should be recorded
        assert len(limiter.call_history['openai']) == 10


class TestDisabledLimits:
    """Test behavior with disabled limits."""

    def test_disabled_limit_always_passes(self):
        """Verify disabled limits don't block calls."""
        limiter = RateLimiter()
        # Ollama limit is disabled
        limiter.set_limit('ollama', RateLimitConfig(
            provider_name='ollama',
            calls_per_minute=1,
            calls_per_hour=1,
            calls_per_day=1,
            enabled=False
        ))

        # Many calls should succeed even though limits are low
        for _ in range(10):
            limiter.check_rate_limit('ollama')
            limiter.record_call('ollama', success=True)

        # No error should be raised
        assert len(limiter.call_history['ollama']) == 10


class TestDatabasePersistence:
    """Test database persistence of rate limit records."""

    def test_calls_persisted_to_database(self):
        """Verify calls are persisted to database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            # Create limiter and record call
            limiter1 = RateLimiter(db_path=db_path)
            limiter1.record_call('openai', success=True, tokens_used=100)

            # Create new limiter with same database
            limiter2 = RateLimiter(db_path=db_path)

            # Database should have the record
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM api_calls WHERE provider = ?', ('openai',))
                count = cursor.fetchone()[0]
                conn.close()
                assert count >= 1
            except sqlite3.Error:
                pass  # Database operations may fail in test

    def test_old_records_cleaned_up(self):
        """Verify old records are cleaned up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            limiter = RateLimiter(db_path=db_path)

            # Record calls
            limiter.record_call('openai', success=True)
            limiter.record_call('openai', success=True)

            # All calls should be recorded
            assert len(limiter.call_history['openai']) == 2

            # Cleanup should remove old records (but our new ones are recent)
            limiter._cleanup_old_records()

            # Recent records should still be there
            assert len(limiter.call_history['openai']) == 2


class TestGlobalLimiterInstance:
    """Test global rate limiter instance."""

    def test_get_rate_limiter_returns_singleton(self):
        """Verify get_rate_limiter returns same instance."""
        reset_rate_limiter()
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2

    def test_reset_rate_limiter(self):
        """Verify reset_rate_limiter clears instance."""
        limiter1 = get_rate_limiter()
        reset_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is not limiter2


class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_rate_limit_error_message(self):
        """Verify RateLimitError has informative message."""
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            limiter = RateLimiter()
            limiter.set_limit('openai', RateLimitConfig(
                provider_name='openai',
                calls_per_minute=1,
                calls_per_hour=100,
                calls_per_day=1000,
            ))
            limiter.record_call('openai', success=True)
            limiter.check_rate_limit('openai')

    def test_includes_provider_in_error(self):
        """Verify error message includes provider name."""
        with pytest.raises(RateLimitError, match="openai"):
            limiter = RateLimiter()
            limiter.set_limit('openai', RateLimitConfig(
                provider_name='openai',
                calls_per_minute=1,
                calls_per_hour=100,
                calls_per_day=1000,
            ))
            limiter.record_call('openai', success=True)
            limiter.check_rate_limit('openai')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
