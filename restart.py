#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actifix Restart Helper
----------------------

Stops any Actifix static frontend running on the given port (default 8080)
and optionally relaunches via start.py.
"""

from __future__ import annotations

import argparse
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8080


def log(message: str) -> None:
    print(f"[Actifix:restart] {message}")


def find_pids_on_port(port: int) -> List[int]:
    """Return PIDs bound to the given TCP port."""
    if platform.system() == "Windows":
        # netstat parsing for Windows
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            pids: List[int] = []
            for line in result.stdout.splitlines():
                if f":{port} " in line and "LISTEN" in line.upper():
                    parts = line.split()
                    if parts:
                        try:
                            pids.append(int(parts[-1]))
                        except ValueError:
                            pass
            return pids
        except Exception:
            return []
    else:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return [int(pid) for pid in result.stdout.split() if pid.strip()]
        except Exception:
            return []


def terminate_pids(pids: Iterable[int]) -> int:
    """Best-effort terminate PIDs. Returns count killed."""
    count = 0
    for pid in set(pids):
        try:
            os.kill(pid, signal.SIGTERM)
            count += 1
        except ProcessLookupError:
            continue
        except PermissionError:
            continue
    # Give processes a moment to exit
    time.sleep(1.0)
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restart Actifix web UI")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to stop/start (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--kill-only",
        action="store_true",
        help="Only stop running servers; do not relaunch start.py",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pids = find_pids_on_port(args.port)

    if pids:
        log(f"Stopping {len(pids)} process(es) on port {args.port}...")
        killed = terminate_pids(pids)
        log(f"Terminated {killed} process(es)")
    else:
        log(f"No processes found on port {args.port}")

    if args.kill_only:
        return 0

    log("Relaunching start.py...")
    cmd = [sys.executable, str(ROOT / "start.py"), "--frontend-port", str(args.port)]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
