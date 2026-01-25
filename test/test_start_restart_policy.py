"""Tests for start.py restart/cleanup behavior."""

from __future__ import annotations

import os


def test_cleanup_existing_instances_kills_all_in_use_ports(monkeypatch):
    from scripts import start

    killed: list[int] = []
    monkeypatch.setattr(start, "is_port_in_use", lambda _p: True)
    monkeypatch.setattr(start, "kill_processes_on_port", lambda p: killed.append(int(p)))
    # Avoid touching the real process table.
    monkeypatch.setattr(start.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 1, "stdout": ""})())

    start.cleanup_existing_instances()
    for port in [
        start.DEFAULT_FRONTEND_PORT,
        start.DEFAULT_API_PORT,
        start.DEFAULT_YHATZEE_PORT,
        start.DEFAULT_SUPERQUIZ_PORT,
        start.DEFAULT_SHOOTY_PORT,
        start.DEFAULT_POKERTOOL_PORT,
    ]:
        assert port in killed


def test_restart_process_for_new_version_execs(monkeypatch, tmp_path):
    from scripts import start

    called = {"execv": False}

    def fake_execv(_exe, _argv):
        called["execv"] = True
        raise SystemExit(0)

    monkeypatch.setattr(start.os, "execv", fake_execv)
    monkeypatch.setattr(start, "build_frontend", lambda *_: None)
    monkeypatch.setattr(start, "kill_processes_on_port", lambda *_: None)
    monkeypatch.setenv(start.ENV_FRONTEND_PORT, "1111")

    try:
        start.restart_process_for_new_version(tmp_path, reason="test", ports=[1111])
    except SystemExit:
        pass

    assert called["execv"] is True

