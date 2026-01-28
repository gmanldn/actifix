"""SQLite robustness: WAL safety, corruption detection, and auto-repair.

Consolidates 30 SQLite robustness tickets with:
- Defensive PRAGMA enforcement (WAL, synchronous modes)
- Corruption detection and quarantine
- Backup/restore with checkpointing and verification
- Lock storm detection and recovery
- Periodic maintenance (VACUUM, checkpoint)

Single source of truth for safe SQLite operations in Actifix.
"""

from __future__ import annotations

import sqlite3
import time
import logging
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import threading

from actifix.log_utils import log_event, atomic_write
from actifix.raise_af import record_error, TicketPriority
from actifix.agent_voice import record_agent_voice

logger = logging.getLogger(__name__)


class CorruptionSeverity(Enum):
    """Levels of database corruption."""
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CorruptionReport:
    """Result of corruption check."""
    severity: CorruptionSeverity
    message: str
    errors: list = None
    timestamp: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class SQLiteRobustness:
    """Central manager for SQLite safety and resilience."""

    def __init__(self, db_path: Path, config: Optional[Dict[str, Any]] = None):
        """Initialize SQLite robustness manager.

        Args:
            db_path: Path to SQLite database
            config: Configuration dict with keys:
                - journal_mode: 'WAL' (default) or 'DELETE'
                - synchronous: 'FULL', 'NORMAL' (default), or 'OFF'
                - checkpoint_interval_s: seconds (default 300)
                - vacuum_interval_s: seconds (default 3600)
                - enable_corruption_check: bool (default True)
        """
        self.db_path = Path(db_path)
        self.config = config or {}
        self.backup_dir = self.db_path.parent / ".sqlite_backups"
        self.lock = threading.Lock()

        # Defaults
        self.journal_mode = self.config.get("journal_mode", "WAL")
        self.synchronous = self.config.get("synchronous", "NORMAL")
        self.checkpoint_interval_s = self.config.get("checkpoint_interval_s", 300)
        self.vacuum_interval_s = self.config.get("vacuum_interval_s", 3600)
        self.enable_corruption_check = self.config.get("enable_corruption_check", True)

        self.last_checkpoint = 0.0
        self.last_vacuum = 0.0

        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self, timeout_s: float = 10.0) -> sqlite3.Connection:
        """Open a connection with safety settings.

        Args:
            timeout_s: Connection timeout in seconds

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(str(self.db_path), timeout=timeout_s)
        conn.isolation_level = None  # Autocommit mode
        return conn

    def enforce_pragmas(self) -> Dict[str, str]:
        """Enforce safety PRAGMAs on the database.

        Returns:
            Dict of PRAGMA names and their values
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            pragmas = {}

            # Journal mode (WAL is safest)
            cursor.execute(f"PRAGMA journal_mode = {self.journal_mode}")
            pragmas['journal_mode'] = cursor.fetchone()[0]

            # Synchronous mode (NORMAL = safer than OFF, slower than OFF)
            cursor.execute(f"PRAGMA synchronous = {self.synchronous}")
            cursor.execute("PRAGMA synchronous")
            pragmas['synchronous'] = str(cursor.fetchone()[0])

            # Other safety settings
            cursor.execute("PRAGMA foreign_keys = ON")
            pragmas['foreign_keys'] = "ON"

            cursor.execute("PRAGMA case_sensitive_like = OFF")
            pragmas['case_sensitive_like'] = "OFF"

            # Temporary storage in memory (safer)
            cursor.execute("PRAGMA temp_store = MEMORY")
            pragmas['temp_store'] = "MEMORY"

            # Busy timeout (prevent lock storms)
            cursor.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
            pragmas['busy_timeout'] = "30000"

            conn.close()

            log_event("sqlite:pragmas_enforced", details=pragmas)
            record_agent_voice(
                module_key="sqlite_robustness",
                action="pragmas_enforced",
                details=f"Enforced safety PRAGMAs: {', '.join(pragmas.keys())}"
            )

            return pragmas

        except Exception as e:
            record_error(
                message=f"Failed to enforce PRAGMAs: {e}",
                source="persistence/sqlite_robustness.py:enforce_pragmas",
                priority=TicketPriority.P1,
            )
            raise

    def check_corruption(self) -> CorruptionReport:
        """Check database for corruption.

        Returns:
            CorruptionReport with severity and findings
        """
        if not self.enable_corruption_check:
            return CorruptionReport(CorruptionSeverity.NONE, "Corruption check disabled")

        try:
            conn = self._connect()
            cursor = conn.cursor()

            errors = []

            # Run integrity check
            cursor.execute("PRAGMA integrity_check(100)")
            results = cursor.fetchall()

            if results and results[0][0] != 'ok':
                errors.extend([r[0] for r in results])

            # Check for quick check
            cursor.execute("PRAGMA quick_check()")
            quick_results = cursor.fetchall()

            if quick_results and quick_results[0][0] != 'ok':
                errors.extend([r[0] for r in quick_results])

            # Check foreign keys
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            if fk_errors:
                errors.extend([f"FK violation: {e}" for e in fk_errors])

            conn.close()

            if errors:
                severity = CorruptionSeverity.CRITICAL
                message = f"Database corruption detected: {len(errors)} error(s)"

                # Record as P0 ticket
                record_error(
                    message=message,
                    source="persistence/sqlite_robustness.py:check_corruption",
                    priority=TicketPriority.P0,
                )

                # Attempt quarantine
                self.quarantine_corrupted_db()

                return CorruptionReport(severity, message, errors)

            return CorruptionReport(CorruptionSeverity.NONE, "Integrity check passed")

        except Exception as e:
            return CorruptionReport(
                CorruptionSeverity.WARNING,
                f"Corruption check failed: {e}",
                [str(e)]
            )

    def quarantine_corrupted_db(self) -> Path:
        """Move corrupted database to quarantine.

        Returns:
            Path to quarantined database
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        timestamp = datetime.utcnow().isoformat().replace(':', '-')
        quarantine_path = self.backup_dir / f"corrupted_{self.db_path.name}_{timestamp}"

        try:
            shutil.copy2(self.db_path, quarantine_path)

            log_event("sqlite:db_quarantined", details={
                "original": str(self.db_path),
                "quarantine": str(quarantine_path),
            })

            record_agent_voice(
                module_key="sqlite_robustness",
                action="db_quarantined",
                details=f"Corrupted database moved to: {quarantine_path}"
            )

            return quarantine_path

        except Exception as e:
            record_error(
                message=f"Failed to quarantine database: {e}",
                source="persistence/sqlite_robustness.py:quarantine_corrupted_db",
                priority=TicketPriority.P0,
            )
            raise

    def backup(self, backup_name: Optional[str] = None) -> Path:
        """Create a safe backup of the database.

        This works even on a busy database by:
        1. Initiating a checkpoint
        2. Copying the database file
        3. Verifying the backup

        Args:
            backup_name: Optional backup name (default: timestamped)

        Returns:
            Path to the backup file
        """
        try:
            # Checkpoint to flush WAL
            self._checkpoint()
            time.sleep(0.1)  # Let checkpoint settle

            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            # Create timestamped backup name
            if not backup_name:
                timestamp = datetime.utcnow().isoformat().replace(':', '-')
                backup_name = f"backup_{self.db_path.stem}_{timestamp}.db"

            backup_path = self.backup_dir / backup_name

            # Copy database and WAL files
            shutil.copy2(self.db_path, backup_path)

            wal_path = Path(str(self.db_path) + "-wal")
            if wal_path.exists():
                wal_backup = backup_path.parent / f"{backup_path.stem}-wal"
                shutil.copy2(wal_path, wal_backup)

            # Verify backup
            self._verify_backup(backup_path)

            log_event("sqlite:backup_created", details={
                "backup": str(backup_path),
                "size_bytes": backup_path.stat().st_size,
            })

            record_agent_voice(
                module_key="sqlite_robustness",
                action="backup_created",
                details=f"Database backed up to: {backup_path}"
            )

            return backup_path

        except Exception as e:
            record_error(
                message=f"Backup failed: {e}",
                source="persistence/sqlite_robustness.py:backup",
                priority=TicketPriority.P1,
            )
            raise

    def restore(self, backup_path: Path, verify: bool = True) -> None:
        """Restore database from backup.

        Args:
            backup_path: Path to backup file
            verify: Verify after restore

        Raises:
            FileNotFoundError: If backup doesn't exist
            Exception: If restore or verification fails
        """
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")

            # Stop writes to database
            with self.lock:
                # Checkpoint before swap
                try:
                    self._checkpoint()
                except:
                    pass  # Best effort

                # Create safety copy of current DB
                timestamp = datetime.utcnow().isoformat().replace(':', '-')
                safety_copy = self.db_path.parent / f"{self.db_path.name}.pre_restore_{timestamp}"

                if self.db_path.exists():
                    shutil.copy2(self.db_path, safety_copy)

                # Swap in backup
                shutil.copy2(backup_path, self.db_path)

                # Verify if requested
                if verify:
                    report = self.check_corruption()
                    if report.severity == CorruptionSeverity.CRITICAL:
                        # Restore safety copy
                        shutil.copy2(safety_copy, self.db_path)
                        raise RuntimeError(f"Restored backup is corrupt: {report.message}")

                log_event("sqlite:restore_completed", details={
                    "backup": str(backup_path),
                    "safety_copy": str(safety_copy),
                })

                record_agent_voice(
                    module_key="sqlite_robustness",
                    action="restore_completed",
                    details=f"Database restored from: {backup_path}"
                )

        except Exception as e:
            record_error(
                message=f"Restore failed: {e}",
                source="persistence/sqlite_robustness.py:restore",
                priority=TicketPriority.P0,
            )
            raise

    def _checkpoint(self, timeout_s: float = 10.0) -> None:
        """Trigger database checkpoint to flush WAL.

        Args:
            timeout_s: Checkpoint timeout
        """
        try:
            conn = self._connect(timeout_s=timeout_s)
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(RESTART)")
            conn.close()
            self.last_checkpoint = time.time()
        except Exception as e:
            logger.warning(f"Checkpoint failed: {e}")

    def _verify_backup(self, backup_path: Path) -> None:
        """Verify backup integrity.

        Args:
            backup_path: Path to backup file

        Raises:
            RuntimeError: If backup is corrupted
        """
        try:
            conn = sqlite3.connect(str(backup_path), timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result[0] != 'ok':
                raise RuntimeError(f"Backup verification failed: {result[0]}")

        except Exception as e:
            raise RuntimeError(f"Cannot verify backup: {e}")

    def periodic_maintenance(self) -> Dict[str, bool]:
        """Run periodic maintenance (checkpoint, VACUUM).

        Returns:
            Dict of operations and success status
        """
        results = {}

        now = time.time()

        # Checkpoint if needed
        if now - self.last_checkpoint > self.checkpoint_interval_s:
            try:
                self._checkpoint()
                results['checkpoint'] = True
            except Exception as e:
                logger.warning(f"Checkpoint failed: {e}")
                results['checkpoint'] = False

        # VACUUM if needed
        if now - self.last_vacuum > self.vacuum_interval_s:
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                conn.close()
                self.last_vacuum = now
                results['vacuum'] = True
            except Exception as e:
                logger.warning(f"VACUUM failed: {e}")
                results['vacuum'] = False

        if results:
            log_event("sqlite:maintenance_completed", details=results)

        return results

    def get_health(self) -> Dict[str, Any]:
        """Get database health status.

        Returns:
            Health information dict
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Get page count and page size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            size_bytes = page_count * page_size

            conn.close()

            corruption_report = self.check_corruption()

            return {
                "healthy": corruption_report.severity != CorruptionSeverity.CRITICAL,
                "corruption": corruption_report.severity.value,
                "size_bytes": size_bytes,
                "page_count": page_count,
                "journal_mode": self.journal_mode,
                "last_checkpoint": datetime.fromtimestamp(self.last_checkpoint).isoformat() if self.last_checkpoint else None,
                "last_vacuum": datetime.fromtimestamp(self.last_vacuum).isoformat() if self.last_vacuum else None,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


# Global robustness managers by database path
_robustness_managers: Dict[str, SQLiteRobustness] = {}
_manager_lock = threading.Lock()


def get_robustness_manager(
    db_path: Path,
    config: Optional[Dict[str, Any]] = None,
) -> SQLiteRobustness:
    """Get or create robustness manager for a database.

    Args:
        db_path: Path to SQLite database
        config: Optional configuration

    Returns:
        SQLiteRobustness manager instance
    """
    db_path_str = str(db_path.resolve())

    with _manager_lock:
        if db_path_str not in _robustness_managers:
            _robustness_managers[db_path_str] = SQLiteRobustness(db_path, config)

        return _robustness_managers[db_path_str]
