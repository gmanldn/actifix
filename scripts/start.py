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
import platform
import atexit
from pathlib import Path
from typing import Optional

# Detect the repository root (pyproject marker) so we can import sibling packages reliably.
_SCRIPT_DIR = Path(__file__).resolve().parent
for _candidate in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
    if (_candidate / "pyproject.toml").is_file():
        ROOT = _candidate
        break
else:
    ROOT = _SCRIPT_DIR.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_frontend import build_frontend
SRC_DIR = ROOT / "src"
FRONTEND_DIR = ROOT / "actifix-frontend"
DEFAULT_FRONTEND_PORT = 8080
DEFAULT_API_PORT = 5001
DEFAULT_YHATZEE_PORT = 8090
DEFAULT_SUPERQUIZ_PORT = 8070
DEFAULT_SHOOTY_PORT = 8040
DEFAULT_POKERTOOL_PORT = 8060
VERSION_LINE_RE = re.compile(r'^version\s*=\s*["\'](?P<version>[^"\']+)["\']', re.MULTILINE)


# Global singleton instances - only one of each can exist
_API_SERVER_INSTANCE: Optional[threading.Thread] = None
_API_SERVER_LOCK = threading.Lock()
_YHATZEE_SERVER_INSTANCE: Optional[threading.Thread] = None
_YHATZEE_SERVER_LOCK = threading.Lock()
_SUPERQUIZ_SERVER_INSTANCE: Optional[threading.Thread] = None
_SUPERQUIZ_SERVER_LOCK = threading.Lock()
_FRONTEND_MANAGER_INSTANCE: Optional['FrontendManager'] = None
_FRONTEND_LOCK = threading.Lock()
_POKERTOOL_THREAD: Optional[threading.Thread] = None
_POKERTOOL_LOCK = threading.Lock()

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
        _ensure_frontend_build(paths.project_root)
    except Exception as e:
        log_error(f"Failed to initialize Actifix: {e}")
        raise


def _ensure_frontend_build(project_root: Path) -> None:
    """Ensure the frontend bundle is built."""
    log_info("Rebuilding frontend assets...")
    try:
        build_frontend(project_root)
        log_success("Frontend assets ready")
    except FileNotFoundError as exc:
        log_warning(f"Frontend bundle skipped: {exc}")


def is_port_in_use(port: int) -> bool:
    """Return True if a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_frontend(port: int) -> subprocess.Popen:
    """Launch the static frontend server."""
    cmd = [sys.executable, "-m", "http.server", str(port)]
    serve_dir = FRONTEND_DIR / "dist" if (FRONTEND_DIR / "dist").exists() else FRONTEND_DIR
    return subprocess.Popen(cmd, cwd=serve_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def kill_processes_on_port(port: int) -> None:
    """Terminate any processes listening on the given TCP port."""
    system = platform.system()
    pids = []
    if system == "Windows":
        try:
            ps_cmd = f'Get-NetTCPConnection -LocalPort {port} -State Listen | Select-Object -ExpandProperty OwningProcess'
            output = subprocess.check_output(["powershell.exe", "-Command", ps_cmd], text=True, stderr=subprocess.STDOUT, timeout=10)
            pids = [line.strip() for line in output.splitlines() if line.strip().isdigit()]
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            log_warning(f"Windows port query for port {port} failed: {e}")
            return
    else:
        try:
            result = subprocess.run(["lsof", "-tiTCP:{}".format(port)], capture_output=True, text=True, timeout=10)
            pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            log_warning(f"Unix port query for port {port} failed: {e}")
            return
    if not pids:
        return
    log_warning(f"Found {len(pids)} stale process(es) on port {port}")
    killed = 0
    for pid_str in pids:
        try:
            if system == "Windows":
                subprocess.check_output(["taskkill", "/F", "/PID", pid_str], stderr=subprocess.STDOUT, timeout=10)
                log_info(f"Terminated Windows PID {pid_str}")
            else:
                pid = int(pid_str)
                os.kill(pid, signal.SIGTERM)
                log_info(f"Signaled Unix PID {pid}")
            killed += 1
        except Exception as e:
            log_warning(f"Failed to terminate PID {pid_str}: {e}")
    if killed > 0:
        log_success(f"Terminated {killed} process(es)")


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
    for port in [
        DEFAULT_FRONTEND_PORT,
        DEFAULT_API_PORT,
        DEFAULT_YHATZEE_PORT,
        DEFAULT_SUPERQUIZ_PORT,
        DEFAULT_SHOOTY_PORT,
        DEFAULT_POKERTOOL_PORT,
    ]:
        if is_port_in_use(port):
            log_warning(f"Port {port} is in use")
            kill_processes_on_port(port)
            cleaned = True

    if cleaned:
        log_success("Cleaned up existing instances")
        time.sleep(0.5)  # Give processes time to terminate
    else:
        log_success("No existing instances found")


def start_api_server(port: int, project_root: Path, host: str = "127.0.0.1") -> threading.Thread:
    """Launch the API server in a background thread. Enforces singleton - only one instance can exist."""
    global _API_SERVER_INSTANCE

    with _API_SERVER_LOCK:
        if _API_SERVER_INSTANCE is not None and _API_SERVER_INSTANCE.is_alive():
            log_warning("API server already running - refusing to start duplicate instance")
            return _API_SERVER_INSTANCE

        log_info(f"Starting API server on {host}:{port}...")

        def run_server():
            try:
                from actifix.api import create_app
                app = create_app(project_root, host=host, port=port)
                log_success(f"API server initialized on http://{host}:{port}")
                # Use werkzeug's run_simple for better control
                from werkzeug.serving import run_simple
                run_simple(
                    host,
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


def start_yhatzee_server(port: int, project_root: Path, host: str = "127.0.0.1") -> threading.Thread:
    """Launch the Yhatzee GUI server in a background thread."""
    global _YHATZEE_SERVER_INSTANCE

    with _YHATZEE_SERVER_LOCK:
        if _YHATZEE_SERVER_INSTANCE is not None and _YHATZEE_SERVER_INSTANCE.is_alive():
            log_warning("Yhatzee server already running - refusing to start duplicate instance")
            return _YHATZEE_SERVER_INSTANCE

        log_info(f"Starting Yhatzee GUI server on {host}:{port}...")

        try:
            from actifix.modules.yhatzee import run_gui
        except ImportError as exc:
            log_error("Yhatzee module requires Flask/Flask-CORS (install via pip install -e '.[web]')")
            raise exc

        def run_server():
            try:
                run_gui(host=host, port=port, project_root=project_root, debug=False)
            except Exception as exc:
                log_error(f"Yhatzee GUI server error: {exc}")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    _YHATZEE_SERVER_INSTANCE = thread
    time.sleep(0.3)
    log_success(f"Yhatzee GUI server running at http://{host}:{port}")
    return thread


def _wait_for_superquiz_health(host: str, port: int, timeout: float = 5.0) -> bool:
    """Probe the SuperQuiz health endpoint to ensure the GUI started cleanly."""
    from urllib.request import urlopen

    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def start_superquiz_server(port: int, project_root: Path, host: str = "127.0.0.1") -> threading.Thread:
    """Launch the SuperQuiz GUI server and verify its dependencies."""
    global _SUPERQUIZ_SERVER_INSTANCE

    with _SUPERQUIZ_SERVER_LOCK:
        if _SUPERQUIZ_SERVER_INSTANCE is not None and _SUPERQUIZ_SERVER_INSTANCE.is_alive():
            log_warning("SuperQuiz server already running - refusing to start duplicate instance")
            return _SUPERQUIZ_SERVER_INSTANCE

        log_info(f"Starting SuperQuiz GUI server on {host}:{port}...")

        try:
            from actifix.modules.superquiz import run_gui
        except ImportError as exc:
            log_error("SuperQuiz module requires Flask (install via pip install -e '.[web]')")
            raise exc

        def run_server():
            try:
                run_gui(host=host, port=port, project_root=project_root, debug=False)
            except Exception as exc:
                log_error(f"SuperQuiz GUI server error: {exc}")

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        _SUPERQUIZ_SERVER_INSTANCE = thread
        time.sleep(0.3)

        if not _wait_for_superquiz_health(host, port):
            message = "SuperQuiz GUI failed to respond on /health (check Flask/dependencies)"
            log_error(message)
            raise RuntimeError(message)

        log_success(f"SuperQuiz GUI server running at http://{host}:{port}")
        log_info("SuperQuiz health endpoint responded; dependencies validated")
        return thread


def start_shooty_server(port: int, project_root: Path, host: str = "127.0.0.1") -> threading.Thread:
    """Launch the ShootyMcShoot GUI server in a background thread."""
    global _SHOOTY_SERVER_INSTANCE

    with _SHOOTY_SERVER_LOCK:
        if _SHOOTY_SERVER_INSTANCE is not None and _SHOOTY_SERVER_INSTANCE.is_alive():
            log_warning("ShootyMcShoot server already running - refusing to start duplicate instance")
            return _SHOOTY_SERVER_INSTANCE

        log_info(f"Starting ShootyMcShoot GUI server on {host}:{port}...")

        try:
            from actifix.modules.shootymcshoot import run_gui
        except ImportError as exc:
            log_error("ShootyMcShoot module requires Flask/Flask-CORS (install via pip install -e '.[web]')")
            raise exc

        def run_server():
            try:
                run_gui(host=host, port=port, project_root=project_root, debug=False)
            except Exception as exc:
                log_error(f"ShootyMcShoot GUI server error: {exc}")

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        _SHOOTY_SERVER_INSTANCE = thread
        time.sleep(0.3)
        log_success(f"ShootyMcShoot GUI server running at http://{host}:{port}")
        return thread


def start_pokertool_service(port: int, project_root: Path, host: str = "127.0.0.1") -> threading.Thread:
    """Launch the PokerTool service in a background thread."""
    global _POKERTOOL_THREAD

    with _POKERTOOL_LOCK:
        if _POKERTOOL_THREAD is not None and _POKERTOOL_THREAD.is_alive():
            log_warning("PokerTool service already running - refusing to start duplicate instance")
            return _POKERTOOL_THREAD

        log_info(f"Starting PokerTool service on {host}:{port}...")

        try:
            from actifix.modules.pokertool import run_service
        except ImportError as exc:
            log_error("PokerTool module requires Flask/Flask-CORS (install via pip install -e '.[web]')")
            raise exc

        def run_service_thread() -> None:
            try:
                run_service(host=host, port=port, project_root=project_root, debug=False)
            except Exception as exc:
                log_error(f"PokerTool service error: {exc}")

        thread = threading.Thread(target=run_service_thread, daemon=True)
        thread.start()
        _POKERTOOL_THREAD = thread
        time.sleep(0.3)
        log_success(f"PokerTool service running at http://{host}:{port}")
        return thread


def start_api_watchdog(api_port: int, project_root: Path, interval_seconds: float = 30.0, stop_event: Optional[threading.Event] = None) -> threading.Thread:

    """API watchdog: monitor port and auto-restart if down."""
    def watchdog_loop():
        while True:
            if stop_event and stop_event.is_set():
                break
            if not is_port_in_use(api_port):
                log_warning(f"API port {api_port} down - restarting...")
                try:
                    start_api_server(api_port, project_root)
                except Exception as e:
                    log_error(f"Watchdog restart failed: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=watchdog_loop, daemon=True)
    thread.start()
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
    """Ensure the served frontend stays in sync with pyproject version."""

    def _read_index_asset_version(frontend_dir: Path) -> Optional[str]:
        index_path = frontend_dir / "index.html"
        if not index_path.exists():
            return None
        try:
            text = index_path.read_text(encoding="utf-8")
        except OSError:
            return None
        match = re.search(r'window\\.ACTIFIX_ASSET_VERSION\\s*=\\s*["\\\']([^"\\\']+)["\\\']', text)
        return match.group(1).strip() if match else None

    def _read_app_ui_version(frontend_dir: Path) -> Optional[str]:
        app_path = frontend_dir / "app.js"
        if not app_path.exists():
            return None
        try:
            text = app_path.read_text(encoding="utf-8")
        except OSError:
            return None
        match = re.search(r"const\\s+UI_VERSION\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"]", text)
        return match.group(1).strip() if match else None

    def monitor_loop() -> None:
        last_version = read_project_version(project_root)
        frontend_root = FRONTEND_DIR
        served_frontend = frontend_root / "dist" if (frontend_root / "dist").exists() else frontend_root
        while True:
            if stop_event and stop_event.is_set():
                break
            time.sleep(interval_seconds)
            current_version = read_project_version(project_root)
            index_version = _read_index_asset_version(served_frontend)
            ui_version = _read_app_ui_version(served_frontend)

            mismatch = False
            if current_version and index_version and current_version != index_version:
                mismatch = True
            if current_version and ui_version and current_version != ui_version:
                mismatch = True

            if current_version != last_version or mismatch:
                log_info(
                    "Frontend version sync triggered: "
                    f"pyproject={current_version or 'unknown'} "
                    f"index={index_version or 'unknown'} "
                    f"ui={ui_version or 'unknown'}"
                )
                try:
                    build_frontend(project_root)
                except Exception as exc:
                    log_warning(f"Frontend rebuild failed during sync monitor: {exc}")

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
        "--yhatzee-port",
        type=int,
        default=DEFAULT_YHATZEE_PORT,
        help=f"Port for the standalone Yhatzee GUI (default: {DEFAULT_YHATZEE_PORT})",
    )
    parser.add_argument(
        "--no-yhatzee",
        action="store_true",
        help="Do not start the standalone Yhatzee GUI",
    )
    parser.add_argument(
        "--superquiz-port",
        type=int,
        default=DEFAULT_SUPERQUIZ_PORT,
        help=f"Port for the standalone SuperQuiz GUI (default: {DEFAULT_SUPERQUIZ_PORT})",
    )
    parser.add_argument(
        "--no-superquiz",
        action="store_true",
        help="Do not start the standalone SuperQuiz GUI",
    )
    parser.add_argument(
        "--shooty-port",
        type=int,
        default=DEFAULT_SHOOTY_PORT,
        help=f"Port for the standalone ShootyMcShoot GUI (default: {DEFAULT_SHOOTY_PORT})",
    )
    parser.add_argument(
        "--no-shooty",
        action="store_true",
        help="Do not start the standalone ShootyMcShoot GUI",
    )
    parser.add_argument(
        "--pokertool-port",
        type=int,
        default=DEFAULT_POKERTOOL_PORT,
        help=f"Port for the standalone PokerTool service (default: {DEFAULT_POKERTOOL_PORT})",
    )
    parser.add_argument(
        "--no-pokertool",
        action="store_true",
        help="Do not start the standalone PokerTool service",
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
    parser.add_argument(
        "--run-duration",
        type=float,
        metavar="SECONDS",
        help="Automatically stop after running for SECONDS (automation-friendly)",
        default=None,
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        help="Start servers and exit immediately (detached mode for automation)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point with beautiful color-coded output."""
    args = parse_args(argv)

    if args.run_duration is not None and args.run_duration <= 0:
        log_error("--run-duration must be greater than zero")
        return 1

    # Print startup banner
    print_banner("ACTIFIX STARTUP")

    # Step 0: Cleanup existing instances first
    cleanup_existing_instances()

    total_steps = 3
    if not args.no_api:
        total_steps += 1
    if not args.no_yhatzee:
        total_steps += 1
    if not args.no_superquiz:
        total_steps += 1
    if not args.no_shooty:
        total_steps += 1
    if not args.no_pokertool:
        total_steps += 1
    total_steps += 1  # frontend step

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

    if not args.no_yhatzee and is_port_in_use(args.yhatzee_port):
        log_warning(f"Yhatzee port {args.yhatzee_port} still in use, forcing cleanup")
        kill_processes_on_port(args.yhatzee_port)
        time.sleep(0.5)

        if is_port_in_use(args.yhatzee_port):
            log_error(f"Could not free Yhatzee port {args.yhatzee_port}")
            log_error("Try manually: pkill -f 'start.py' or use --yhatzee-port <PORT>")
            return 1

    if not args.no_superquiz and is_port_in_use(args.superquiz_port):
        log_warning(f"SuperQuiz port {args.superquiz_port} still in use, forcing cleanup")
        kill_processes_on_port(args.superquiz_port)
        time.sleep(0.5)

        if is_port_in_use(args.superquiz_port):
            log_error(f"Could not free SuperQuiz port {args.superquiz_port}")
            log_error("Try manually: pkill -f 'start.py' or use --superquiz-port <PORT>")
            return 1

    if not args.no_pokertool and is_port_in_use(args.pokertool_port):
        log_warning(f"PokerTool port {args.pokertool_port} still in use, forcing cleanup")
        kill_processes_on_port(args.pokertool_port)
        time.sleep(0.5)

        if is_port_in_use(args.pokertool_port):
            log_error(f"Could not free PokerTool port {args.pokertool_port}")
            log_error("Try manually: pkill -f 'start.py' or use --pokertool-port <PORT>")
            return 1

    # Step 4: Start API server (if enabled)
    api_thread = None
    api_watchdog_thread = None
    version_monitor_thread: Optional[threading.Thread] = None
    yhatzee_thread: Optional[threading.Thread] = None
    superquiz_thread: Optional[threading.Thread] = None
    pokertool_thread: Optional[threading.Thread] = None
    stop_event = threading.Event()
    if not args.no_api:
        current_step += 1
        log_step(current_step, total_steps, "Starting API server")
        try:
            api_thread = start_api_server(args.api_port, ROOT)
            api_watchdog_thread = start_api_watchdog(args.api_port, ROOT, stop_event=stop_event)
            log_success("API server + watchdog started")
        except Exception as e:
            log_error(f"Failed to start API server: {e}")
            return 1

    # Step 5: Start Yhatzee GUI
    if not args.no_yhatzee:
        current_step += 1
        log_step(current_step, total_steps, "Starting Yhatzee GUI")
        try:
            yhatzee_thread = start_yhatzee_server(args.yhatzee_port, ROOT)
        except Exception as e:
            log_error(f"Failed to start Yhatzee GUI: {e}")
            return 1

    if not args.no_superquiz:
        current_step += 1
        log_step(current_step, total_steps, "Starting SuperQuiz GUI")
        try:
            superquiz_thread = start_superquiz_server(args.superquiz_port, ROOT)
        except Exception as e:
            log_error(f"Failed to start SuperQuiz GUI: {e}")
            return 1

    if not args.no_pokertool:
        current_step += 1
        log_step(current_step, total_steps, "Starting PokerTool service")
        try:
            pokertool_thread = start_pokertool_service(args.pokertool_port, ROOT)
        except Exception as e:
            log_error(f"Failed to start PokerTool service: {e}")
            return 1

    # Start frontend server
    current_step += 1
    log_step(current_step, total_steps, "Starting frontend server")
    try:
        frontend_manager = FrontendManager(args.frontend_port)
        frontend_manager.start()
        version_monitor_thread = start_version_monitor(frontend_manager, ROOT, stop_event=stop_event)
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
    if not args.no_yhatzee:
        yhatzee_url = f"http://localhost:{args.yhatzee_port}/"
        print(f"{Color.BOLD}{Color.GREEN}Yhatzee:{Color.RESET}   {Color.CYAN}{yhatzee_url}{Color.RESET}")
    if not args.no_superquiz:
        superquiz_url = f"http://localhost:{args.superquiz_port}/"
        print(f"{Color.BOLD}{Color.GREEN}SuperQuiz:{Color.RESET} {Color.CYAN}{superquiz_url}{Color.RESET}")

    if not args.no_shooty:
        shooty_url = f"http://localhost:{args.shooty_port}/"
        print(f"{Color.BOLD}{Color.GREEN}ShootyMcShoot:{Color.RESET} {Color.CYAN}{shooty_url}{Color.RESET}")

    if not args.no_pokertool:
        pokertool_url = f"http://localhost:{args.pokertool_port}/"
        print(f"{Color.BOLD}{Color.GREEN}PokerTool:{Color.RESET} {Color.CYAN}{pokertool_url}{Color.RESET}")

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
    
    # Handle detached mode - exit immediately after starting servers
    if args.detach:
        log_success("All servers started in detached mode")
        log_info("Servers will continue running in background")
        log_info("Use 'pkill -f start.py' or kill processes on ports to stop")
        return 0
    
    print(f"{Color.YELLOW}Press Ctrl+C to stop all servers{Color.RESET}")
    print()

    run_until = None
    if args.run_duration is not None:
        run_until = time.monotonic() + args.run_duration
        log_info(f"Run duration set to {args.run_duration}s - launcher will stop automatically")

    exit_code = 0
    try:
        while True:
            time.sleep(1.0)
            current_server = frontend_manager.get_process()
            if current_server and current_server.poll() is not None:
                log_error("Frontend server stopped unexpectedly")
                exit_code = current_server.returncode or 1
                break
            if run_until and time.monotonic() >= run_until:
                log_info("Run duration reached - shutting down gracefully")
                break
    except KeyboardInterrupt:
        print()
        log_info("Shutdown signal received...")
    finally:
        stop_event.set()
        log_info("Stopping servers...")
        current_server = frontend_manager.get_process()
        if current_server:
            current_server.terminate()
            try:
                current_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current_server.kill()
        if api_watchdog_thread:
            api_watchdog_thread.join(timeout=1)
        if version_monitor_thread:
            version_monitor_thread.join(timeout=1)
        log_success("All servers stopped")
        log_success("Goodbye!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
