#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actifix Launcher
================

Lightweight starter for the generic Actifix system. It prepares the
Actifix scaffold, enables error capture, runs a quick health check, and
serves both the static web interface and API backend.

Usage:
    python scripts/start.py                     # init + health + start web UI + API
    python scripts/start.py --setup-only        # init only, no servers
    python scripts/start.py --health-only       # health check and exit
    python scripts/start.py --frontend-port 8081
    python scripts/start.py --api-port 5002
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import signal
import atexit
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
FRONTEND_DIR = ROOT / "actifix-frontend"
DEFAULT_FRONTEND_PORT = 8080
DEFAULT_API_PORT = 5001
VERSION_LINE_RE = re.compile(r'^version\s*=\s*["\'](?P<version>[^"\']+)["\']', re.MULTILINE)

# Global singleton instances - only one of each can exist
_API_SERVER_INSTANCE: Optional[threading.Thread] = None
_API_SERVER_LOCK = threading.Lock()
_FRONTEND_MANAGER_INSTANCE: Optional['FrontendManager'] = None
_FRONTEND_LOCK = threading.Lock()

# ANSI Color codes for terminal output
class Color:
    """ANSI color codes for beautiful terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    @staticmethod
    def disable_on_windows():
        """Disable colors on Windows if ANSI not supported."""
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                # Fallback: disable colors
                Color.RED = Color.GREEN = Color.BLUE = ''
                Color.YELLOW = Color.CYAN = Color.MAGENTA = ''
                Color.BOLD = Color.UNDERLINE = Color.RESET = ''

Color.disable_on_windows()


def log(message: str) -> None:
    """Standard log prefix for launcher output."""
    print(f"[Actifix] {message}")


def log_info(message: str) -> None:
    """Log informational message in blue."""
    print(f"{Color.BLUE}[INFO]{Color.RESET} {message}")


def log_success(message: str) -> None:
    """Log success message in green."""
    print(f"{Color.GREEN}[✓]{Color.RESET} {message}")


def log_error(message: str) -> None:
    """Log error message in red."""
    print(f"{Color.RED}[✗]{Color.RESET} {message}")


def log_warning(message: str) -> None:
    """Log warning message in yellow."""
    print(f"{Color.YELLOW}[!]{Color.RESET} {message}")


def log_step(step_num: int, total: int, message: str) -> None:
    """Log a step in a multi-step process."""
    print(f"{Color.CYAN}[{step_num}/{total}]{Color.RESET} {message}")


def print_banner(text: str) -> None:
    """Print a banner with the given text."""
    line = "=" * 60
    print(f"\n{Color.BOLD}{Color.CYAN}{line}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{text.center(60)}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{line}{Color.RESET}\n")


def clean_bytecode_cache() -> None:
    """Remove stale .pyc files to avoid version mismatches."""
    log_info("Cleaning bytecode cache...")
    cleaned = 0
    for pyc in SRC_DIR.rglob("*.pyc"):
        try:
            pyc.unlink()
            cleaned += 1
        except OSError:
            pass
    if cleaned:
        log_success(f"Removed {cleaned} stale .pyc file(s)")
    else:
        log_info("Bytecode cache is clean")


def ensure_scaffold() -> None:
    """Create Actifix directories and files if missing."""
    log_info("Initializing Actifix environment...")

    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    # Defer imports until path is set
    from actifix.state_paths import get_actifix_paths, init_actifix_files
    from actifix.raise_af import ACTIFIX_CAPTURE_ENV_VAR, enforce_raise_af_only

    # Set required environment variable for Raise_AF enforcement
    if "ACTIFIX_CHANGE_ORIGIN" not in os.environ:
        os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
        log_info("Set ACTIFIX_CHANGE_ORIGIN=raise_af (required for operation)")

    os.environ.setdefault(ACTIFIX_CAPTURE_ENV_VAR, "1")

    try:
        paths = get_actifix_paths()
        enforce_raise_af_only(paths)
        init_actifix_files(paths)
        log_success("Actifix environment initialized")

        # Get database path
        env_db = os.environ.get("ACTIFIX_DB_PATH")
        if env_db:
            db_path = Path(env_db)
        else:
            db_path = paths.project_root / "data" / "actifix.db"

        log_info(f"Project root: {paths.project_root}")
        log_info(f"State directory: {paths.state_dir}")
        log_info(f"Database: {db_path}")
    except Exception as e:
        log_error(f"Failed to initialize Actifix: {e}")
        raise


def is_port_in_use(port: int) -> bool:
    """Return True if a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_frontend(port: int) -> subprocess.Popen:
    """Launch the static frontend server."""
    cmd = [sys.executable, "-m", "http.server", str(port)]
    return subprocess.Popen(cmd, cwd=FRONTEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def kill_processes_on_port(port: int) -> None:
    """Terminate any processes listening on the given TCP port."""
    try:
        result = subprocess.run(["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True)
        pids = [pid for pid in result.stdout.splitlines() if pid.strip()]
        if pids:
            log_warning(f"Found {len(pids)} stale process(es) on port {port}")
        for pid in pids:
            if pid.isdigit():
                log_info(f"Terminating process {pid}...")
                os.kill(int(pid), signal.SIGTERM)
                log_success(f"Terminated process {pid}")
    except Exception as e:
        log_error(f"Failed to kill processes on port {port}: {e}")


def cleanup_existing_instances() -> None:
    """Kill any existing Actifix processes before starting new ones."""
    log_info("Checking for existing Actifix instances...")

    cleaned = False

    # Get current process ID to avoid killing ourselves
    current_pid = os.getpid()

    try:
        # Find all start.py processes except this one
        result = subprocess.run(
            ["pgrep", "-f", "start.py"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
            for pid_str in pids:
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid != current_pid:
                        try:
                            log_info(f"Terminating existing start.py process {pid}")
                            os.kill(pid, signal.SIGTERM)
                            cleaned = True
                        except ProcessLookupError:
                            pass
                        except Exception as e:
                            log_warning(f"Could not kill process {pid}: {e}")
    except FileNotFoundError:
        # pgrep not available, try alternative method
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.splitlines():
                if "start.py" in line and str(current_pid) not in line:
                    try:
                        pid = int(line.split()[1])
                        log_info(f"Terminating existing start.py process {pid}")
                        os.kill(pid, signal.SIGTERM)
                        cleaned = True
                    except (ValueError, IndexError, ProcessLookupError):
                        pass
        except Exception:
            pass
    except Exception:
        pass

    # Kill any http.server processes on our ports
    for port in [DEFAULT_FRONTEND_PORT, DEFAULT_API_PORT]:
        if is_port_in_use(port):
            log_warning(f"Port {port} is in use")
            kill_processes_on_port(port)
            cleaned = True

    if cleaned:
        log_success("Cleaned up existing instances")
        time.sleep(0.5)  # Give processes time to terminate
    else:
        log_success("No existing instances found")


def start_api_server(port: int, project_root: Path) -> threading.Thread:
    """Launch the API server in a background thread. Enforces singleton - only one instance can exist."""
    global _API_SERVER_INSTANCE

    with _API_SERVER_LOCK:
        if _API_SERVER_INSTANCE is not None and _API_SERVER_INSTANCE.is_alive():
            log_warning("API server already running - refusing to start duplicate instance")
            return _API_SERVER_INSTANCE

        log_info(f"Starting API server on port {port}...")

        def run_server():
            try:
                from actifix.api import create_app
                app = create_app(project_root)
                log_success(f"API server initialized on http://127.0.0.1:{port}")
                # Use werkzeug's run_simple for better control
                from werkzeug.serving import run_simple
                run_simple(
                    '127.0.0.1',
                    port,
                    app,
                    use_reloader=False,
                    use_debugger=False,
                    threaded=True,
                )
            except ImportError as e:
                log_error(f"API server failed to start: {e}")
                log_error("Install Flask with: pip install flask flask-cors")
            except Exception as e:
                log_error(f"API server error: {e}")

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        _API_SERVER_INSTANCE = thread
        # Give the server a moment to start
        time.sleep(0.5)
        return thread


def read_project_version(project_root: Path) -> Optional[str]:
    """Return the current project version from pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except OSError:
        return None

    match = VERSION_LINE_RE.search(text)
    if match:
        return match.group("version").strip()
    return None


class FrontendManager:
    """Thread-safe helper for managing the frontend server process. Enforces singleton pattern."""

    _instance: Optional['FrontendManager'] = None
    _instance_lock = threading.Lock()

    def __new__(cls, port: int) -> 'FrontendManager':
        """Enforce singleton pattern - only one FrontendManager can exist."""
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                cls._instance = instance
                log("FrontendManager singleton instance created")
            else:
                log("FrontendManager singleton already exists - returning existing instance")
            return cls._instance

    def __init__(self, port: int) -> None:
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self.port = port
            self._lock = threading.Lock()
            self._server: Optional[subprocess.Popen] = None
            self._initialized = True
            # Register cleanup on exit
            atexit.register(self._cleanup_on_exit)

    def start(self) -> subprocess.Popen:
        with self._lock:
            if self._server is not None and self._server.poll() is None:
                log_warning("Frontend server already running - refusing to start duplicate instance")
                return self._server
            log_info(f"Starting frontend server on port {self.port}...")
            self._server = start_frontend(self.port)
            time.sleep(0.3)  # Give server time to start
            log_success(f"Frontend server started on http://localhost:{self.port}")
            return self._server

    def restart(self) -> Optional[subprocess.Popen]:
        with self._lock:
            log_info("Restarting frontend server...")
            self._terminate_current()
            self._server = start_frontend(self.port)
            log_success("Frontend server restarted")
            return self._server

    def get_process(self) -> Optional[subprocess.Popen]:
        with self._lock:
            return self._server

    def _terminate_current(self) -> None:
        if self._server and self._server.poll() is None:
            try:
                log_info("Stopping frontend server...")
                self._server.terminate()
                self._server.wait(timeout=5)
                log_success("Frontend server stopped")
            except subprocess.TimeoutExpired:
                log_warning("Frontend server didn't stop gracefully, forcing...")
                self._server.kill()
            finally:
                self._server = None

    def _cleanup_on_exit(self) -> None:
        """Cleanup handler called on exit."""
        with self._lock:
            self._terminate_current()


def start_version_monitor(
    manager: FrontendManager,
    project_root: Path,
    interval_seconds: float = 60.0,
    stop_event: Optional[threading.Event] = None,
) -> threading.Thread:
    """Monitor pyproject version changes and bounce the frontend when needed."""

    def monitor_loop() -> None:
        last_version = read_project_version(project_root)
        while True:
            if stop_event and stop_event.is_set():
                break
            time.sleep(interval_seconds)
            current_version = read_project_version(project_root)
            if current_version != last_version:
                log_info(
                    f"Version change detected: "
                    f"{last_version or 'unknown'} -> {current_version or 'unknown'}"
                )
                try:
                    kill_processes_on_port(manager.port)
                except Exception:
                    pass
                manager.restart()
                last_version = current_version

    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    return thread


def run_health_check() -> bool:
    """Run Actifix health check and return True if healthy."""
    log_info("Running health check...")
    try:
        from actifix.health import run_health_check
        result = run_health_check(print_report=True)
        is_healthy = bool(getattr(result, "healthy", False))
        if is_healthy:
            log_success("Health check passed!")
        else:
            log_error("Health check failed - see details above")
        return is_healthy
    except Exception as e:
        log_error(f"Health check error: {e}")
        return False


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Actifix launcher")
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=DEFAULT_FRONTEND_PORT,
        help=f"Port for static frontend (default: {DEFAULT_FRONTEND_PORT})",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=DEFAULT_API_PORT,
        help=f"Port for API server (default: {DEFAULT_API_PORT})",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Initialize Actifix and exit without starting servers",
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Run health check after init and exit",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        default=False,
        help="Open the browser automatically (disabled by default to prevent unwanted windows)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Do not start the API server",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point with beautiful color-coded output."""
    args = parse_args(argv)

    # Print startup banner
    print_banner("ACTIFIX STARTUP")

    # Step 0: Cleanup existing instances first
    cleanup_existing_instances()

    total_steps = 5 if not args.no_api else 4
    current_step = 0

    # Step 1: Clean cache
    current_step += 1
    log_step(current_step, total_steps, "Cleaning Python bytecode cache")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    clean_bytecode_cache()

    # Step 2: Initialize environment
    current_step += 1
    log_step(current_step, total_steps, "Initializing Actifix environment")
    try:
        ensure_scaffold()
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        return 1

    # Optional: Setup dock icon on macOS
    try:
        from actifix.dock_icon import setup_dock_icon
        setup_dock_icon()
        log_info("Dock icon configured (macOS)")
    except Exception:
        # Dock icon setup is best-effort; ignore failures on non-macOS
        pass

    # Handle special modes
    if args.health_only:
        print_banner("HEALTH CHECK")
        healthy = run_health_check()
        return 0 if healthy else 1

    if args.setup_only:
        log_success("Initialization complete (setup-only mode)")
        return 0

    # Step 3: Validate frontend directory
    current_step += 1
    log_step(current_step, total_steps, "Validating frontend directory")
    if not FRONTEND_DIR.exists():
        log_error(f"Frontend directory missing: {FRONTEND_DIR}")
        return 1
    log_success(f"Frontend directory found: {FRONTEND_DIR}")

    # Final port check (should be clean after cleanup_existing_instances)
    if is_port_in_use(args.frontend_port):
        log_warning(f"Port {args.frontend_port} still in use, forcing cleanup")
        kill_processes_on_port(args.frontend_port)
        time.sleep(0.5)

    if not args.no_api and is_port_in_use(args.api_port):
        log_warning(f"API port {args.api_port} still in use, forcing cleanup")
        kill_processes_on_port(args.api_port)
        time.sleep(0.5)

        # Final check
        if is_port_in_use(args.api_port):
            log_error(f"Could not free API port {args.api_port}")
            log_error("Try manually: pkill -f 'start.py' or use --api-port <PORT>")
            return 1

    # Step 4: Start API server (if enabled)
    api_thread = None
    if not args.no_api:
        current_step += 1
        log_step(current_step, total_steps, "Starting API server")
        try:
            api_thread = start_api_server(args.api_port, ROOT)
        except Exception as e:
            log_error(f"Failed to start API server: {e}")
            return 1

    # Step 5: Start frontend server
    current_step += 1
    log_step(current_step, total_steps, "Starting frontend server")
    try:
        frontend_manager = FrontendManager(args.frontend_port)
        frontend_manager.start()
        start_version_monitor(frontend_manager, ROOT)
    except Exception as e:
        log_error(f"Failed to start frontend server: {e}")
        return 1

    # Success banner
    print_banner("ACTIFIX IS READY!")

    # Display access information
    url = f"http://localhost:{args.frontend_port}"
    print(f"{Color.BOLD}{Color.GREEN}Frontend:{Color.RESET}  {Color.CYAN}{url}{Color.RESET}")
    if not args.no_api:
        api_url = f"http://localhost:{args.api_port}/api/"
        print(f"{Color.BOLD}{Color.GREEN}API:{Color.RESET}       {Color.CYAN}{api_url}{Color.RESET}")

    print()

    # Optional: Open browser
    if args.browser:
        try:
            log_info("Opening browser...")
            webbrowser.open(url)
            log_success("Browser opened")
        except Exception:
            log_warning("Browser launch failed - please open URL manually")
    else:
        log_info("Tip: Use --browser flag to auto-open browser")

    print()
    print(f"{Color.YELLOW}Press Ctrl+C to stop all servers{Color.RESET}")
    print()

    # Keep process alive
    try:
        while True:
            time.sleep(1.0)
            current_server = frontend_manager.get_process()
            if current_server and current_server.poll() is not None:
                log_error("Frontend server stopped unexpectedly")
                return current_server.returncode or 1
    except KeyboardInterrupt:
        print()
        log_info("Shutdown signal received...")
        log_info("Stopping servers...")
        current_server = frontend_manager.get_process()
        if current_server:
            current_server.terminate()
            try:
                current_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current_server.kill()
        log_success("All servers stopped")
        log_success("Goodbye!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
