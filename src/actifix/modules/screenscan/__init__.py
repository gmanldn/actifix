"""Screenscan module: always-on screen capture with ring-buffer storage.

Critical always-on module for debugging UI state and regressions.
Captures 2 FPS, retains last 60 seconds in ring-buffer, zero overhead.
All security guardrails in place - no screenshots in tickets or logs.
"""

from __future__ import annotations

import threading
import time
import os
import fcntl
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error
from actifix.modules.base import ModuleBase
from actifix.agent_voice import record_agent_voice

if TYPE_CHECKING:
    from flask import Blueprint

class CapturePermissionError(Enum):
    """Permission error types for capture backends."""
    NO_PERMISSION = "no_permission"
    NOT_SUPPORTED = "not_supported"
    DISABLED_IN_CONFIG = "disabled_in_config"


@dataclass
class FrameMetadata:
    """Frame metadata without bytes (for stats/logging)."""
    format: str
    width: int
    height: int
    bytes: int
    captured_at: str = ""


class ScreenCaptureProvider:
    """Base interface for screen capture providers (SC-005)."""

    def capture(self) -> Optional[Tuple[bytes, FrameMetadata]]:
        """Capture a screenshot. Returns (data, metadata) or None."""
        raise NotImplementedError()

    def get_health(self) -> Dict[str, Any]:
        """Get health status of provider."""
        raise NotImplementedError()


class FakeScreenCaptureProvider(ScreenCaptureProvider):
    """Deterministic test provider (SC-016 test support)."""

    def __init__(self, frame_size_bytes: int = 65536):
        self.frame_size = frame_size_bytes
        self.call_count = 0

    def capture(self) -> Optional[Tuple[bytes, FrameMetadata]]:
        """Return deterministic fake PNG data."""
        # Fake PNG header + data
        data = b'\x89PNG\r\n\x1a\n' + (b'\x00' * (self.frame_size - 8))
        meta = FrameMetadata(
            format='png',
            width=1920,
            height=1080,
            bytes=len(data),
        )
        self.call_count += 1
        return data, meta

    def get_health(self) -> Dict[str, Any]:
        return {
            'status': 'ok',
            'type': 'fake',
            'call_count': self.call_count,
        }


MODULE_DEFAULTS = {
    "fps": 2,  # Frames per second (SC-008)
    "retention_seconds": 60,  # Retain last 60 seconds only
    "enabled": True,
    "capture_backend": "auto",  # auto, macos, windows, linux, none
    "max_frame_bytes": 512 * 1024,  # Max 512KB per frame
    "enable_in_prod": False,  # SC-013: Require explicit enable in production
    "use_fake_provider": False,  # For testing (SC-016)
    # Privacy controls
    "privacy_opt_in_required": True,  # Require explicit opt-in for screen capture
    "privacy_consent_env_var": "ACTIFIX_SCREENSCAN_CONSENT",  # Environment variable for consent
    "privacy_allow_ui_access": True,  # Allow UI to show frame metadata
    "restart_policy_enabled": True,  # Auto-restart worker on crash
    "max_restart_attempts": 5,  # Max restarts within restart_window_seconds
    "restart_window_seconds": 300,  # 5 minute window for counting restarts
    "initial_backoff_seconds": 1,  # Initial backoff delay
    "max_backoff_seconds": 60,  # Max backoff delay
    "backoff_multiplier": 2,  # Exponential backoff multiplier
    # API payload limits
    "api_max_frames_per_request": 120,  # Max frames returned in single request
    "api_max_total_bytes": 100 * 1024 * 1024,  # 100MB max total response
    "api_request_timeout_seconds": 30,  # Max request processing time
    "api_rate_limit_per_minute": 60,  # Max requests per minute per IP
    # Storage quota enforcement
    "storage_quota_bytes": 50 * 1024 * 1024,  # 50MB max storage for screenscan data
    "storage_quota_warning_threshold": 0.8,  # Warn at 80% of quota
    "cleanup_check_interval_seconds": 300,  # Check storage every 5 minutes
    "vacuum_on_cleanup": True,  # Run VACUUM to reclaim space
    # Alerting thresholds
    "lag_alert_threshold_seconds": 5.0,  # Alert if capture lags behind by this much
    "failure_alert_threshold": 10,  # Alert after N consecutive capture failures
    "restart_alert_enabled": True,  # Alert on worker restarts
}

ACCESS_RULE = "local-only"

MODULE_METADATA = {
    "name": "modules.screenscan",
    "version": "1.0.0",
    "description": "Always-on screen capture with ring-buffer storage for debugging.",
    "capabilities": {
        "health": True,
        "api": True,
    },
    "permissions": ["logging", "fs_read"],
}

MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
    "infra.persistence.database",
]

# Global state for screenscan worker
_worker_thread: Optional[threading.Thread] = None
_worker_running = False
_worker_lock = threading.Lock()
_restart_attempts: list[float] = []  # Timestamps of restart attempts
_current_backoff = 1  # Current backoff delay in seconds

# API rate limiting state (IP -> list of request timestamps)
_api_request_log: Dict[str, list[float]] = {}
_api_rate_lock = threading.Lock()

# Capture health tracking
_consecutive_failures = 0
_last_lag_alert = 0.0  # Timestamp of last lag alert


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for screenscan."""
    return ModuleBase(
        module_key="screenscan",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _should_restart_worker(helper: ModuleBase) -> bool:
    """Check if worker should be restarted based on restart policy."""
    global _restart_attempts, _current_backoff

    config = helper.get_config()
    if not config.get("restart_policy_enabled", True):
        return False

    max_attempts = config.get("max_restart_attempts", 5)
    window_seconds = config.get("restart_window_seconds", 300)

    # Clean up old restart attempts outside the window
    now = time.time()
    _restart_attempts = [t for t in _restart_attempts if now - t < window_seconds]

    # Check if we've exceeded max restarts in the window
    if len(_restart_attempts) >= max_attempts:
        helper.record_module_error(
            message=f"Screenscan worker exceeded {max_attempts} restarts in {window_seconds}s window. Restart policy disabled.",
            source="modules/screenscan/__init__.py:_should_restart_worker",
            error_type="RestartLimitExceeded",
            priority=TicketPriority.P1,
        )
        record_agent_voice(
            module_key="screenscan",
            action="restart_limit_exceeded",
            level="ERROR",
            details=f"Worker restart limit exceeded: {len(_restart_attempts)} attempts in {window_seconds}s",
        )
        return False

    return True


def _calculate_backoff(helper: ModuleBase) -> float:
    """Calculate exponential backoff delay for worker restart."""
    global _current_backoff

    config = helper.get_config()
    initial_backoff = config.get("initial_backoff_seconds", 1)
    max_backoff = config.get("max_backoff_seconds", 60)
    multiplier = config.get("backoff_multiplier", 2)

    # First restart uses initial backoff
    if not _restart_attempts:
        _current_backoff = initial_backoff
    else:
        # Exponential backoff with multiplier
        _current_backoff = min(_current_backoff * multiplier, max_backoff)

    return _current_backoff


def _check_api_rate_limit(client_ip: str, helper: ModuleBase) -> bool:
    """Check if client has exceeded API rate limit.

    Returns True if request is allowed, False if rate limit exceeded.
    """
    global _api_request_log

    config = helper.get_config()
    rate_limit = config.get("api_rate_limit_per_minute", 60)

    now = time.time()
    window = 60.0  # 1 minute window

    with _api_rate_lock:
        # Clean up old requests outside the window
        if client_ip in _api_request_log:
            _api_request_log[client_ip] = [
                t for t in _api_request_log[client_ip] if now - t < window
            ]
        else:
            _api_request_log[client_ip] = []

        # Check if limit exceeded
        if len(_api_request_log[client_ip]) >= rate_limit:
            record_agent_voice(
                module_key="screenscan",
                action="api_rate_limit_exceeded",
                level="WARNING",
                details=f"Rate limit exceeded for {client_ip}: {len(_api_request_log[client_ip])} requests in last minute",
            )
            return False

        # Record this request
        _api_request_log[client_ip].append(now)
        return True


def _get_storage_usage(db) -> Dict[str, Any]:
    """Get current storage usage for screenscan tables."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get page count and page size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]

        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]

        total_db_bytes = page_count * page_size

        # Get screenscan-specific table sizes
        cursor.execute("SELECT SUM(bytes) FROM screenscan_frames")
        row = cursor.fetchone()
        frames_bytes = row[0] if row and row[0] else 0

        cursor.execute("SELECT COUNT(*) FROM screenscan_frames")
        frame_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total_db_bytes": total_db_bytes,
            "frames_bytes": frames_bytes,
            "frame_count": frame_count,
            "estimated_overhead": total_db_bytes - frames_bytes,
        }
    except Exception as e:
        helper = _module_helper()
        helper.record_module_error(
            message=f"Failed to get storage usage: {e}",
            source="modules/screenscan/__init__.py:_get_storage_usage",
            error_type=type(e).__name__,
            priority=TicketPriority.P3,
        )
        return {
            "total_db_bytes": 0,
            "frames_bytes": 0,
            "frame_count": 0,
            "estimated_overhead": 0,
        }


def _enforce_storage_quota(db, helper: ModuleBase) -> None:
    """Enforce storage quota by cleaning up old data and running VACUUM if needed."""
    try:
        config = helper.get_config()
        quota_bytes = config.get("storage_quota_bytes", 50 * 1024 * 1024)
        warning_threshold = config.get("storage_quota_warning_threshold", 0.8)
        vacuum_enabled = config.get("vacuum_on_cleanup", True)

        usage = _get_storage_usage(db)
        current_bytes = usage["total_db_bytes"]
        utilization = current_bytes / quota_bytes if quota_bytes > 0 else 0

        # Check if we're approaching or exceeding quota
        if utilization >= 1.0:
            # Quota exceeded - force cleanup
            helper.record_module_error(
                message=f"Storage quota exceeded: {current_bytes}/{quota_bytes} bytes ({utilization:.1%})",
                source="modules/screenscan/__init__.py:_enforce_storage_quota",
                error_type="QuotaExceeded",
                priority=TicketPriority.P2,
            )

            record_agent_voice(
                module_key="screenscan",
                action="storage_quota_exceeded",
                level="ERROR",
                details=f"Storage quota exceeded: {current_bytes}/{quota_bytes} bytes, triggering cleanup",
            )

            # Delete oldest frames to free space
            conn = db.get_connection()
            cursor = conn.cursor()

            # Keep only the newest 50% of frames
            cursor.execute("SELECT COUNT(*) FROM screenscan_frames")
            total_frames = cursor.fetchone()[0]
            frames_to_delete = total_frames // 2

            if frames_to_delete > 0:
                cursor.execute("""
                    DELETE FROM screenscan_frames
                    WHERE frame_seq IN (
                        SELECT frame_seq FROM screenscan_frames
                        ORDER BY frame_seq ASC
                        LIMIT ?
                    )
                """, (frames_to_delete,))
                conn.commit()

                record_agent_voice(
                    module_key="screenscan",
                    action="quota_cleanup",
                    level="WARNING",
                    details=f"Deleted {frames_to_delete} oldest frames to reclaim storage",
                )

            conn.close()

            # Run VACUUM to reclaim space
            if vacuum_enabled:
                _vacuum_database(db, helper)

        elif utilization >= warning_threshold:
            # Approaching quota - warn
            record_agent_voice(
                module_key="screenscan",
                action="storage_quota_warning",
                level="WARNING",
                details=f"Storage approaching quota: {current_bytes}/{quota_bytes} bytes ({utilization:.1%})",
            )

    except Exception as e:
        helper.record_module_error(
            message=f"Failed to enforce storage quota: {e}",
            source="modules/screenscan/__init__.py:_enforce_storage_quota",
            error_type=type(e).__name__,
            priority=TicketPriority.P3,
        )


def _vacuum_database(db, helper: ModuleBase) -> None:
    """Run VACUUM to reclaim deleted space."""
    try:
        conn = db.get_connection()
        # VACUUM must be run outside a transaction
        conn.isolation_level = None
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.close()

        record_agent_voice(
            module_key="screenscan",
            action="vacuum_complete",
            details="Database VACUUM completed successfully",
        )
    except Exception as e:
        helper.record_module_error(
            message=f"Failed to VACUUM database: {e}",
            source="modules/screenscan/__init__.py:_vacuum_database",
            error_type=type(e).__name__,
            priority=TicketPriority.P3,
        )


def _start_capture_worker(
    project_root: Optional[Union[str, Path]] = None,
    fps: int = 2,
    retention_seconds: int = 60,
) -> None:
    """Start the background capture worker thread with restart policy."""
    global _worker_thread, _worker_running, _restart_attempts

    with _worker_lock:
        if _worker_running:
            return

        _worker_running = True
        helper = _module_helper(project_root)

        def worker_with_restart():
            """Background worker wrapper with automatic restart policy."""
            global _worker_running, _restart_attempts, _current_backoff

            while _worker_running:
                try:
                    _run_capture_loop(project_root, fps, retention_seconds, helper)
                except Exception as exc:
                    helper.record_module_error(
                        message=f"Screenscan worker crashed: {exc}",
                        source="modules/screenscan/__init__.py:worker",
                        error_type=type(exc).__name__,
                        priority=TicketPriority.P1,
                    )

                    if not _worker_running:
                        break

                    # Check restart policy
                    if not _should_restart_worker(helper):
                        with _worker_lock:
                            _worker_running = False
                        break

                    # Record restart attempt
                    _restart_attempts.append(time.time())
                    backoff = _calculate_backoff(helper)

                    record_agent_voice(
                        module_key="screenscan",
                        action="worker_restart",
                        level="WARNING",
                        details=f"Restarting screenscan worker after crash. Backoff: {backoff}s, attempt {len(_restart_attempts)}",
                    )

                    # Wait with backoff before restarting
                    time.sleep(backoff)

            with _worker_lock:
                _worker_running = False

        _worker_thread = threading.Thread(target=worker_with_restart, daemon=True, name="screenscan-worker")
        _worker_thread.start()


def _run_capture_loop(
    project_root: Optional[Union[str, Path]],
    fps: int,
    retention_seconds: int,
    helper: ModuleBase,
) -> None:
    """Run the main capture loop with lag detection and alerting."""
    global _consecutive_failures, _last_lag_alert

    from actifix.persistence import get_database
    import platform

    db = get_database(project_root)

    # Ensure schema exists
    _ensure_screenscan_schema(db)

    interval = 1.0 / fps
    platform_name = platform.system()
    backend = _detect_capture_backend(platform_name, project_root, helper)

    config = helper.get_config()
    cleanup_interval = config.get("cleanup_check_interval_seconds", 300)
    lag_threshold = config.get("lag_alert_threshold_seconds", 5.0)
    failure_threshold = config.get("failure_alert_threshold", 10)

    record_agent_voice(
        module_key="screenscan",
        action="worker_start",
        details=f"Starting screenscan worker (fps={fps}, retention={retention_seconds}s, backend={backend})",
    )

    last_capture = time.time()
    last_cleanup_check = time.time()
    expected_capture_time = time.time()
    frame_count = 0

    while _worker_running:
        now = time.time()

        # Capture frames
        if now - last_capture >= interval:
            # Check for lag (actual time vs expected time)
            lag = now - expected_capture_time
            if lag > lag_threshold:
                # Alert on excessive lag (but rate-limit to once per minute)
                if now - _last_lag_alert > 60.0:
                    helper.record_module_error(
                        message=f"Screenscan capture lag detected: {lag:.2f}s behind schedule",
                        source="modules/screenscan/__init__.py:worker",
                        error_type="CaptureLag",
                        priority=TicketPriority.P3,
                    )

                    record_agent_voice(
                        module_key="screenscan",
                        action="capture_lag_detected",
                        level="WARNING",
                        details=f"Capture lagging {lag:.2f}s behind schedule (threshold: {lag_threshold}s)",
                    )
                    _last_lag_alert = now

            try:
                frame_data = _capture_frame(backend, project_root, helper)
                if frame_data:
                    _store_frame(db, frame_data, retention_seconds, fps)
                    frame_count += 1
                    _consecutive_failures = 0  # Reset failure counter on success
                else:
                    _consecutive_failures += 1
            except Exception as e:
                _consecutive_failures += 1
                helper.record_module_error(
                    message=f"Frame capture failed: {e}",
                    source="modules/screenscan/__init__.py:worker",
                    error_type=type(e).__name__,
                    priority=TicketPriority.P3,
                )

            # Alert on consecutive failures
            if _consecutive_failures >= failure_threshold:
                helper.record_module_error(
                    message=f"Screenscan capture failing consistently: {_consecutive_failures} consecutive failures",
                    source="modules/screenscan/__init__.py:worker",
                    error_type="ConsecutiveFailures",
                    priority=TicketPriority.P2,
                )

                record_agent_voice(
                    module_key="screenscan",
                    action="consecutive_failures_alert",
                    level="ERROR",
                    details=f"{_consecutive_failures} consecutive capture failures (threshold: {failure_threshold})",
                )

                # Reset counter after alerting to avoid spam
                _consecutive_failures = 0

            last_capture = now
            expected_capture_time += interval

        # Periodic storage quota check
        if now - last_cleanup_check >= cleanup_interval:
            try:
                _enforce_storage_quota(db, helper)
            except Exception as e:
                helper.record_module_error(
                    message=f"Storage quota enforcement failed: {e}",
                    source="modules/screenscan/__init__.py:worker",
                    error_type=type(e).__name__,
                    priority=TicketPriority.P3,
                )
            last_cleanup_check = now

        time.sleep(0.01)  # 10ms sleep to avoid busy-waiting

    record_agent_voice(
        module_key="screenscan",
        action="worker_stop",
        details=f"Screenscan worker stopped after {frame_count} frames",
    )


def _stop_capture_worker() -> None:
    """Stop the background capture worker thread."""
    global _worker_running, _worker_thread

    with _worker_lock:
        _worker_running = False
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=2.0)
        _worker_thread = None


class InstanceLock:
    """Single-instance lock to prevent concurrent screenscan workers (SC-027)."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.lock_file = None
        self.locked = False

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns True if successful."""
        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            self.lock_file = open(self.lock_path, 'w')
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(f"{os.getpid()}\n")
            self.lock_file.flush()
            self.locked = True
            return True
        except (IOError, OSError):
            return False

    def release(self) -> None:
        """Release the lock."""
        if self.lock_file and self.locked:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_UN)
                self.lock_file.close()
            except (IOError, OSError):
                pass
            self.locked = False

    def __del__(self):
        self.release()


def _validate_retention_config(fps: int, retention_seconds: int, helper: ModuleBase) -> tuple[int, int]:
    """Validate and normalize retention configuration.

    Returns: (validated_fps, validated_retention_seconds)
    """
    # Validate FPS
    if fps < 1 or fps > 10:
        helper.record_module_error(
            message=f"Invalid FPS {fps}, must be between 1 and 10. Using default 2.",
            source="modules/screenscan/__init__.py:_validate_retention_config",
            error_type="ConfigValidationError",
            priority=TicketPriority.P3,
        )
        fps = 2

    # Validate retention
    if retention_seconds < 10 or retention_seconds > 300:
        helper.record_module_error(
            message=f"Invalid retention {retention_seconds}s, must be between 10 and 300. Using default 60.",
            source="modules/screenscan/__init__.py:_validate_retention_config",
            error_type="ConfigValidationError",
            priority=TicketPriority.P3,
        )
        retention_seconds = 60

    # Check if ring buffer capacity is reasonable
    capacity = fps * retention_seconds
    if capacity > 600:  # More than 10 minutes at max FPS
        helper.record_module_error(
            message=f"Ring buffer capacity {capacity} frames may be excessive. Consider reducing fps or retention.",
            source="modules/screenscan/__init__.py:_validate_retention_config",
            error_type="ConfigWarning",
            priority=TicketPriority.P4,
        )

    record_agent_voice(
        module_key="screenscan",
        action="config_validated",
        details=f"Retention config validated: fps={fps}, retention={retention_seconds}s, capacity={capacity} frames",
    )

    return fps, retention_seconds


def _migrate_retention_config(db, old_capacity: int, new_capacity: int, helper: ModuleBase) -> None:
    """Migrate ring buffer when retention config changes."""
    try:
        if old_capacity == new_capacity:
            return

        conn = db.get_connection()
        cursor = conn.cursor()

        if new_capacity < old_capacity:
            # Shrinking - delete oldest frames beyond new capacity
            cursor.execute("SELECT COUNT(*) FROM screenscan_frames")
            current_frames = cursor.fetchone()[0]

            if current_frames > new_capacity:
                frames_to_delete = current_frames - new_capacity
                cursor.execute("""
                    DELETE FROM screenscan_frames
                    WHERE frame_seq IN (
                        SELECT frame_seq FROM screenscan_frames
                        ORDER BY frame_seq ASC
                        LIMIT ?
                    )
                """, (frames_to_delete,))

                record_agent_voice(
                    module_key="screenscan",
                    action="retention_migration",
                    level="WARNING",
                    details=f"Deleted {frames_to_delete} oldest frames during retention migration ({old_capacity} → {new_capacity})",
                )

        # Update capacity in state
        cursor.execute(
            "INSERT OR REPLACE INTO screenscan_state (key, value) VALUES ('capacity', ?)",
            (new_capacity,)
        )

        conn.commit()
        conn.close()

        record_agent_voice(
            module_key="screenscan",
            action="retention_config_migrated",
            details=f"Ring buffer capacity migrated from {old_capacity} to {new_capacity} frames",
        )

    except Exception as e:
        helper.record_module_error(
            message=f"Failed to migrate retention config: {e}",
            source="modules/screenscan/__init__.py:_migrate_retention_config",
            error_type=type(e).__name__,
            priority=TicketPriority.P2,
        )


def _ensure_screenscan_schema(db) -> None:
    """Ensure screenscan tables exist in the database."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # State table for ring buffer config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenscan_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Frames table with ring buffer design
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenscan_frames (
                slot INTEGER PRIMARY KEY,
                frame_seq INTEGER NOT NULL,
                captured_at TEXT NOT NULL,
                format TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                data BLOB NOT NULL,
                bytes INTEGER NOT NULL
            ) WITHOUT ROWID
        """)

        # Index on frame_seq for ordering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_screenscan_frames_seq
            ON screenscan_frames(frame_seq)
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        helper = _module_helper()
        helper.record_module_error(
            message=f"Failed to create screenscan schema: {e}",
            source="modules/screenscan/__init__.py:_ensure_screenscan_schema",
            error_type=type(e).__name__,
            priority=TicketPriority.P2,
        )


def _detect_capture_backend(platform_name: str, project_root, helper) -> str:
    """Detect available capture backend for the current platform."""
    if platform_name == "Darwin":
        return "macos"
    elif platform_name == "Windows":
        # Try to import pyautogui or similar for Windows
        return "windows_noop"  # Placeholder for now
    elif platform_name == "Linux":
        return "linux_noop"  # Placeholder for now
    else:
        return "unsupported"


def _capture_frame(backend: str, project_root, helper) -> Optional[dict]:
    """Capture a screenshot using the specified backend."""
    try:
        if backend == "macos":
            return _capture_macos()
        else:
            # For unsupported platforms, return None
            return None
    except Exception as e:
        helper.record_module_error(
            message=f"Failed to capture frame: {e}",
            source="modules/screenscan/__init__.py:_capture_frame",
            error_type=type(e).__name__,
            priority=TicketPriority.P3,
        )
        return None


def _capture_macos() -> Optional[dict]:
    """Capture screenshot on macOS using screencapture utility."""
    try:
        import subprocess
        import os
        from pathlib import Path
        from datetime import datetime

        # Use temporary file with timestamp to avoid race conditions
        temp_dir = "/tmp"
        temp_file = os.path.join(temp_dir, f"screenscan_{int(datetime.utcnow().timestamp() * 1000)}.png")

        try:
            # Use screencapture utility on macOS
            # -x: no beep
            # -m: capture main display only (most common case)
            result = subprocess.run(
                ["screencapture", "-x", "-m", temp_file],
                capture_output=True,
                timeout=1.5,  # Faster timeout
                check=False,
            )

            if result.returncode != 0:
                return None

            # Read the captured PNG
            if not os.path.exists(temp_file):
                return None

            with open(temp_file, "rb") as f:
                data = f.read()

            # Verify we got actual PNG data (minimum PNG header)
            if len(data) < 8 or not data.startswith(b'\x89PNG\r\n\x1a\n'):
                return None

            return {
                "format": "png",
                "width": 0,  # Could parse PNG header for actual dimensions
                "height": 0,
                "data": data,
                "bytes": len(data),
            }
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    except FileNotFoundError:
        # screencapture not found
        return None
    except subprocess.TimeoutExpired:
        # Capture took too long
        return None
    except Exception:
        # Any other error
        return None


def _store_frame(db, frame_data: dict, retention_seconds: int, fps: int) -> None:
    """Store a frame in the ring buffer."""
    try:
        from datetime import datetime

        conn = db.get_connection()
        cursor = conn.cursor()

        # Get current state
        cursor.execute("SELECT value FROM screenscan_state WHERE key='next_seq'")
        row = cursor.fetchone()
        next_seq = int(row[0]) if row else 0

        cursor.execute("SELECT value FROM screenscan_state WHERE key='capacity'")
        row = cursor.fetchone()
        capacity = int(row[0]) if row else (fps * retention_seconds)

        # Calculate slot and wrap around
        slot = next_seq % capacity

        # Insert frame
        captured_at = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO screenscan_frames
            (slot, frame_seq, captured_at, format, width, height, data, bytes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            slot,
            next_seq,
            captured_at,
            frame_data.get("format", "png"),
            frame_data.get("width", 0),
            frame_data.get("height", 0),
            frame_data.get("data", b""),
            frame_data.get("bytes", 0),
        ))

        # Update sequence counter
        cursor.execute(
            "INSERT OR REPLACE INTO screenscan_state (key, value) VALUES ('next_seq', ?)",
            (next_seq + 1,)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        helper = _module_helper()
        helper.record_module_error(
            message=f"Failed to store frame: {e}",
            source="modules/screenscan/__init__.py:_store_frame",
            error_type=type(e).__name__,
            priority=TicketPriority.P2,
        )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    url_prefix: Optional[str] = "/modules/screenscan",
) -> Blueprint:
    """Create the Flask blueprint that serves screenscan API endpoints."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, jsonify, request, Response

        blueprint = Blueprint("screenscan", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            """Serve the screenscan UI panel."""
            return Response(_HTML_PAGE, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            """Health check endpoint."""
            status = {
                "status": "ok",
                "worker_running": _worker_running,
                "module": "modules.screenscan",
            }
            return jsonify(status)

        @blueprint.route("/self-test")
        def selftest():
            """Run comprehensive self-test diagnostics."""
            results = self_test(project_root)
            status_code = 200 if results["overall_status"] == "healthy" else 503
            return jsonify(results), status_code

        @blueprint.route("/stats")
        def stats():
            """Statistics endpoint."""
            try:
                from actifix.persistence import get_database

                db = get_database(project_root)
                conn = db.get_connection()
                cursor = conn.cursor()

                # Get frame count
                cursor.execute("SELECT COUNT(*) FROM screenscan_frames")
                frame_count = cursor.fetchone()[0]

                # Get latest frame timestamp
                cursor.execute(
                    "SELECT captured_at FROM screenscan_frames ORDER BY frame_seq DESC LIMIT 1"
                )
                row = cursor.fetchone()
                last_capture = row[0] if row else None

                conn.close()

                # Get storage usage
                usage = _get_storage_usage(db)
                config = helper.get_config()
                quota = config.get("storage_quota_bytes", 50 * 1024 * 1024)

                return jsonify({
                    "frames": frame_count,
                    "last_capture": last_capture,
                    "fps": MODULE_DEFAULTS["fps"],
                    "retention_seconds": MODULE_DEFAULTS["retention_seconds"],
                    "storage": {
                        "used_bytes": usage["total_db_bytes"],
                        "quota_bytes": quota,
                        "utilization": usage["total_db_bytes"] / quota if quota > 0 else 0,
                        "frames_bytes": usage["frames_bytes"],
                        "frame_count": usage["frame_count"],
                    }
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @blueprint.route("/frames")
        def frames():
            """Get recent frames (metadata only by default)."""
            try:
                from actifix.persistence import get_database
                import json

                # Get client IP for rate limiting
                client_ip = request.remote_addr or "unknown"

                # Check rate limit
                if not _check_api_rate_limit(client_ip, helper):
                    config = helper.get_config()
                    rate_limit = config.get("api_rate_limit_per_minute", 60)
                    return jsonify({
                        "error": f"Rate limit exceeded. Maximum {rate_limit} requests per minute."
                    }), 429

                # Get configurable limits
                config = helper.get_config()
                MAX_LIMIT = config.get("api_max_frames_per_request", 120)
                MAX_TOTAL_BYTES = config.get("api_max_total_bytes", 100 * 1024 * 1024)

                limit = min(int(request.args.get("limit", 10)), MAX_LIMIT)
                include_data = request.args.get("include_data", "0") == "1"

                if limit < 1 or limit > MAX_LIMIT:
                    return jsonify({"error": f"Invalid limit. Must be between 1 and {MAX_LIMIT}"}), 400

                db = get_database(project_root)
                conn = db.get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT slot, frame_seq, captured_at, format, width, height, bytes
                    FROM screenscan_frames
                    ORDER BY frame_seq DESC
                    LIMIT ?
                """, (limit,))

                rows = cursor.fetchall()
                conn.close()

                frames_list = []
                total_bytes = 0

                for row in rows:
                    frame_bytes = row[6] if row[6] else 0

                    # Check payload limits
                    if include_data and (total_bytes + frame_bytes) > MAX_TOTAL_BYTES:
                        record_agent_voice(
                            module_key="screenscan",
                            action="payload_limit_enforced",
                            details=f"Request would exceed {MAX_TOTAL_BYTES} bytes, truncating at {len(frames_list)} frames",
                        )
                        break

                    frame_entry = {
                        "slot": row[0],
                        "frame_seq": row[1],
                        "captured_at": row[2],
                        "format": row[3],
                        "width": row[4],
                        "height": row[5],
                        "bytes": row[6],
                    }

                    frames_list.append(frame_entry)
                    total_bytes += frame_bytes

                return jsonify({
                    "frames": frames_list,
                    "count": len(frames_list),
                    "total_bytes": total_bytes,
                    "include_data": include_data,
                    "rate_limit_remaining": config.get("api_rate_limit_per_minute", 60) - len(_api_request_log.get(client_ip, [])),
                })
            except Exception as e:
                helper.record_module_error(
                    message=f"Failed to retrieve frames: {e}",
                    source="modules/screenscan/__init__.py:frames",
                    error_type=type(e).__name__,
                    priority=TicketPriority.P2,
                )
                return jsonify({"error": str(e)}), 500

        log_event(
            "SCREENSCAN_BLUEPRINT_CREATED",
            f"Screenscan blueprint created at {url_prefix}",
            extra={"module": "modules.screenscan"},
            source="modules/screenscan/__init__.py:create_blueprint",
        )
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create screenscan blueprint: {exc}",
            source="modules/screenscan/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def start_module(project_root: Optional[Union[str, Path]] = None) -> None:
    """Start the screenscan module with config validation, privacy checks, and migration."""
    helper = _module_helper(project_root)
    try:
        # Privacy consent check
        config = helper.get_config()
        if config.get("privacy_opt_in_required", True):
            consent_var = config.get("privacy_consent_env_var", "ACTIFIX_SCREENSCAN_CONSENT")
            consent = os.getenv(consent_var, "").lower() in ("1", "true", "yes")

            if not consent:
                record_agent_voice(
                    module_key="screenscan",
                    action="privacy_consent_required",
                    level="WARNING",
                    details=f"Screenscan requires privacy consent via {consent_var}=true",
                )
                raise RuntimeError(f"Privacy consent required. Set {consent_var}=true to enable screenscan.")

        # Ensure schema
        from actifix.persistence import get_database
        db = get_database(project_root)
        _ensure_screenscan_schema(db)

        # Get and validate retention config
        fps = MODULE_DEFAULTS["fps"]
        retention = MODULE_DEFAULTS["retention_seconds"]
        fps, retention = _validate_retention_config(fps, retention, helper)

        # Check if capacity changed and migrate if needed
        new_capacity = fps * retention
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM screenscan_state WHERE key='capacity'")
        row = cursor.fetchone()
        old_capacity = int(row[0]) if row else new_capacity
        conn.close()

        if old_capacity != new_capacity:
            _migrate_retention_config(db, old_capacity, new_capacity, helper)

        # Start worker
        _start_capture_worker(project_root, fps, retention)

        record_agent_voice(
            module_key="screenscan",
            action="module_started",
            details="Screenscan module started successfully",
        )

        log_event(
            "SCREENSCAN_STARTED",
            "Screenscan module started",
            extra={"module": "modules.screenscan", "fps": fps, "retention": retention},
            source="modules/screenscan/__init__.py:start_module",
        )
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start screenscan module: {exc}",
            source="modules/screenscan/__init__.py:start_module",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


def self_test(project_root: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Run self-test diagnostics for screenscan module.

    Returns a dict with test results for production diagnostics.
    """
    helper = _module_helper(project_root)
    results = {
        "overall_status": "unknown",
        "tests": {},
        "timestamp": time.time(),
    }

    try:
        from actifix.persistence import get_database
        import platform

        # Test 1: Worker status
        worker_test = {
            "name": "Worker Running",
            "status": "pass" if _worker_running else "fail",
            "details": f"Worker thread alive: {_worker_thread.is_alive() if _worker_thread else False}",
        }
        results["tests"]["worker"] = worker_test

        # Test 2: Database connectivity
        try:
            db = get_database(project_root)
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM screenscan_frames")
            frame_count = cursor.fetchone()[0]
            conn.close()

            db_test = {
                "name": "Database",
                "status": "pass",
                "details": f"Connected, {frame_count} frames stored",
            }
        except Exception as e:
            db_test = {
                "name": "Database",
                "status": "fail",
                "details": f"Database error: {str(e)[:100]}",
            }
        results["tests"]["database"] = db_test

        # Test 3: Capture backend availability
        platform_name = platform.system()
        backend = _detect_capture_backend(platform_name, project_root, helper)
        backend_test = {
            "name": "Capture Backend",
            "status": "pass" if backend not in ["unsupported", "linux_noop", "windows_noop"] else "warn",
            "details": f"Platform: {platform_name}, Backend: {backend}",
        }
        results["tests"]["backend"] = backend_test

        # Test 4: Recent capture activity
        try:
            db = get_database(project_root)
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT captured_at FROM screenscan_frames ORDER BY frame_seq DESC LIMIT 1"
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                from datetime import datetime
                last_capture = datetime.fromisoformat(row[0])
                age_seconds = (datetime.utcnow() - last_capture).total_seconds()

                activity_test = {
                    "name": "Recent Activity",
                    "status": "pass" if age_seconds < 60 else "warn" if age_seconds < 300 else "fail",
                    "details": f"Last capture {age_seconds:.1f}s ago",
                }
            else:
                activity_test = {
                    "name": "Recent Activity",
                    "status": "warn",
                    "details": "No captures yet",
                }
        except Exception as e:
            activity_test = {
                "name": "Recent Activity",
                "status": "fail",
                "details": f"Error checking activity: {str(e)[:100]}",
            }
        results["tests"]["activity"] = activity_test

        # Test 5: Storage health
        try:
            usage = _get_storage_usage(db)
            config = helper.get_config()
            quota = config.get("storage_quota_bytes", 50 * 1024 * 1024)
            utilization = usage["total_db_bytes"] / quota if quota > 0 else 0

            storage_test = {
                "name": "Storage",
                "status": "pass" if utilization < 0.8 else "warn" if utilization < 1.0 else "fail",
                "details": f"Using {usage['total_db_bytes'] // 1024}KB / {quota // 1024}KB ({utilization:.1%})",
            }
        except Exception as e:
            storage_test = {
                "name": "Storage",
                "status": "warn",
                "details": f"Could not check storage: {str(e)[:100]}",
            }
        results["tests"]["storage"] = storage_test

        # Determine overall status
        test_statuses = [t["status"] for t in results["tests"].values()]
        if all(s == "pass" for s in test_statuses):
            results["overall_status"] = "healthy"
        elif any(s == "fail" for s in test_statuses):
            results["overall_status"] = "unhealthy"
        else:
            results["overall_status"] = "degraded"

        record_agent_voice(
            module_key="screenscan",
            action="self_test_complete",
            level="INFO" if results["overall_status"] == "healthy" else "WARNING",
            details=f"Self-test completed: {results['overall_status']} ({len(results['tests'])} tests)",
        )

    except Exception as exc:
        helper.record_module_error(
            message=f"Self-test failed: {exc}",
            source="modules/screenscan/__init__.py:self_test",
            error_type=type(exc).__name__,
            priority=TicketPriority.P3,
        )
        results["overall_status"] = "error"
        results["error"] = str(exc)

    return results


def stop_module(project_root: Optional[Union[str, Path]] = None) -> None:
    """Stop the screenscan module (SC-039: robust shutdown)."""
    global _worker_thread, _worker_running
    helper = _module_helper(project_root)

    try:
        # Signal worker to stop
        with _worker_lock:
            _worker_running = False

        # Wait for worker thread to finish (with timeout)
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=3.0)

            # Force cleanup if thread didn't exit cleanly
            if _worker_thread.is_alive():
                helper.record_module_error(
                    message="Screenscan worker thread did not shut down cleanly within timeout",
                    source="modules/screenscan/__init__.py:stop_module",
                    error_type="ThreadTimeoutError",
                    priority=TicketPriority.P2,
                )

        # Clear thread reference
        _worker_thread = None

        record_agent_voice(
            module_key="screenscan",
            action="module_stopped",
            details="Screenscan module stopped gracefully",
        )

        log_event(
            "SCREENSCAN_STOPPED",
            "Screenscan module stopped",
            extra={"module": "modules.screenscan"},
            source="modules/screenscan/__init__.py:stop_module",
        )
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to stop screenscan module: {exc}",
            source="modules/screenscan/__init__.py:stop_module",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )


# HTML page for screenscan UI panel
_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Screenscan Monitor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #1a202c;
      padding: 24px;
      min-height: 100vh;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    header {
      background: white;
      border-radius: 12px;
      padding: 24px 32px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
      font-size: 28px;
      font-weight: 700;
      color: #2d3748;
      margin-bottom: 8px;
    }
    .subtitle {
      color: #718096;
      font-size: 14px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stat-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #a0aec0;
      margin-bottom: 8px;
      font-weight: 600;
    }
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: #2d3748;
    }
    .stat-unit {
      font-size: 14px;
      color: #718096;
      margin-left: 4px;
    }
    .frames-panel {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .panel-title {
      font-size: 18px;
      font-weight: 700;
      color: #2d3748;
      margin-bottom: 16px;
    }
    .frames-list {
      max-height: 400px;
      overflow-y: auto;
    }
    .frame-item {
      border-bottom: 1px solid #e2e8f0;
      padding: 12px 0;
      display: grid;
      grid-template-columns: 80px 150px 100px 100px 1fr;
      gap: 16px;
      align-items: center;
      font-size: 14px;
    }
    .frame-item:last-child {
      border-bottom: none;
    }
    .frame-seq {
      font-weight: 600;
      color: #667eea;
    }
    .frame-time {
      color: #718096;
      font-size: 12px;
    }
    .frame-size {
      color: #4a5568;
    }
    .frame-dims {
      color: #718096;
      font-size: 12px;
    }
    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-right: 6px;
    }
    .status-running { background-color: #48bb78; }
    .status-stopped { background-color: #f56565; }
    .refresh-btn {
      background: #667eea;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      margin-top: 16px;
    }
    .refresh-btn:hover {
      background: #5a67d8;
    }
    .error {
      background: #fed7d7;
      color: #c53030;
      padding: 12px 16px;
      border-radius: 6px;
      margin-bottom: 16px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Screenscan Monitor</h1>
      <p class="subtitle">Real-time screen capture monitoring and frame statistics</p>
    </header>

    <div id="error-container"></div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Worker Status</div>
        <div class="stat-value" id="worker-status">
          <span class="status-dot status-stopped"></span>
          <span id="status-text">Loading...</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Frames</div>
        <div class="stat-value">
          <span id="frame-count">-</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Capture Rate</div>
        <div class="stat-value">
          <span id="fps">-</span>
          <span class="stat-unit">fps</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Retention</div>
        <div class="stat-value">
          <span id="retention">-</span>
          <span class="stat-unit">sec</span>
        </div>
      </div>
    </div>

    <div class="frames-panel">
      <div class="panel-title">Recent Frames</div>
      <div class="frames-list" id="frames-list">
        <p style="color: #a0aec0; text-align: center; padding: 32px;">Loading frames...</p>
      </div>
      <button class="refresh-btn" onclick="loadData()">Refresh</button>
    </div>
  </div>

  <script>
    async function loadData() {
      try {
        // Load stats
        const statsResp = await fetch('/modules/screenscan/stats');
        const stats = await statsResp.json();

        document.getElementById('frame-count').textContent = stats.frames || 0;
        document.getElementById('fps').textContent = stats.fps || 2;
        document.getElementById('retention').textContent = stats.retention_seconds || 60;

        // Load health
        const healthResp = await fetch('/modules/screenscan/health');
        const health = await healthResp.json();

        const statusDot = document.querySelector('.status-dot');
        const statusText = document.getElementById('status-text');

        if (health.worker_running) {
          statusDot.className = 'status-dot status-running';
          statusText.textContent = 'Running';
        } else {
          statusDot.className = 'status-dot status-stopped';
          statusText.textContent = 'Stopped';
        }

        // Load frames (metadata only)
        const framesResp = await fetch('/modules/screenscan/frames?limit=20&include_data=0');
        const framesData = await framesResp.json();

        const framesList = document.getElementById('frames-list');
        if (framesData.frames && framesData.frames.length > 0) {
          framesList.innerHTML = framesData.frames.map(f => {
            const time = new Date(f.captured_at).toLocaleTimeString();
            const size = (f.bytes / 1024).toFixed(1);
            const dims = f.width && f.height ? `${f.width}×${f.height}` : 'N/A';
            return `
              <div class="frame-item">
                <div class="frame-seq">#${f.frame_seq}</div>
                <div class="frame-time">${time}</div>
                <div class="frame-size">${size} KB</div>
                <div class="frame-dims">${dims}</div>
                <div>${f.format.toUpperCase()}</div>
              </div>
            `;
          }).join('');
        } else {
          framesList.innerHTML = '<p style="color: #a0aec0; text-align: center; padding: 32px;">No frames captured yet</p>';
        }

        // Clear errors
        document.getElementById('error-container').innerHTML = '';
      } catch (err) {
        document.getElementById('error-container').innerHTML = `
          <div class="error">Failed to load screenscan data: ${err.message}</div>
        `;
      }
    }

    // Load data on page load
    loadData();

    // Auto-refresh every 5 seconds
    setInterval(loadData, 5000);
  </script>
</body>
</html>
"""
