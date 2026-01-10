#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actifix Launcher
================

Lightweight starter for the generic Actifix system. It prepares the
Actifix scaffold, enables error capture, runs a quick health check, and
serves both the static web interface and API backend.

Usage:
    python start.py                     # init + health + start web UI + API
    python start.py --setup-only        # init only, no servers
    python start.py --health-only       # health check and exit
    python start.py --frontend-port 8081
    python start.py --api-port 5002
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
FRONTEND_DIR = ROOT / "actifix-frontend"
DEFAULT_FRONTEND_PORT = 8080
DEFAULT_API_PORT = 5001


def log(message: str) -> None:
    """Standard log prefix for launcher output."""
    print(f"[Actifix] {message}")


def clean_bytecode_cache() -> None:
    """Remove stale .pyc files to avoid version mismatches."""
    cleaned = 0
    for pyc in SRC_DIR.rglob("*.pyc"):
        try:
            pyc.unlink()
            cleaned += 1
        except OSError:
            pass
    if cleaned:
        log(f"Removed {cleaned} .pyc file(s)")


def ensure_scaffold() -> None:
    """Create Actifix directories and files if missing."""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    # Defer imports until path is set
    from actifix.state_paths import init_actifix_files
    from actifix.raise_af import ACTIFIX_CAPTURE_ENV_VAR

    os.environ.setdefault(ACTIFIX_CAPTURE_ENV_VAR, "1")
    init_actifix_files()


def is_port_in_use(port: int) -> bool:
    """Return True if a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_frontend(port: int) -> subprocess.Popen:
    """Launch the static frontend server."""
    cmd = [sys.executable, "-m", "http.server", str(port)]
    return subprocess.Popen(cmd, cwd=FRONTEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_api_server(port: int, project_root: Path) -> threading.Thread:
    """Launch the API server in a background thread."""
    def run_server():
        try:
            from actifix.api import create_app
            app = create_app(project_root)
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
            log(f"API server failed to start: {e}")
            log("Install Flask with: pip install flask flask-cors")
        except Exception as e:
            log(f"API server error: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread


def run_health_check() -> bool:
    """Run Actifix health check and return True if healthy."""
    from actifix.health import run_health_check
    result = run_health_check(print_report=True)
    return bool(getattr(result, "healthy", False))


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
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Do not start the API server",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    clean_bytecode_cache()
    ensure_scaffold()
    try:
        from actifix.dock_icon import setup_dock_icon
        setup_dock_icon()
    except Exception:
        # Dock icon setup is best-effort; ignore failures on non-macOS
        pass

    if args.health_only:
        healthy = run_health_check()
        return 0 if healthy else 1

    if args.setup_only:
        log("Initialization complete (setup-only mode).")
        return 0

    if not FRONTEND_DIR.exists():
        log(f"Frontend directory missing: {FRONTEND_DIR}")
        return 1

    if is_port_in_use(args.frontend_port):
        log(f"Port {args.frontend_port} is already in use. Stop the existing process or choose another port.")
        return 1

    if not args.no_api and is_port_in_use(args.api_port):
        log(f"API port {args.api_port} is already in use. Stop the existing process or choose another port.")
        return 1

    # Start API server first (in background thread)
    api_thread = None
    if not args.no_api:
        log(f"Starting Actifix API server on port {args.api_port}...")
        api_thread = start_api_server(args.api_port, ROOT)
        # Give the API server a moment to start
        time.sleep(0.5)
        log(f"API available at http://localhost:{args.api_port}/api/")

    log(f"Starting Actifix static frontend on port {args.frontend_port}...")
    server = start_frontend(args.frontend_port)
    url = f"http://localhost:{args.frontend_port}"
    log(f"Frontend available at {url}")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            log("Browser launch failed; open the URL manually.")

    log("")
    log("=" * 50)
    log("  ACTIFIX DASHBOARD")
    log("=" * 50)
    log(f"  Frontend: http://localhost:{args.frontend_port}")
    if not args.no_api:
        log(f"  API:      http://localhost:{args.api_port}/api/")
    log("")
    log("  Press Ctrl+C to stop")
    log("=" * 50)

    try:
        # Keep process alive until interrupted
        while True:
            time.sleep(1.0)
            if server.poll() is not None:
                return server.returncode or 0
    except KeyboardInterrupt:
        log("\nStopping servers...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log("Stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
