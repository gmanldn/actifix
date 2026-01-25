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
import platform
from pathlib import Path

# Environment variable required by Actifix change gate
os.environ['ACTIFIX_CHANGE_ORIGIN'] = 'raise_af'


def _find_pids(pattern):
    """
    Return a list of PIDs whose command line matches the given pattern.
    """
    system = platform.system()
    if system in ('Linux', 'Darwin'):
        try:
            output = subprocess.check_output(['pgrep', '-f', pattern])
            return [int(line.strip()) for line in output.decode('ascii').splitlines() if line.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
    elif system == 'Windows':
        try:
            ps_cmd = f'Get-WmiObject Win32_Process | Where-Object {{ $_.CommandLine -match "{pattern}" }} | Select-Object -ExpandProperty ProcessId'
            output = subprocess.check_output(['powershell.exe', '-Command', ps_cmd], text=True)
            return [int(pid.strip()) for pid in output.splitlines() if pid.strip().isdigit()]
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return []
    else:
        return []


def _kill_pids(pids):
    """
    Cross-platform kill of processes by PID.
    """
    system = platform.system()
    for pid in pids:
        try:
            if system == "Windows":
                subprocess.check_output(["taskkill", "/F", "/PID", str(pid)], stderr=subprocess.STDOUT)
            else:
                os.kill(pid, signal.SIGTERM)
        except (subprocess.CalledProcessError, OSError, ProcessLookupError):
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

    # Synchronize frontend version with project version
    print("Synchronizing frontend version...")
    python = sys.executable or 'python3'
    root = Path(__file__).resolve().parents[1]
    build_frontend_script = root / "scripts" / "build_frontend.py"
    
    try:
        result = subprocess.run(
            [python, str(build_frontend_script)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Warning: Frontend version synchronization failed: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)

    # Relaunch Actifix via start.py
    print("Restarting Actifix backend via scripts/start.py...")
    start_script = root / "scripts" / "start.py"
    subprocess.Popen([python, str(start_script)])
    print(" → Actifix restart initiated.")


if __name__ == "__main__":
    main()
