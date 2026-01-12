#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EventRepository - Database-backed event logging for Actifix.

Replaces AFLog.txt file-based logging with structured database storage.
Provides efficient querying, filtering, and event tracking.

Version: 2.0.0
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .database import get_database_pool, serialize_timestamp


@dataclass
class EventFilter:
    """Filter for querying events from the event_log table."""
    
    event_type: Optional[str] = None
    ticket_id: Optional[str] = None
    correlation_id: Optional[str] = None
    level: Optional[str] = None
    source: Optional[str] = None
    limit: int = 100
    offset: int = 0


class EventRepository:
    """
    Repository for event_log table operations.
    
    Provides database-backed event logging with structured querying.
    Thread-safe via connection pooling.
    """
    
    def __init__(self):
        """Initialize event repository with database pool."""
        self.pool = get_database_pool()
    
    def log_event(
        self,
        event_type: str,
        message: str,
        ticket_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        extra_json: Optional[str] = None,
        source: Optional[str] = None,
        level: str = 'INFO',
        timestamp: Optional[datetime] = None,
    ) -> Optional[int]:
        """
        Log an event to the event_log table.
        
        Args:
            event_type: Type of event (e.g., TICKET_CREATED, DISPATCH_STARTED).
            message: Human-readable message.
            ticket_id: Optional ticket ID reference.
            correlation_id: Optional correlation ID for tracing.
            extra_json: Optional JSON string of extra data.
            source: Optional source module/function.
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            timestamp: Optional timestamp (defaults to now).
        
        Returns:
            Event ID if successful, None otherwise.
        """
        try:
            ts = timestamp or datetime.now(timezone.utc)
            ts_str = serialize_timestamp(ts)

            with self.pool.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO event_log
                    (timestamp, event_type, message, ticket_id, correlation_id, extra_json, source, level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ts_str, event_type, message, ticket_id, correlation_id, extra_json, source, level)
                )
                return cursor.lastrowid
        except Exception:
            # Silently fail to avoid recursive logging errors
            return None
    
    def get_events(self, filter: Optional[EventFilter] = None) -> List[Dict[str, Any]]:
        """
        Get events from the event_log table with optional filtering.
        
        Args:
            filter: Optional filter criteria.
        
        Returns:
            List of event records as dictionaries.
        """
        if filter is None:
            filter = EventFilter()
        
        query = "SELECT * FROM event_log WHERE 1=1"
        params = []
        
        if filter.event_type:
            query += " AND event_type = ?"
            params.append(filter.event_type)
        
        if filter.ticket_id:
            query += " AND ticket_id = ?"
            params.append(filter.ticket_id)
        
        if filter.correlation_id:
            query += " AND correlation_id = ?"
            params.append(filter.correlation_id)
        
        if filter.level:
            query += " AND level = ?"
            params.append(filter.level)
        
        if filter.source:
            query += " AND source = ?"
            params.append(filter.source)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([filter.limit, filter.offset])
        
        try:
            with self.pool.connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_events_for_ticket(self, ticket_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all events associated with a specific ticket.
        
        Args:
            ticket_id: Ticket ID to query events for.
            limit: Maximum number of events to return.
        
        Returns:
            List of event records ordered by timestamp.
        """
        filter = EventFilter(ticket_id=ticket_id, limit=limit)
        return self.get_events(filter)
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent events across all types.
        
        Args:
            limit: Number of recent events to return.
        
        Returns:
            List of recent event records.
        """
        filter = EventFilter(limit=limit)
        return self.get_events(filter)
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events of a specific type.
        
        Args:
            event_type: Event type to filter by.
            limit: Maximum number of events to return.
        
        Returns:
            List of matching event records.
        """
        filter = EventFilter(event_type=event_type, limit=limit)
        return self.get_events(filter)
    
    def get_events_by_correlation(self, correlation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all events with a specific correlation ID.
        
        Args:
            correlation_id: Correlation ID to trace.
            limit: Maximum number of events to return.
        
        Returns:
            List of correlated event records.
        """
        filter = EventFilter(correlation_id=correlation_id, limit=limit)
        return self.get_events(filter)
    
    def prune_old_events(self, days_to_keep: int = 90) -> int:
        """
        Delete events older than specified days.
        
        Args:
            days_to_keep: Number of days of events to retain.
        
        Returns:
            Number of events deleted.
        """
        try:
            with self.pool.transaction() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM event_log
                    WHERE timestamp < datetime('now', ? || ' days')
                    """,
                    (f'-{days_to_keep}',)
                )
                return cursor.rowcount
        except Exception:
            return 0
    
    def get_event_count(self) -> int:
        """
        Get total count of events in the log.
        
        Returns:
            Total number of events.
        """
        try:
            with self.pool.connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM event_log")
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception:
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the event log.
        
        Returns:
            Dictionary with event statistics.
        """
        try:
            with self.pool.connection() as conn:
                # Total count
                cursor = conn.execute("SELECT COUNT(*) as total FROM event_log")
                total = cursor.fetchone()['total']
                
                # By event type
                cursor = conn.execute(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM event_log
                    GROUP BY event_type
                    ORDER BY count DESC
                    LIMIT 10
                    """
                )
                by_type = {row['event_type']: row['count'] for row in cursor.fetchall()}
                
                # By level
                cursor = conn.execute(
                    """
                    SELECT level, COUNT(*) as count
                    FROM event_log
                    GROUP BY level
                    """
                )
                by_level = {row['level']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'total': total,
                    'by_type': by_type,
                    'by_level': by_level,
                }
        except Exception:
            return {'total': 0, 'by_type': {}, 'by_level': {}}


# Global singleton instance
_global_event_repo: Optional[EventRepository] = None


def get_event_repository() -> EventRepository:
    """
    Get or create the global EventRepository instance.
    
    Returns:
        EventRepository singleton.
    """
    global _global_event_repo
    if _global_event_repo is None:
        _global_event_repo = EventRepository()
    return _global_event_repo


def reset_event_repository() -> None:
    """Reset the global EventRepository (for testing)."""
    global _global_event_repo
    _global_event_repo = None