"""Screenscan module: always-on screen capture with ring-buffer storage."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority
from actifix.modules.base import ModuleBase
from actifix.agent_voice import record_agent_voice

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "fps": 2,  # Frames per second
    "retention_seconds": 60,  # Retain last 60 seconds only
    "enabled": True,
    "capture_backend": "auto",  # auto, macos, windows, linux, none
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


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for screenscan."""
    return ModuleBase(
        module_key="screenscan",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _start_capture_worker(
    project_root: Optional[Union[str, Path]] = None,
    fps: int = 2,
    retention_seconds: int = 60,
) -> None:
    """Start the background capture worker thread."""
    global _worker_thread, _worker_running

    with _worker_lock:
        if _worker_running:
            return

        _worker_running = True
        helper = _module_helper(project_root)

        def worker():
            """Background worker that captures screenshots periodically."""
            global _worker_running
            try:
                from actifix.persistence import get_database
                import platform

                db = get_database(project_root)

                # Ensure schema exists
                _ensure_screenscan_schema(db)

                interval = 1.0 / fps
                platform_name = platform.system()
                backend = _detect_capture_backend(platform_name, project_root, helper)

                record_agent_voice(
                    module_key="screenscan",
                    action="worker_start",
                    details=f"Starting screenscan worker (fps={fps}, retention={retention_seconds}s, backend={backend})",
                )

                last_capture = time.time()
                frame_count = 0

                while _worker_running:
                    now = time.time()
                    if now - last_capture >= interval:
                        try:
                            frame_data = _capture_frame(backend, project_root, helper)
                            if frame_data:
                                _store_frame(db, frame_data, retention_seconds, fps)
                                frame_count += 1
                        except Exception as e:
                            helper.record_module_error(
                                message=f"Frame capture failed: {e}",
                                source="modules/screenscan/__init__.py:worker",
                                error_type=type(e).__name__,
                                priority=TicketPriority.P3,
                            )
                        last_capture = now

                    time.sleep(0.01)  # 10ms sleep to avoid busy-waiting

                record_agent_voice(
                    module_key="screenscan",
                    action="worker_stop",
                    details=f"Screenscan worker stopped after {frame_count} frames",
                )
            except Exception as exc:
                helper = _module_helper(project_root)
                helper.record_module_error(
                    message=f"Screenscan worker crashed: {exc}",
                    source="modules/screenscan/__init__.py:worker",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P1,
                )
            finally:
                with _worker_lock:
                    _worker_running = False

        _worker_thread = threading.Thread(target=worker, daemon=True, name="screenscan-worker")
        _worker_thread.start()


def _stop_capture_worker() -> None:
    """Stop the background capture worker thread."""
    global _worker_running, _worker_thread

    with _worker_lock:
        _worker_running = False
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=2.0)
        _worker_thread = None


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
        from flask import Blueprint, jsonify, request

        blueprint = Blueprint("screenscan", __name__, url_prefix=url_prefix)

        @blueprint.route("/health")
        def health():
            """Health check endpoint."""
            status = {
                "status": "ok",
                "worker_running": _worker_running,
                "module": "modules.screenscan",
            }
            return jsonify(status)

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

                return jsonify({
                    "frames": frame_count,
                    "last_capture": last_capture,
                    "fps": MODULE_DEFAULTS["fps"],
                    "retention_seconds": MODULE_DEFAULTS["retention_seconds"],
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @blueprint.route("/frames")
        def frames():
            """Get recent frames (metadata only by default)."""
            try:
                from actifix.persistence import get_database
                import json

                # SC-026: API safeguards - enforce limits
                MAX_LIMIT = 120
                MAX_TOTAL_BYTES = 100 * 1024 * 1024  # 100MB max total

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
                            details=f"Request would exceed {MAX_TOTAL_BYTES} bytes, truncating",
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
    """Start the screenscan module."""
    helper = _module_helper(project_root)
    try:
        # Ensure schema
        from actifix.persistence import get_database
        db = get_database(project_root)
        _ensure_screenscan_schema(db)

        # Start worker
        fps = MODULE_DEFAULTS["fps"]
        retention = MODULE_DEFAULTS["retention_seconds"]
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
