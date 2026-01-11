#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticket Repository - Database operations for Actifix tickets

Provides CRUD operations with locking, filtering, and duplicate prevention.
Thread-safe with lease-based locking for concurrent ticket processing.

Version: 1.0.0
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..raise_af import ActifixEntry, TicketPriority
from .database import (
    get_database_pool,
    DatabasePool,
    DatabaseError,
    serialize_json_field,
    deserialize_json_field,
    serialize_timestamp,
    deserialize_timestamp,
)


@dataclass
class TicketFilter:
    """Filter criteria for querying tickets."""
    
    status: Optional[str] = None  # Open, In Progress, Completed
    priority: Optional[str] = None  # P0-P4
    owner: Optional[str] = None
    locked: Optional[bool] = None  # True for locked, False for unlocked, None for all
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    correlation_id: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class TicketLock:
    """Ticket lock information."""
    
    ticket_id: str
    locked_by: str
    locked_at: datetime
    lease_expires: datetime


class TicketRepository:
    """
    Repository for ticket database operations.
    
    Provides thread-safe CRUD operations with locking support.
    """
    
    def __init__(self, pool: Optional[DatabasePool] = None):
        """
        Initialize ticket repository.
        
        Args:
            pool: Optional database pool (uses global pool if None).
        """
        self.pool = pool or get_database_pool()
    
    def create_ticket(self, entry: ActifixEntry) -> bool:
        """
        Create a new ticket in the database.
        
        Args:
            entry: Actifix entry to create.
        
        Returns:
            True if created, False if duplicate exists.
        
        Raises:
            DatabaseError: On database errors.
        """
        with self.pool.transaction() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO tickets (
                        id, priority, error_type, message, source, run_label,
                        created_at, duplicate_guard, status, stack_trace,
                        file_context, system_state, ai_remediation_notes,
                        correlation_id, format_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.entry_id,
                        entry.priority.value,
                        entry.error_type,
                        entry.message,
                        entry.source,
                        entry.run_label,
                        serialize_timestamp(entry.created_at),
                        entry.duplicate_guard,
                        "Open",
                        entry.stack_trace,
                        serialize_json_field(entry.file_context),
                        serialize_json_field(entry.system_state),
                        entry.ai_remediation_notes,
                        entry.correlation_id,
                        entry.format_version,
                    )
                )
                return True
            except sqlite3.IntegrityError:
                # Duplicate guard violation
                return False
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get ticket by ID.
        
        Args:
            ticket_id: Ticket ID to fetch.
        
        Returns:
            Ticket data as dict, or None if not found.
        """
        with self.pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tickets WHERE id = ?",
                (ticket_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_dict(row)
    
    def get_tickets(self, filter: Optional[TicketFilter] = None) -> List[Dict[str, Any]]:
        """
        Get tickets with optional filtering.
        
        Args:
            filter: Optional filter criteria.
        
        Returns:
            List of ticket dicts.
        """
        if filter is None:
            filter = TicketFilter()
        
        # Build query
        conditions = []
        params = []
        
        if filter.status:
            conditions.append("status = ?")
            params.append(filter.status)
        
        if filter.priority:
            conditions.append("priority = ?")
            params.append(filter.priority)
        
        if filter.owner:
            conditions.append("owner = ?")
            params.append(filter.owner)
        
        if filter.locked is not None:
            if filter.locked:
                conditions.append("locked_by IS NOT NULL")
            else:
                conditions.append("locked_by IS NULL")
        
        if filter.created_after:
            conditions.append("created_at >= ?")
            params.append(serialize_timestamp(filter.created_after))
        
        if filter.created_before:
            conditions.append("created_at <= ?")
            params.append(serialize_timestamp(filter.created_before))
        
        if filter.correlation_id:
            conditions.append("correlation_id = ?")
            params.append(filter.correlation_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM tickets 
            WHERE {where_clause}
            ORDER BY 
                CASE priority 
                    WHEN 'P0' THEN 0 
                    WHEN 'P1' THEN 1 
                    WHEN 'P2' THEN 2 
                    WHEN 'P3' THEN 3 
                    WHEN 'P4' THEN 4 
                    ELSE 5 
                END,
                created_at DESC
        """
        
        if filter.limit:
            query += f" LIMIT {filter.limit} OFFSET {filter.offset}"
        
        with self.pool.connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_open_tickets(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all open tickets, sorted by priority."""
        filter = TicketFilter(status="Open", limit=limit)
        return self.get_tickets(filter)
    
    def get_completed_tickets(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all completed tickets."""
        filter = TicketFilter(status="Completed", limit=limit)
        return self.get_tickets(filter)
    
    def check_duplicate_guard(self, duplicate_guard: str) -> Optional[Dict[str, Any]]:
        """
        Check if a ticket with the same duplicate guard exists.
        
        Args:
            duplicate_guard: Duplicate guard to check.
        
        Returns:
            Ticket data if exists, None otherwise.
        """
        with self.pool.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tickets WHERE duplicate_guard = ?",
                (duplicate_guard,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_dict(row)
    
    def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update ticket fields.
        
        Args:
            ticket_id: Ticket ID to update.
            updates: Dict of field names to new values.
        
        Returns:
            True if updated, False if not found.
        """
        if not updates:
            return False
        
        # Add updated_at timestamp
        updates['updated_at'] = serialize_timestamp(datetime.now(timezone.utc))
        
        # Build update query
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        params = list(updates.values()) + [ticket_id]
        
        with self.pool.transaction() as conn:
            cursor = conn.execute(
                f"UPDATE tickets SET {set_clause} WHERE id = ?",
                params
            )
            return cursor.rowcount > 0
    
    def mark_complete(
        self,
        ticket_id: str,
        summary: Optional[str] = None,
    ) -> bool:
        """
        Mark ticket as completed.
        
        Args:
            ticket_id: Ticket ID to complete.
            summary: Optional completion summary.
        
        Returns:
            True if completed, False if not found.
        """
        updates = {
            'status': 'Completed',
            'completed': 1,
            'documented': 1,
            'functioning': 1,
            'tested': 1,
            'locked_by': None,
            'locked_at': None,
            'lease_expires': None,
        }
        
        if summary:
            updates['completion_summary'] = summary
        
        return self.update_ticket(ticket_id, updates)
    
    def acquire_lock(
        self,
        ticket_id: str,
        locked_by: str,
        lease_duration: timedelta = timedelta(hours=1),
    ) -> Optional[TicketLock]:
        """
        Acquire lock on a ticket with lease expiry.
        
        Args:
            ticket_id: Ticket ID to lock.
            locked_by: Identifier for lock holder.
            lease_duration: How long the lock is valid.
        
        Returns:
            TicketLock if acquired, None if already locked or not found.
        """
        now = datetime.now(timezone.utc)
        lease_expires = now + lease_duration
        
        with self.pool.transaction() as conn:
            # Check if ticket exists and is not locked (or lease expired)
            cursor = conn.execute(
                """
                SELECT id, locked_by, locked_at, lease_expires 
                FROM tickets 
                WHERE id = ? AND (
                    locked_by IS NULL 
                    OR lease_expires < ?
                )
                """,
                (ticket_id, serialize_timestamp(now))
            )
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            # Acquire lock
            conn.execute(
                """
                UPDATE tickets 
                SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress'
                WHERE id = ?
                """,
                (
                    locked_by,
                    serialize_timestamp(now),
                    serialize_timestamp(lease_expires),
                    ticket_id,
                )
            )
            
            return TicketLock(
                ticket_id=ticket_id,
                locked_by=locked_by,
                locked_at=now,
                lease_expires=lease_expires,
            )
    
    def release_lock(self, ticket_id: str, locked_by: str) -> bool:
        """
        Release lock on a ticket.
        
        Args:
            ticket_id: Ticket ID to unlock.
            locked_by: Must match current lock holder.
        
        Returns:
            True if released, False if not locked or wrong holder.
        """
        with self.pool.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE tickets 
                SET locked_by = NULL, locked_at = NULL, lease_expires = NULL, status = 'Open'
                WHERE id = ? AND locked_by = ?
                """,
                (ticket_id, locked_by)
            )
            return cursor.rowcount > 0
    
    def renew_lock(
        self,
        ticket_id: str,
        locked_by: str,
        lease_duration: timedelta = timedelta(hours=1),
    ) -> Optional[TicketLock]:
        """
        Renew lease on existing lock.
        
        Args:
            ticket_id: Ticket ID.
            locked_by: Must match current lock holder.
            lease_duration: New lease duration.
        
        Returns:
            Updated TicketLock if renewed, None if not locked or wrong holder.
        """
        now = datetime.now(timezone.utc)
        new_expiry = now + lease_duration
        
        with self.pool.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE tickets 
                SET lease_expires = ?
                WHERE id = ? AND locked_by = ?
                """,
                (serialize_timestamp(new_expiry), ticket_id, locked_by)
            )
            
            if cursor.rowcount == 0:
                return None
            
            return TicketLock(
                ticket_id=ticket_id,
                locked_by=locked_by,
                locked_at=now,
                lease_expires=new_expiry,
            )
    
    def get_expired_locks(self) -> List[Dict[str, Any]]:
        """Get tickets with expired locks."""
        now = datetime.now(timezone.utc)
        
        with self.pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM tickets 
                WHERE locked_by IS NOT NULL AND lease_expires < ?
                """,
                (serialize_timestamp(now),)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
    
    def cleanup_expired_locks(self) -> int:
        """
        Cleanup expired locks automatically.
        
        Returns:
            Number of locks cleaned up.
        """
        now = datetime.now(timezone.utc)
        
        with self.pool.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE tickets 
                SET locked_by = NULL, locked_at = NULL, lease_expires = NULL, status = 'Open'
                WHERE locked_by IS NOT NULL AND lease_expires < ?
                """,
                (serialize_timestamp(now),)
            )
            return cursor.rowcount
    
    def get_and_lock_next_ticket(
        self,
        locked_by: str,
        lease_duration: timedelta = timedelta(hours=1),
        priority_filter: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically get the next highest-priority unlocked ticket and lock it.
        
        This is the recommended method for concurrent AI agents to claim work.
        It ensures only one agent gets each ticket.
        
        Args:
            locked_by: Identifier for lock holder (e.g., "agent-1", "agent-2").
            lease_duration: How long the lock is valid.
            priority_filter: Optional list of priorities to consider (e.g., ["P0", "P1"]).
        
        Returns:
            Ticket data if acquired, None if no unlocked tickets available.
        
        Example:
            >>> repo = get_ticket_repository()
            >>> ticket = repo.get_and_lock_next_ticket("agent-1")
            >>> if ticket:
            >>>     # Process ticket...
            >>>     repo.mark_complete(ticket['id'], "Fixed the issue")
        """
        now = datetime.now(timezone.utc)
        lease_expires = now + lease_duration
        
        with self.pool.transaction() as conn:
            # First, cleanup any expired locks to make tickets available
            conn.execute(
                """
                UPDATE tickets 
                SET locked_by = NULL, locked_at = NULL, lease_expires = NULL, status = 'Open'
                WHERE locked_by IS NOT NULL AND lease_expires < ?
                """,
                (serialize_timestamp(now),)
            )
            
            # Build query to find next available ticket
            priority_condition = ""
            params = []
            
            if priority_filter:
                placeholders = ",".join("?" for _ in priority_filter)
                priority_condition = f"AND priority IN ({placeholders})"
                params.extend(priority_filter)
            
            # Find highest priority unlocked ticket
            query = f"""
                SELECT id FROM tickets 
                WHERE status = 'Open' 
                AND locked_by IS NULL
                {priority_condition}
                ORDER BY 
                    CASE priority 
                        WHEN 'P0' THEN 0 
                        WHEN 'P1' THEN 1 
                        WHEN 'P2' THEN 2 
                        WHEN 'P3' THEN 3 
                        WHEN 'P4' THEN 4 
                        ELSE 5 
                    END,
                    created_at ASC
                LIMIT 1
            """
            
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            ticket_id = row['id']
            
            # Lock the ticket
            conn.execute(
                """
                UPDATE tickets 
                SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress'
                WHERE id = ?
                """,
                (
                    locked_by,
                    serialize_timestamp(now),
                    serialize_timestamp(lease_expires),
                    ticket_id,
                )
            )
            
            # Fetch and return the full ticket
            cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            ticket_row = cursor.fetchone()
            
            return self._row_to_dict(ticket_row)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get ticket statistics.
        
        Returns:
            Dict with counts and breakdowns.
        """
        with self.pool.connection() as conn:
            # Total counts
            cursor = conn.execute("SELECT COUNT(*) as total FROM tickets")
            total = cursor.fetchone()['total']
            
            # By status
            cursor = conn.execute(
                "SELECT status, COUNT(*) as count FROM tickets GROUP BY status"
            )
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # By priority
            cursor = conn.execute(
                "SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority"
            )
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            # Locked count
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM tickets WHERE locked_by IS NOT NULL"
            )
            locked = cursor.fetchone()['count']
            
            return {
                'total': total,
                'open': by_status.get('Open', 0),
                'in_progress': by_status.get('In Progress', 0),
                'completed': by_status.get('Completed', 0),
                'by_priority': {
                    'P0': by_priority.get('P0', 0),
                    'P1': by_priority.get('P1', 0),
                    'P2': by_priority.get('P2', 0),
                    'P3': by_priority.get('P3', 0),
                    'P4': by_priority.get('P4', 0),
                },
                'locked': locked,
            }
    
    def delete_ticket(self, ticket_id: str) -> bool:
        """
        Delete ticket (use with caution).
        
        Args:
            ticket_id: Ticket ID to delete.
        
        Returns:
            True if deleted, False if not found.
        """
        with self.pool.transaction() as conn:
            cursor = conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            return cursor.rowcount > 0
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to dict."""
        return {
            'id': row['id'],
            'priority': row['priority'],
            'error_type': row['error_type'],
            'message': row['message'],
            'source': row['source'],
            'run_label': row['run_label'],
            'created_at': deserialize_timestamp(row['created_at']),
            'updated_at': deserialize_timestamp(row['updated_at']),
            'duplicate_guard': row['duplicate_guard'],
            'status': row['status'],
            'owner': row['owner'],
            'locked_by': row['locked_by'],
            'locked_at': deserialize_timestamp(row['locked_at']),
            'lease_expires': deserialize_timestamp(row['lease_expires']),
            'branch': row['branch'],
            'stack_trace': row['stack_trace'],
            'file_context': deserialize_json_field(row['file_context']),
            'system_state': deserialize_json_field(row['system_state']),
            'ai_remediation_notes': row['ai_remediation_notes'],
            'correlation_id': row['correlation_id'],
            'completion_summary': row['completion_summary'],
            'format_version': row['format_version'],
            'documented': bool(row['documented']),
            'functioning': bool(row['functioning']),
            'tested': bool(row['tested']),
            'completed': bool(row['completed']),
        }


# Global repository instance
_global_repo: Optional[TicketRepository] = None


def get_ticket_repository(pool: Optional[DatabasePool] = None) -> TicketRepository:
    """
    Get or create global ticket repository.
    
    Args:
        pool: Optional database pool override.
    
    Returns:
        Ticket repository instance.
    """
    global _global_repo
    
    if _global_repo is None or (pool and _global_repo.pool != pool):
        _global_repo = TicketRepository(pool=pool)
    
    return _global_repo


def reset_ticket_repository() -> None:
    """Reset global repository (for testing)."""
    global _global_repo
    _global_repo = None
