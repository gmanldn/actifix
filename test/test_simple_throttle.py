#!/usr/bin/env python3
"""Simple throttle test without full actifix integration."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from actifix.raise_af import TicketPriority
from actifix.security.ticket_throttler import TicketThrottler, ThrottleConfig

# Create a fresh throttler with test config
config = ThrottleConfig(
    max_p2_tickets_per_hour=3,
    max_p3_tickets_per_4h=2,
    max_p4_tickets_per_day=1,
    emergency_ticket_threshold=10,
    emergency_window_minutes=1,
    enabled=True,
)

throttler = TicketThrottler(config=config)

print("Testing throttler directly (without record_error)...")
print("\nTest 1: P0 should never be throttled")
for i in range(5):
    try:
        throttler.check_throttle(TicketPriority.P0, f"TestError{i}")
        print(f"  P0 ticket {i+1}: ✓ ALLOWED")
    except Exception as e:
        print(f"  P0 ticket {i+1}: ✗ BLOCKED - {e}")

print("\nTest 2: P2 should be throttled after 3")
for i in range(5):
    try:
        throttler.check_throttle(TicketPriority.P2, f"TestError{i}")
        print(f"  P2 ticket {i+1}: ✓ ALLOWED")
        # Simulate ticket creation by recording it
        from datetime import datetime, timezone
        throttler.record_ticket(TicketPriority.P2, f"TICKET-{i}", f"TestError{i}")
    except Exception as e:
        print(f"  P2 ticket {i+1}: ✗ THROTTLED - {e}")

print("\nThrottle stats:")
stats = throttler.get_throttle_stats()
print(f"  P2 last hour: {stats['P2']['count_last_hour']}/{stats['P2']['limit_per_hour']}")
print(f"  Emergency: {stats['emergency_brake']['recent_count']}/{stats['emergency_brake']['threshold']}")
