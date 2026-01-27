#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticket Repository - Database operations for Actifix tickets

Provides CRUD operations with locking, filtering, and duplicate prevention.
Thread-safe with lease-based locking for concurrent ticket processing.

LEASE-BASED LOCKING MECHANISM:

This module implements a sophisticated lease-based distributed locking pattern
that is essential for concurrent ticket processing in a multi-agent environment.

Why Lease-Based Locking?
------------------------
Traditional persistent locks can deadlock if a process crashes while holding a lock.
Lease-based locking prevents this through automatic expiry:

1. When a lock is acquired, it has a fixed duration (default: 1 hour)
2. If the lock holder doesn't renew it before expiry, the lock automatically expires
3. Other processes can then acquire the same ticket, preventing deadlock scenarios
4. Lock holders must periodically renew locks on tickets they're still processing

Lock Acquisition Strategy:
--------------------------
The lock acquisition uses SQLite's IMMEDIATE transactions to prevent TOCTOU
(Time-Of-Check-Time-Of-Use) race conditions:

1. Start an IMMEDIATE transaction (acquires write lock immediately)
2. Check ticket status and expiry time atomically
3. Update lock fields only if conditions still hold
4. Commit atomic transaction - this prevents other threads from interleaving

Key Properties:
- ATOMIC: Lock check and acquisition are indivisible
- SAFE: No TOCTOU race conditions between threads
- RELIABLE: Automatic cleanup of stale locks prevents deadlock
- FAIR: get_and_lock_next_ticket() ensures each thread gets different tickets

Default Lease Duration (1 Hour):
--------------------------------
The 1-hour default was chosen based on these considerations:

1. LONG ENOUGH: Gives typical AI agents sufficient time to process complex tickets
   - Most ticket processing takes 5-30 minutes
   - 1 hour provides 2-12x safety margin
   - Accounts for occasional network delays

2. SHORT ENOUGH: Prevents blocking for too long if a process crashes
   - System can recover from failed agents within 1 hour
   - Doesn't leave tickets locked for days/weeks
   - Balances availability vs. processing safety

3. CONFIGURABLE: Can be tuned per-deployment via lease_duration parameter
   - Fast agents can renew frequently
   - Slow systems can use longer leases
   - Emergency overrides possible with shorter leases

Lock Lifecycle Example:
-----------------------
>>> # Agent 1 acquires lock
>>> lock = repo.acquire_lock("ACT-20260114-ABC12", "agent-1", lease_duration=timedelta(hours=1))
>>> # Agent works on ticket... processing takes 30 minutes
>>> # Agent renews lock before it expires (e.g., after 50 minutes)
>>> renewed = repo.renew_lock("ACT-20260114-ABC12", "agent-1", lease_duration=timedelta(hours=1))
>>> # Agent finishes and completes ticket
>>> repo.release_lock("ACT-20260114-ABC12", "agent-1")
>>> # If agent crashed without releasing, lock auto-expires after 1 hour
>>> # Then other agents can acquire it via get_and_lock_next_ticket()

TICKET THROTTLING & LIMITS:

The repository enforces several configurable limits to prevent DoS attacks
and system overload:

1. Message Length Limit (max_ticket_message_length)
   - Prevents extremely long error messages from consuming disk space
   - Default: 5000 characters
   - Configurable via ACTIFIX_MAX_MESSAGE_LENGTH env var

2. File Context Size Limit (max_file_context_size_bytes)
   - Prevents large captured file context from bloating the database
   - Default: 1MB
   - Configurable via ACTIFIX_MAX_FILE_CONTEXT_BYTES env var
   - Enforced at both create and update time

3. Open Tickets Limit (max_open_tickets)
   - Prevents system from accumulating too many unprocessed tickets
   - Default: 10000
   - Configurable via ACTIFIX_MAX_OPEN_TICKETS env var
   - Enforced at create time to prevent queue overflow

All limits are validated against configuration and raise appropriate exceptions
when exceeded, providing clear error messages with actual vs. maximum values.

Version: 1.0.0
"""

import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..raise_af import ActifixEntry, TicketPriority
from ..config import ActifixConfig, get_config
from .database import (
    get_database_pool,
    DatabasePool,
    DatabaseError,
    serialize_json_field,
    deserialize_json_field,
    serialize_timestamp,
    deserialize_timestamp,
    log_database_audit,
)


_SECTION_HEADER_PATTERN = re.compile(r"^[A-Za-z0-9 _/.-]{2,60}:\s*$")


def _extract_completion_section(completion_notes: str, header: str) -> str:
    header_pattern = re.compile(rf"^{re.escape(header)}\s*:\s*(.*)$", re.IGNORECASE)
    lines = completion_notes.splitlines()
    collecting = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if collecting:
                break
            continue
        match = header_pattern.match(stripped)
        if match:
            collecting = True
            remainder = match.group(1).strip()
            if remainder:
                collected.append(remainder)
            continue
        if collecting:
            if _SECTION_HEADER_PATTERN.match(stripped):
                break
            item = stripped.lstrip("-*").strip()
            if item:
                collected.append(item)

    return " ".join(collected).strip()


def _extract_completion_files(completion_notes: str) -> list[str]:
    header_pattern = re.compile(
        r"^(files?(?:\s+changed|\s+touched|\s+modified|\s+updated)?|paths?)\s*:\s*(.*)$",
        re.IGNORECASE,
    )
    lines = completion_notes.splitlines()
    collecting = False
    files: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if collecting:
                break
            continue
        match = header_pattern.match(stripped)
        if match:
            collecting = True
            remainder = match.group(2).strip()
            if remainder:
                files.extend([part.strip() for part in remainder.split(",") if part.strip()])
            continue
        if collecting:
            if _SECTION_HEADER_PATTERN.match(stripped):
                break
            item = stripped.lstrip("-*").strip()
            if item:
                files.append(item)

    return files


def _normalize_completion_file_entry(entry: str) -> str:
    lowered = entry.lower()
    for prefix in ("deleted:", "removed:", "renamed:", "moved:", "added:", "updated:"):
        if lowered.startswith(prefix):
            return entry[len(prefix):].strip()
    return entry.strip()


def _looks_like_path(value: str) -> bool:
    if not value:
        return False
    if value in {"Makefile", "Dockerfile"}:
        return True
    return "/" in value or "." in Path(value).name


# DoS Prevention: Length limits for ticket fields
MAX_MESSAGE_LENGTH = 5000  # Maximum message length (aligned with default config)
MAX_SOURCE_LENGTH = 500     # Prevent extremely long source file paths
MAX_ERROR_TYPE_LENGTH = 200 # Error type names have reasonable bounds
MAX_STACK_TRACE_LENGTH = 50000  # Stack traces can be large but not unlimited
MAX_FIELD_LENGTH = 50000   # General field limit for other text fields


class FieldLengthError(ValueError):
    """Raised when a field exceeds maximum allowed length."""
    pass


class OpenTicketLimitExceededError(Exception):
    """Raised when attempting to create a ticket and open ticket limit is exceeded."""
    pass


def _validate_field_length(value: Optional[str], max_length: int, field_name: str) -> None:
    """Validate that a field doesn't exceed maximum length.

    Args:
        value: The field value to validate.
        max_length: Maximum allowed length.
        field_name: Name of the field for error messages.

    Raises:
        FieldLengthError: If value exceeds max_length.
    """
    if value and len(value) > max_length:
        raise FieldLengthError(
            f"Field '{field_name}' exceeds maximum length of {max_length} chars "
            f"(got {len(value)} chars)"
        )


def _validate_file_context_size(
    file_context: Optional[Dict[str, str]],
    max_size_bytes: int,
    field_name: str = "file_context"
) -> None:
    """Validate that file context doesn't exceed maximum size.

    Args:
        file_context: The file context dict to validate.
        max_size_bytes: Maximum allowed size in bytes.
        field_name: Name of the field for error messages.

    Raises:
        FieldLengthError: If serialized size exceeds max_size_bytes.
    """
    if not file_context:
        return

    # Serialize to JSON to get actual storage size
    json_str = serialize_json_field(file_context)
    size_bytes = len(json_str.encode('utf-8'))

    if size_bytes > max_size_bytes:
        raise FieldLengthError(
            f"Field '{field_name}' exceeds maximum size of {max_size_bytes} bytes "
            f"(got {size_bytes} bytes, {len(file_context)} files)"
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


def _get_user_context() -> str:
    """Get current user context for audit logging."""
    return os.environ.get("ACTIFIX_USER") or os.environ.get("USER") or "unknown"


class TicketRepository:
    """
    Repository for ticket database operations.
    
    Provides thread-safe CRUD operations with locking support.
    """
    
    def __init__(self, pool: Optional[DatabasePool] = None, config: Optional[ActifixConfig] = None):
        """
        Initialize ticket repository.

        Args:
            pool: Optional database pool (uses global pool if None).
            config: Optional configuration (uses global config if None).
        """
        self.pool = pool or get_database_pool()
        self.config = config or get_config()
    
    def create_ticket(self, entry: ActifixEntry) -> bool:
        """
        Create a new ticket in the database.

        Args:
            entry: Actifix entry to create.

        Returns:
            True if created, False if duplicate exists.

        Raises:
            FieldLengthError: If any field exceeds maximum length.
            OpenTicketLimitExceededError: If open ticket limit is exceeded.
            DatabaseError: On database errors.
        """
        # Validate field lengths to prevent DoS attacks
        _validate_field_length(entry.message, self.config.max_ticket_message_length, "message")
        _validate_field_length(entry.source, MAX_SOURCE_LENGTH, "source")
        _validate_field_length(entry.error_type, MAX_ERROR_TYPE_LENGTH, "error_type")
        _validate_field_length(entry.stack_trace, MAX_STACK_TRACE_LENGTH, "stack_trace")
        _validate_field_length(entry.ai_remediation_notes, MAX_FIELD_LENGTH, "ai_remediation_notes")

        # Validate file context size
        if entry.file_context:
            _validate_file_context_size(
                entry.file_context,
                self.config.max_file_context_size_bytes,
                "file_context"
            )

        success = False

        try:
            with self.pool.transaction() as conn:
                # Check if we would exceed the open ticket limit
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM tickets WHERE status = 'Open' AND deleted = 0"
                )
                open_count = cursor.fetchone()['count']

                if open_count >= self.config.max_open_tickets:
                    raise OpenTicketLimitExceededError(
                        f"Cannot create new ticket: Open ticket limit ({self.config.max_open_tickets}) "
                        f"has been reached. Currently {open_count} open tickets exist. "
                        f"Please complete or close some tickets before creating new ones."
                    )
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
            success = True
        except sqlite3.IntegrityError:
            # Duplicate guard violation
            success = False

        # Log ticket creation to audit log (after transaction commits)
        if success:
            log_database_audit(
                pool=self.pool,
                table_name="tickets",
                operation="INSERT",
                record_id=entry.entry_id,
                user_context=_get_user_context(),
                new_values={
                    "id": entry.entry_id,
                    "priority": entry.priority.value,
                    "error_type": entry.error_type,
                    "message": entry.message[:100],  # Truncate for audit log
                    "source": entry.source,
                    "status": "Open",
                },
                change_description=f"Created ticket: {entry.message[:60]}"
            )

        return success
    
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
        conditions = ["deleted = 0"]  # Exclude soft-deleted tickets by default
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

        where_clause = " AND ".join(conditions)

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

        Raises:
            FieldLengthError: If any field exceeds maximum length.
        """
        if not updates:
            return False

        # Validate field lengths to prevent DoS attacks
        field_limits = {
            "message": self.config.max_ticket_message_length,
            "source": MAX_SOURCE_LENGTH,
            "error_type": MAX_ERROR_TYPE_LENGTH,
            "stack_trace": MAX_STACK_TRACE_LENGTH,
            "ai_remediation_notes": MAX_FIELD_LENGTH,
        }

        for field_name, max_length in field_limits.items():
            if field_name in updates:
                _validate_field_length(updates[field_name], max_length, field_name)

        # Validate file_context size if present
        if "file_context" in updates and updates["file_context"]:
            _validate_file_context_size(
                updates["file_context"],
                self.config.max_file_context_size_bytes,
                "file_context"
            )

        old_values = {}
        success = False

        # Use BEGIN IMMEDIATE to acquire write locks upfront and prevent
        # lock escalation conflicts in concurrent scenarios
        with self.pool.transaction(immediate=True) as conn:
            # Get current ticket values for audit log
            cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            current_row = cursor.fetchone()

            if current_row is None:
                return False

            # Capture old values
            for key in updates.keys():
                if key in current_row.keys():
                    old_values[key] = current_row[key]

            # Add updated_at timestamp
            updates['updated_at'] = serialize_timestamp(datetime.now(timezone.utc))

            # Build update query
            set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
            params = list(updates.values()) + [ticket_id]

            cursor = conn.execute(
                f"UPDATE tickets SET {set_clause} WHERE id = ?",
                params
            )

            success = cursor.rowcount > 0

        # Log ticket update to audit log (after transaction commits)
        if success:
            log_database_audit(
                pool=self.pool,
                table_name="tickets",
                operation="UPDATE",
                record_id=ticket_id,
                user_context=_get_user_context(),
                old_values=old_values,
                new_values=updates,
                change_description=f"Updated ticket: {', '.join(updates.keys())}"
            )

        return success
    
    def mark_complete(
        self,
        ticket_id: str,
        completion_notes: str,
        test_steps: str,
        test_results: str,
        summary: Optional[str] = None,
        test_documentation_url: Optional[str] = None,
    ) -> bool:
        """
        Mark ticket as completed with mandatory quality documentation.

        Performs TWO checks:
        1. IDEMPOTENCY: Prevents re-completion of already-finished tickets
           (returns False if already completed)
        2. QUALITY GATE: Validates completion evidence fields
           (raises ValueError if validation fails)

        NOTE: The application layer (do_af.py:mark_ticket_complete) also
        performs idempotency checks before calling this method. This creates
        defense-in-depth: idempotency is checked at both layers.

        Args:
            ticket_id: Ticket ID to complete.
            completion_notes: Required description of what was done (min 20 chars).
            test_steps: Required description of testing performed (min 10 chars).
            test_results: Required test outcomes/evidence (min 10 chars).
            summary: Optional short summary.
            test_documentation_url: Optional link to test artifacts.

        Returns:
            True if completed, False if not found or already completed.

        Raises:
            ValueError: If completion evidence fields are missing or too short.
        """
        # Get ticket (for update) and idempotency check
        existing = self.get_ticket(ticket_id)
        if not existing:
            return False

        # IDEMPOTENCY CHECK
        # Prevents re-completion of already-finished tickets.
        # NOTE: This check is ALSO performed in the application layer
        # (do_af.py:mark_ticket_complete) before calling this method, but
        # we keep it here for defense-in-depth. Calling this method directly
        # (not through mark_ticket_complete) will still get idempotency protection.
        if existing.get('status') == 'Completed' or existing.get('completed'):
            return False

        # QUALITY GATE VALIDATION
        # These validations are the core quality gate mechanism.
        # They ensure NO ticket can be marked complete without evidence.
        if not completion_notes or len(completion_notes.strip()) < 20:
            raise ValueError(
                "completion_notes required: must describe what was done (min 20 chars)"
            )

        if not test_steps or len(test_steps.strip()) < 10:
            raise ValueError(
                "test_steps required: must describe how testing was performed (min 10 chars)"
            )

        if not test_results or len(test_results.strip()) < 10:
            raise ValueError(
                "test_results required: must provide test outcomes/evidence (min 10 chars)"
            )

        implementation_details = _extract_completion_section(completion_notes, "Implementation")
        if not implementation_details:
            raise ValueError(
                "completion_notes required: include Implementation section describing code changes"
            )

        completion_files = _extract_completion_files(completion_notes)
        if not completion_files:
            raise ValueError(
                "completion_notes required: include Files section with modified paths"
            )

        for entry in completion_files:
            normalized = _normalize_completion_file_entry(entry)
            lowered = normalized.lower()
            if lowered in {"tbd", "todo", "n/a", "na", "none"}:
                raise ValueError(
                    "completion_notes required: Files section must list real paths"
                )
            if not _looks_like_path(normalized):
                raise ValueError(
                    "completion_notes required: Files section must list valid file paths"
                )

        # Build updates with validated fields
        updates = {
            'status': 'Completed',
            'completion_notes': completion_notes.strip(),
            'test_steps': test_steps.strip(),
            'test_results': test_results.strip(),
            'test_documentation_url': test_documentation_url,
            'documented': 1,  # NOW JUSTIFIED by completion_notes
            'functioning': 1,  # NOW JUSTIFIED by test_results
            'tested': 1,  # NOW JUSTIFIED by test_steps
            'completed': 1,
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

        try:
            with self.pool.transaction(immediate=True) as conn:
                # Acquire lock directly without separate SELECT to eliminate TOCTOU race
                # The WHERE clause ensures we only lock if ticket is available or lease expired
                # This is atomic - no window for another transaction to interfere
                cursor = conn.execute(
                    """
                    UPDATE tickets
                    SET locked_by = ?, locked_at = ?, lease_expires = ?, status = 'In Progress'
                    WHERE id = ? AND (
                        locked_by IS NULL
                        OR lease_expires < ?
                    )
                    """,
                    (
                        locked_by,
                        serialize_timestamp(now),
                        serialize_timestamp(lease_expires),
                        ticket_id,
                        serialize_timestamp(now)
                    )
                )

                # If no rows updated, ticket doesn't exist or is already locked
                if cursor.rowcount == 0:
                    return None

                return TicketLock(
                    ticket_id=ticket_id,
                    locked_by=locked_by,
                    locked_at=now,
                    lease_expires=lease_expires,
                )
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                return None
            raise
    
    def release_lock(self, ticket_id: str, locked_by: str) -> bool:
        """
        Release lock on a ticket.

        Args:
            ticket_id: Ticket ID to unlock.
            locked_by: Must match current lock holder.

        Returns:
            True if released, False if not locked or wrong holder.
        """
        with self.pool.transaction(immediate=True) as conn:
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

        with self.pool.transaction(immediate=True) as conn:
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

        with self.pool.transaction(immediate=True) as conn:
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
            Dict with counts and breakdowns (excluding soft-deleted tickets).
        """
        with self.pool.connection() as conn:
            # Total counts (excluding soft-deleted)
            cursor = conn.execute("SELECT COUNT(*) as total FROM tickets WHERE deleted = 0")
            total = cursor.fetchone()['total']

            # By status (excluding soft-deleted)
            cursor = conn.execute(
                "SELECT status, COUNT(*) as count FROM tickets WHERE deleted = 0 GROUP BY status"
            )
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}

            # By priority (excluding soft-deleted)
            cursor = conn.execute(
                "SELECT priority, COUNT(*) as count FROM tickets WHERE deleted = 0 GROUP BY priority"
            )
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}

            # Locked count (excluding soft-deleted)
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM tickets WHERE deleted = 0 AND locked_by IS NOT NULL"
            )
            locked = cursor.fetchone()['count']

            # Soft-deleted count
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM tickets WHERE deleted = 1"
            )
            deleted = cursor.fetchone()['count']

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
                'deleted': deleted,
            }
    
    def delete_ticket(self, ticket_id: str, soft_delete: bool = True) -> bool:
        """
        Delete ticket with optional soft-delete for data recovery.

        Soft-delete (default) marks ticket as deleted without removing data,
        allowing recovery if needed. Hard-delete permanently removes the record.

        Args:
            ticket_id: Ticket ID to delete.
            soft_delete: If True (default), soft-delete; if False, hard-delete.

        Returns:
            True if deleted, False if not found.
        """
        operation = None
        is_soft = soft_delete

        with self.pool.transaction() as conn:
            if soft_delete:
                now = serialize_timestamp(datetime.now(timezone.utc))
                cursor = conn.execute(
                    "UPDATE tickets SET deleted = 1, deleted_at = ? WHERE id = ? AND deleted = 0",
                    (now, ticket_id,)
                )
                operation = "UPDATE"  # UPDATE for soft delete
            else:
                cursor = conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                operation = "DELETE"

            success = cursor.rowcount > 0

        # Log ticket deletion to audit log (after transaction commits)
        if success and operation:
            delete_type = "SOFT_DELETE" if is_soft else "HARD_DELETE"
            log_database_audit(
                pool=self.pool,
                table_name="tickets",
                operation=operation,
                record_id=ticket_id,
                user_context=_get_user_context(),
                change_description=f"Deleted ticket ({delete_type})"
            )

        return success

    def recover_ticket(self, ticket_id: str) -> bool:
        """
        Recover a soft-deleted ticket.

        Args:
            ticket_id: Ticket ID to recover.

        Returns:
            True if recovered, False if not found or not soft-deleted.
        """
        with self.pool.transaction() as conn:
            cursor = conn.execute(
                "UPDATE tickets SET deleted = 0, deleted_at = NULL WHERE id = ? AND deleted = 1",
                (ticket_id,)
            )
            return cursor.rowcount > 0

    def get_deleted_tickets(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all soft-deleted tickets.

        Args:
            limit: Optional limit on returned tickets.

        Returns:
            List of soft-deleted ticket dicts.
        """
        query = "SELECT * FROM tickets WHERE deleted = 1 ORDER BY deleted_at DESC"
        params = []

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self.pool.connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

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
            'completion_notes': row['completion_notes'],
            'test_steps': row['test_steps'],
            'test_results': row['test_results'],
            'test_documentation_url': row['test_documentation_url'],
            'completion_verified_by': row['completion_verified_by'],
            'completion_verified_at': deserialize_timestamp(row['completion_verified_at']),
            'github_issue_url': _maybe_get(row, 'github_issue_url'),
            'github_issue_number': _maybe_get(row, 'github_issue_number'),
            'github_sync_state': _maybe_get(row, 'github_sync_state'),
            'github_sync_message': _maybe_get(row, 'github_sync_message'),
            'format_version': row['format_version'],
            'documented': bool(row['documented']),
            'functioning': bool(row['functioning']),
            'tested': bool(row['tested']),
            'completed': bool(row['completed']),
            'deleted': bool(row['deleted']),
            'deleted_at': deserialize_timestamp(row['deleted_at']),
        }


def _maybe_get(row: sqlite3.Row, key: str):
    return row[key] if key in row.keys() else None


# Global repository instance
_global_repo: Optional[TicketRepository] = None


def get_ticket_repository(pool: Optional[DatabasePool] = None, config: Optional[ActifixConfig] = None) -> TicketRepository:
    """
    Get or create global ticket repository.

    Args:
        pool: Optional database pool override.
        config: Optional configuration override.

    Returns:
        Ticket repository instance.
    """
    global _global_repo

    if _global_repo is None or (pool and _global_repo.pool != pool) or (config and _global_repo.config != config):
        _global_repo = TicketRepository(pool=pool, config=config)

    return _global_repo


def reset_ticket_repository() -> None:
    """Reset global repository (for testing)."""
    global _global_repo
    _global_repo = None
