#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticket Throttler - Prevent excessive ticket creation to avoid ticket floods.

Implements ticket-specific rate limiting with:
- Priority-based throttling (P2, P3, P4 have different limits)
- Time-window enforcement (per hour, per 4 hours, per day)
- Emergency brake for ticket floods (>200 tickets in 1 minute)
- Thread-safe enforcement
- Persistent state tracking

This prevents:
1. Accidental ticket floods from loops or recursive errors
2. System overload from too many tickets
3. Database bloat from excessive ticket creation

Version: 1.0.0
"""

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List

from ..raise_af import TicketPriority


class TicketThrottleError(Exception):
    """Raised when ticket creation would exceed throttling limits."""
    pass


@dataclass
class ThrottleConfig:
    """Configuration for ticket throttling limits."""

    # Priority-based limits
    max_p2_tickets_per_hour: int = 15
    max_p3_tickets_per_4h: int = 5
    max_p4_tickets_per_day: int = 2

    # Emergency brake
    emergency_ticket_threshold: int = 200  # Max tickets in emergency window
    emergency_window_minutes: int = 1  # Emergency window duration

    # P0 and P1 are never throttled - they're critical
    enabled: bool = True


class TicketThrottler:
    """
    Thread-safe ticket throttler to prevent excessive ticket creation.

    Enforces per-priority rate limits and emergency brake for ticket floods.
    """

    def __init__(self, config: Optional[ThrottleConfig] = None, db_path: Optional[str] = None):
        """Initialize the ticket throttler.

        Args:
            config: Throttle configuration (uses defaults if None)
            db_path: Path to SQLite database for tracking tickets
        """
        self.config = config or ThrottleConfig()
        self.db_path = db_path or self._get_default_db_path()
        self.lock = threading.RLock()
        self.ticket_history: Dict[str, List[datetime]] = {}  # In-memory cache
        self._init_database()

    def _get_default_db_path(self) -> str:
        """Get default database path for throttle tracking data."""
        from ..state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'ticket_throttle.db')

    def _init_database(self) -> None:
        """Initialize database for ticket throttle tracking."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # Create ticket throttle tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_creations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    priority TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ticket_id TEXT,
                    error_type TEXT,
                    CHECK (priority IN ('P0', 'P1', 'P2', 'P3', 'P4'))
                )
            ''')

            # Create index for efficient queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticket_creations_priority_timestamp
                ON ticket_creations(priority, timestamp)
            ''')

            # Create index for emergency brake queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticket_creations_timestamp
                ON ticket_creations(timestamp)
            ''')

            conn.commit()
            conn.close()
        except sqlite3.Error:
            # Database errors shouldn't block operation
            pass

    def check_throttle(self, priority: TicketPriority, error_type: str = "unknown") -> None:
        """Check if creating a ticket would exceed throttle limits.

        Args:
            priority: Priority level of the ticket to create
            error_type: Type of error (for logging)

        Raises:
            TicketThrottleError: If throttle limit would be exceeded
        """
        if not self.config.enabled:
            return

        with self.lock:
            now = datetime.now(timezone.utc)

            # EMERGENCY BRAKE: Check total ticket count in emergency window
            # Applies to all priorities
            emergency_window_start = now - timedelta(minutes=self.config.emergency_window_minutes)
            total_recent = sum(
                1
                for priority_key in ("P2", "P3", "P4")
                for ts in self.ticket_history.get(priority_key, [])
                if ts >= emergency_window_start
            )

            if total_recent >= self.config.emergency_ticket_threshold:
                raise TicketThrottleError(
                    f"EMERGENCY BRAKE: {total_recent} tickets created in last "
                    f"{self.config.emergency_window_minutes} minute(s) "
                    f"(threshold: {self.config.emergency_ticket_threshold}). "
                    f"Ticket creation temporarily blocked to prevent flood."
                )

            # P0 and P1 are NEVER throttled - they're critical
            if priority in (TicketPriority.P0, TicketPriority.P1):
                return

            # Priority-specific throttling
            priority_str = priority.value

            if priority == TicketPriority.P2:
                # P2: Max 15 per hour
                hour_ago = now - timedelta(hours=1)
                count = self._count_tickets_since(priority_str, hour_ago)

                if count >= self.config.max_p2_tickets_per_hour:
                    raise TicketThrottleError(
                        f"P2 ticket throttle exceeded: {count}/{self.config.max_p2_tickets_per_hour} "
                        f"tickets in last hour. Wait before creating more P2 tickets."
                    )

            elif priority == TicketPriority.P3:
                # P3: Max 5 per 4 hours
                four_hours_ago = now - timedelta(hours=4)
                count = self._count_tickets_since(priority_str, four_hours_ago)

                if count >= self.config.max_p3_tickets_per_4h:
                    raise TicketThrottleError(
                        f"P3 ticket throttle exceeded: {count}/{self.config.max_p3_tickets_per_4h} "
                        f"tickets in last 4 hours. Wait before creating more P3 tickets."
                    )

            elif priority == TicketPriority.P4:
                # P4: Max 2 per day
                day_ago = now - timedelta(days=1)
                count = self._count_tickets_since(priority_str, day_ago)

                if count >= self.config.max_p4_tickets_per_day:
                    raise TicketThrottleError(
                        f"P4 ticket throttle exceeded: {count}/{self.config.max_p4_tickets_per_day} "
                        f"tickets in last 24 hours. Wait before creating more P4 tickets."
                    )

    def record_ticket(
        self,
        priority: TicketPriority,
        ticket_id: str,
        error_type: str = "unknown"
    ) -> None:
        """Record a ticket creation for throttle tracking.

        Args:
            priority: Priority level of the ticket
            ticket_id: Ticket ID
            error_type: Type of error
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            priority_str = priority.value

            # Update in-memory cache
            if priority_str not in self.ticket_history:
                self.ticket_history[priority_str] = []
            self.ticket_history[priority_str].append(now)

            # Persist to database
            self._persist_ticket(priority_str, now, ticket_id, error_type)

            # Clean up old records
            self._cleanup_old_records()

    def get_throttle_stats(self) -> Dict[str, any]:
        """Get current throttle statistics.

        Returns:
            Dictionary with throttle stats for each priority
        """
        with self.lock:
            now = datetime.now(timezone.utc)

            stats = {
                'emergency_brake': {
                    'window_minutes': self.config.emergency_window_minutes,
                    'threshold': self.config.emergency_ticket_threshold,
                    'recent_count': self._count_all_tickets_since(
                        now - timedelta(minutes=self.config.emergency_window_minutes)
                    ),
                },
                'P2': {
                    'limit_per_hour': self.config.max_p2_tickets_per_hour,
                    'count_last_hour': self._count_tickets_since('P2', now - timedelta(hours=1)),
                },
                'P3': {
                    'limit_per_4h': self.config.max_p3_tickets_per_4h,
                    'count_last_4h': self._count_tickets_since('P3', now - timedelta(hours=4)),
                },
                'P4': {
                    'limit_per_day': self.config.max_p4_tickets_per_day,
                    'count_last_day': self._count_tickets_since('P4', now - timedelta(days=1)),
                },
            }

            return stats

    def _count_tickets_since(self, priority: str, since: datetime) -> int:
        """Count tickets of a specific priority since a specific time."""
        if priority not in self.ticket_history:
            return 0

        return sum(1 for ts in self.ticket_history[priority] if ts >= since)

    def _count_all_tickets_since(self, since: datetime) -> int:
        """Count all tickets regardless of priority since a specific time."""
        total = 0
        for priority in self.ticket_history.values():
            total += sum(1 for ts in priority if ts >= since)
        return total

    def _persist_ticket(self, priority: str, timestamp: datetime, ticket_id: str, error_type: str) -> None:
        """Persist a ticket creation record to database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ticket_creations
                (priority, timestamp, ticket_id, error_type)
                VALUES (?, ?, ?, ?)
            ''', (
                priority,
                timestamp.isoformat(),
                ticket_id,
                error_type,
            ))

            conn.commit()
            conn.close()
        except sqlite3.Error:
            # Database persistence failure shouldn't block operation
            pass

    def _cleanup_old_records(self) -> None:
        """Remove ticket creation records older than 24 hours."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM ticket_creations WHERE timestamp < ?
            ''', (cutoff,))

            conn.commit()
            conn.close()

            # Also clean up in-memory cache
            with self.lock:
                cutoff_dt = datetime.now(timezone.utc) - timedelta(days=1)
                for priority in self.ticket_history:
                    self.ticket_history[priority] = [
                        ts for ts in self.ticket_history[priority]
                        if ts >= cutoff_dt
                    ]

        except sqlite3.Error:
            pass


# Global throttler instance
_throttler: Optional[TicketThrottler] = None
_throttler_lock = threading.Lock()


def get_ticket_throttler(config: Optional[ThrottleConfig] = None) -> TicketThrottler:
    """Get or create the global ticket throttler instance.

    Args:
        config: Optional throttle configuration

    Returns:
        Global TicketThrottler instance
    """
    global _throttler

    if _throttler is None:
        with _throttler_lock:
            if _throttler is None:
                # Load config from ActifixConfig if not provided
                if config is None:
                    try:
                        from ..config import get_config
                        actifix_config = get_config()
                        config = ThrottleConfig(
                            max_p2_tickets_per_hour=actifix_config.max_p2_tickets_per_hour,
                            max_p3_tickets_per_4h=actifix_config.max_p3_tickets_per_4h,
                            max_p4_tickets_per_day=actifix_config.max_p4_tickets_per_day,
                            emergency_ticket_threshold=actifix_config.emergency_ticket_threshold,
                            emergency_window_minutes=actifix_config.emergency_window_minutes,
                            enabled=actifix_config.ticket_throttling_enabled,
                        )
                    except Exception:
                        # Fall back to defaults
                        config = ThrottleConfig()

                _throttler = TicketThrottler(config=config)

    return _throttler


def reset_ticket_throttler() -> None:
    """Reset the global ticket throttler (for testing)."""
    global _throttler
    with _throttler_lock:
        _throttler = None
