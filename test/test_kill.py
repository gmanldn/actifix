"""Tests for the Actifix kill helper."""

from pathlib import Path

import pytest

import kill


def test_kill_symlink_exists():
    root = Path(__file__).resolve().parent.parent
    symlink = root / "kill.py"
    assert symlink.is_symlink()
    assert symlink.resolve() == (root / "src" / "kill.py").resolve()


def test_identify_targets_filters_commands():
    data = """\
PID CMD
 100 python /usr/bin/python3 src/actifix/api.py
 101 python /usr/bin/ssh
"""
    targets = kill.identify_targets(data)
    assert targets == [kill.ProcessEntry(100, "python /usr/bin/python3 src/actifix/api.py")]


def test_kill_processes_dry_run(monkeypatch):
    entry = kill.ProcessEntry(201, "python ./src/actifix/main.py")
    calls = []

    def _fake_kill(pid, sig):
        calls.append(pid)

    monkeypatch.setattr(kill.os, "kill", _fake_kill)

    succeeded, failed = kill.kill_processes([entry], dry_run=True)

    assert succeeded == [entry]
    assert failed == []
    assert not calls


def test_kill_processes_handles_failure(monkeypatch):
    entry = kill.ProcessEntry(202, "python ./Do_AF.py")

    def _fail(pid, sig):
        raise PermissionError("denied")

    monkeypatch.setattr(kill.os, "kill", _fail)

    succeeded, failed = kill.kill_processes([entry], dry_run=False)

    assert succeeded == []
    assert len(failed) == 1
    assert isinstance(failed[0][1], PermissionError)


def test_main_reports_dry_run(monkeypatch, capsys):
    entry = kill.ProcessEntry(300, "python start.py")
    monkeypatch.setattr(kill, "identify_targets", lambda: [entry])
    calls = []

    def _fake_kill(pid, sig):
        calls.append(pid)

    monkeypatch.setattr(kill.os, "kill", _fake_kill)

    result = kill.main(["--dry-run"])
    captured = capsys.readouterr()

    assert "Dry-run mode" in captured.out
    assert "300" in captured.out
    assert calls == []
    assert result == 0
