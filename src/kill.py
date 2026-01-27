"""Helper to terminate lingering Actifix services."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
from dataclasses import dataclass
from typing import Iterable, Sequence


SEARCH_KEYWORDS = (
    "actifix",
    "do_af.py",
    "start.py",
    "yahtzee",
    "api.py",
    "yfinance",
)
EXCLUDE_KEYWORDS = ("kill.py", "build_frontend.py", "ps -eo")


@dataclass(frozen=True)
class ProcessEntry:
    pid: int
    command: str


def _fetch_ps_output() -> str:
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,args"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout or ""
    except Exception:
        return ""


def _parse_ps_output(raw_output: str) -> Iterable[ProcessEntry]:
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 1)
        if not parts:
            continue
        pid_str = parts[0]
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        command = parts[1] if len(parts) > 1 else ""
        yield ProcessEntry(pid=pid, command=command)


def identify_targets(ps_output: str | None = None) -> list[ProcessEntry]:
    """Return Actifix-related processes that should be terminated."""
    raw = ps_output if ps_output is not None else _fetch_ps_output()
    targets: list[ProcessEntry] = []
    lower_keywords = tuple(key.lower() for key in SEARCH_KEYWORDS)
    lower_excludes = tuple(key.lower() for key in EXCLUDE_KEYWORDS)

    for entry in _parse_ps_output(raw):
        if entry.pid == os.getpid():
            continue
        command_lower = entry.command.lower()
        if not any(keyword in command_lower for keyword in lower_keywords):
            continue
        if any(excluded in command_lower for excluded in lower_excludes):
            continue
        targets.append(entry)
    return targets


def kill_processes(
    entries: Sequence[ProcessEntry],
    *,
    dry_run: bool = False,
    signal_type: signal.Signals = signal.SIGTERM,
) -> tuple[list[ProcessEntry], list[tuple[ProcessEntry, Exception]]]:
    """Terminate the provided processes and classify results."""
    succeeded: list[ProcessEntry] = []
    failed: list[tuple[ProcessEntry, Exception]] = []

    for entry in entries:
        if dry_run:
            succeeded.append(entry)
            continue
        try:
            os.kill(entry.pid, signal_type)
            succeeded.append(entry)
        except Exception as exc:
            failed.append((entry, exc))

    return succeeded, failed


def _render_report(
    entries: Sequence[ProcessEntry],
    succeeded: Sequence[ProcessEntry],
    failed: Sequence[tuple[ProcessEntry, Exception]],
    dry_run: bool,
) -> None:
    total = len(entries)
    print(f"Actifix service cleanup report ({total} candidate(s)):")
    if dry_run:
        print("Dry-run mode: no signals were sent.")

    for entry in succeeded:
        print(f"  ✓ {entry.pid}: {entry.command}")

    for entry, exc in failed:
        print(f"  ✗ {entry.pid}: {entry.command}")
        print(f"    reason: {exc}")

    if not succeeded and not failed:
        print("No Actifix-related processes detected.")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint that kills active Actifix services."""
    parser = argparse.ArgumentParser(description="Terminate Actifix-related services.")
    parser.add_argument("--dry-run", action="store_true", help="Report targets without sending signals.")
    args = parser.parse_args(argv)

    entries = identify_targets()
    if not entries:
        print("No Actifix-related processes found.")
        return 0

    succeeded, failed = kill_processes(entries, dry_run=args.dry_run)
    _render_report(entries, succeeded, failed, args.dry_run)

    if failed:
        print(f"{len(failed)} process(es) could not be terminated.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
