#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crash Detection and Recovery System.

Detects and recovers from system crashes:
- Monitors application state
- Detects abnormal termination
- Recovers from corrupted state
- Preserves data integrity
- Provides recovery audit trail

Version: 1.0.0
"""

import json
import os
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List


class CrashRecoveryState(Enum):
    """States in crash recovery process."""
    HEALTHY = "healthy"              # Normal operation
    RECOVERING = "recovering"         # In recovery process
    RECOVERED = "recovered"           # Successfully recovered
    CORRUPTED = "corrupted"           # Unrecoverable corruption detected
    DISABLED = "disabled"             # Recovery disabled


@dataclass
class CrashSnapshot:
    """Snapshot of application state before potential crash."""

    timestamp: datetime
    application_state: Dict[str, str]  # Key application state
    memory_usage_mb: int
    database_size_bytes: int
    open_transactions: int
    pending_writes: int
    last_checkpoint_timestamp: Optional[datetime] = None


@dataclass
class CrashRecord:
    """Record of a detected crash."""

    crash_id: str
    detected_at: datetime
    recovery_state: CrashRecoveryState
    root_cause: Optional[str] = None
    recovery_actions: List[str] = None
    data_loss_detected: bool = False
    severity: str = "unknown"

    def __post_init__(self):
        if self.recovery_actions is None:
            self.recovery_actions = []


class CrashDetectionError(Exception):
    """Raised when crash detection fails."""
    pass


class CrashRecoveryManager:
    """Manages crash detection and recovery."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize crash recovery manager.

        Args:
            db_path: Path to SQLite database for recovery state
        """
        self.db_path = db_path or self._get_default_db_path()
        self.lock = threading.RLock()
        self.state_file = self._get_state_file()
        self._init_database()
        self._init_state()

    def _get_default_db_path(self) -> str:
        """Get default database path."""
        from .state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'recovery.db')

    def _get_state_file(self) -> str:
        """Get application state file path."""
        from .state_paths import get_actifix_paths
        paths = get_actifix_paths()
        return str(Path(paths.state_dir) / 'app_state.json')

    def _init_database(self) -> None:
        """Initialize recovery database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # Recovery records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crash_records (
                    crash_id TEXT PRIMARY KEY,
                    detected_at TEXT NOT NULL,
                    recovery_state TEXT NOT NULL,
                    root_cause TEXT,
                    recovery_actions TEXT,
                    data_loss_detected BOOLEAN DEFAULT 0,
                    severity TEXT DEFAULT 'unknown'
                )
            ''')

            # Crash snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crash_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    application_state TEXT NOT NULL,
                    memory_usage_mb INTEGER,
                    database_size_bytes INTEGER,
                    open_transactions INTEGER,
                    pending_writes INTEGER,
                    last_checkpoint_timestamp TEXT
                )
            ''')

            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_crash_detected ON crash_records(detected_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON crash_snapshots(timestamp)')

            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass

    def _init_state(self) -> None:
        """Initialize application state tracking."""
        try:
            # Check if we're recovering from a crash
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    if state.get('status') == 'running':
                        # Previous run crashed without clean shutdown
                        self._detect_crash()
            else:
                # First run - initialize clean state
                self._save_state('running')
        except Exception:
            pass

    def _save_state(self, status: str, extra_info: Optional[Dict] = None) -> None:
        """Save application state to file."""
        try:
            state = {
                'status': status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            if extra_info:
                state.update(extra_info)

            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            with open(self.state_file, 'w') as f:
                json.dump(state, f)

            os.chmod(self.state_file, 0o600)
        except Exception:
            pass

    def _detect_crash(self) -> None:
        """Detect and record a system crash."""
        with self.lock:
            import secrets
            crash_id = secrets.token_hex(8)

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                now = datetime.now(timezone.utc)

                cursor.execute('''
                    INSERT INTO crash_records
                    (crash_id, detected_at, recovery_state, severity)
                    VALUES (?, ?, ?, ?)
                ''', (crash_id, now.isoformat(), CrashRecoveryState.RECOVERING.value, 'critical'))

                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass

    def create_snapshot(self, app_state: Dict[str, str]) -> CrashSnapshot:
        """Create a state snapshot before potential crash.

        Args:
            app_state: Application state dictionary

        Returns:
            Created snapshot
        """
        with self.lock:
            import os
            snapshot = CrashSnapshot(
                timestamp=datetime.now(timezone.utc),
                application_state=app_state,
                memory_usage_mb=self._get_memory_usage(),
                database_size_bytes=self._get_database_size(),
                open_transactions=0,
                pending_writes=0,
            )

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO crash_snapshots
                    (timestamp, application_state, memory_usage_mb, database_size_bytes,
                     open_transactions, pending_writes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.timestamp.isoformat(),
                    json.dumps(snapshot.application_state),
                    snapshot.memory_usage_mb,
                    snapshot.database_size_bytes,
                    snapshot.open_transactions,
                    snapshot.pending_writes,
                ))

                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass

            return snapshot

    def record_crash(self, crash_id: str, root_cause: str, recovery_actions: List[str]) -> None:
        """Record crash details and recovery actions.

        Args:
            crash_id: Unique crash identifier
            root_cause: Root cause of the crash
            recovery_actions: List of recovery actions taken
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE crash_records
                    SET root_cause = ?, recovery_actions = ?, recovery_state = ?
                    WHERE crash_id = ?
                ''', (
                    root_cause,
                    json.dumps(recovery_actions),
                    CrashRecoveryState.RECOVERED.value,
                    crash_id,
                ))

                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass

    def get_last_crash(self) -> Optional[CrashRecord]:
        """Get information about the last crash.

        Returns:
            Last crash record if available, None otherwise
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT crash_id, detected_at, recovery_state, root_cause,
                           recovery_actions, data_loss_detected, severity
                    FROM crash_records
                    ORDER BY detected_at DESC
                    LIMIT 1
                ''')

                result = cursor.fetchone()
                conn.close()

                if result:
                    crash_id, detected_at, recovery_state, root_cause, recovery_actions, data_loss, severity = result
                    return CrashRecord(
                        crash_id=crash_id,
                        detected_at=datetime.fromisoformat(detected_at),
                        recovery_state=CrashRecoveryState(recovery_state),
                        root_cause=root_cause,
                        recovery_actions=json.loads(recovery_actions) if recovery_actions else [],
                        data_loss_detected=bool(data_loss),
                        severity=severity,
                    )
            except sqlite3.Error:
                pass

            return None

    def get_recent_snapshots(self, limit: int = 5) -> List[CrashSnapshot]:
        """Get recent state snapshots.

        Args:
            limit: Maximum number of snapshots to retrieve

        Returns:
            List of recent snapshots
        """
        with self.lock:
            snapshots = []

            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, application_state, memory_usage_mb,
                           database_size_bytes, open_transactions, pending_writes
                    FROM crash_snapshots
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                for row in cursor.fetchall():
                    timestamp, app_state_json, memory_mb, db_size, transactions, writes = row
                    snapshots.append(CrashSnapshot(
                        timestamp=datetime.fromisoformat(timestamp),
                        application_state=json.loads(app_state_json),
                        memory_usage_mb=memory_mb,
                        database_size_bytes=db_size,
                        open_transactions=transactions,
                        pending_writes=writes,
                    ))

                conn.close()
            except sqlite3.Error:
                pass

            return snapshots

    def mark_healthy(self) -> None:
        """Mark application as healthy after startup."""
        self._save_state('healthy')

    def mark_shutting_down(self) -> None:
        """Mark application as shutting down cleanly."""
        self._save_state('shutting_down')

    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return int(process.memory_info().rss / 1024 / 1024)
        except Exception:
            return 0

    def _get_database_size(self) -> int:
        """Get database file size in bytes."""
        try:
            db_path = Path(self.db_path)
            if db_path.exists():
                return db_path.stat().st_size
        except Exception:
            pass

        return 0


# Global recovery manager instance
_recovery_manager: Optional[CrashRecoveryManager] = None


def get_recovery_manager() -> CrashRecoveryManager:
    """Get or create global recovery manager."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = CrashRecoveryManager()
    return _recovery_manager


def reset_recovery_manager() -> None:
    """Reset global recovery manager (for testing)."""
    global _recovery_manager
    _recovery_manager = None
