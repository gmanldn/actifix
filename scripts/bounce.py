#!/usr/bin/env python3
"""
bounce.py

Stops any running Actifix backend or frontend processes, then restarts the
Actifix application via scripts/start.py, honoring the Raise_AF gate.
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

# Environment variable required by Actifix change gate
os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'


def _find_pids(pattern):
    """
    Return a list of PIDs whose command line matches the given pattern.
    """
    try:
        output = subprocess.check_output(['pgrep', '-f', pattern])
    except subprocess.CalledProcessError:
        return []
    return [int(p) for p in output.split()]


def _kill_pids(pids):
    """
    Send SIGTERM to each PID in the list.
    """
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def main():
    # Patterns to identify backend (start.py) and frontend (actifix-frontend) processes
    patterns = ['start\\.py', 'actifix-frontend']

    print("Stopping Actifix processes...")
    all_pids = []
    for pat in patterns:
        pids = _find_pids(pat)
        if pids:
            print(f" → Found {len(pids)} process(es) for pattern '{pat}': {pids}")
            all_pids.extend(pids)

    if all_pids:
        _kill_pids(all_pids)
        print(" → Processes terminated.")
    else:
        print(" → No running Actifix processes detected.")

    # Relaunch Actifix via start.py
    print("Restarting Actifix backend via scripts/start.py...")
    python = sys.executable or 'python3'
    root = Path(__file__).resolve().parents[1]
    start_script = root / "scripts" / "start.py"
    subprocess.Popen([python, str(start_script)])
    print(" → Actifix restart initiated.")


if __name__ == "__main__":
    main()
