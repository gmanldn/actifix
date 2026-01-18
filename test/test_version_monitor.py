import threading
from types import SimpleNamespace
from pathlib import Path

import pytest

from scripts import start

pytestmark = [pytest.mark.integration]


class DummyProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self._poll = None

    def poll(self):
        return self._poll

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


def test_frontend_manager_restart_invokes_start(monkeypatch):
    calls = []

    dummy_proc = DummyProcess()

    def fake_start_frontend(port):
        calls.append(port)
        return dummy_proc

    monkeypatch.setattr(start, "start_frontend", fake_start_frontend)

    manager = start.FrontendManager(port=8080)
    proc1 = manager.start()
    assert proc1 is dummy_proc
    assert calls == [8080]

    proc2 = manager.restart()
    assert proc2 is dummy_proc
    assert calls == [8080, 8080]
    assert dummy_proc.terminated is True


def test_read_project_version_parses_version(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('version = "9.9.9"\n', encoding="utf-8")

    version = start.read_project_version(tmp_path)
    assert version == "9.9.9"


def test_version_monitor_restarts_on_change(monkeypatch):
    versions = iter(["1.0.0", "1.0.0", "1.1.0", "1.1.0"])
    restart_count = SimpleNamespace(value=0)
    sleeps = SimpleNamespace(count=0)
    stop_event = threading.Event()

    def fake_read_version(_):
        return next(versions)

    def fake_sleep(_):
        sleeps.count += 1
        if sleeps.count >= 3:
            stop_event.set()

    class DummyManager:
        def restart(self):
            restart_count.value += 1

    monkeypatch.setattr(start, "read_project_version", fake_read_version)
    monkeypatch.setattr(start.time, "sleep", fake_sleep)

    manager = DummyManager()
    thread = start.start_version_monitor(manager, Path("."), interval_seconds=0.01, stop_event=stop_event)
    thread.join(timeout=1)

    assert restart_count.value >= 1


def test_version_monitor_no_restart_without_change(monkeypatch):
    versions = iter(["2.0.0"] * 4)
    restart_count = SimpleNamespace(value=0)
    sleeps = SimpleNamespace(count=0)
    stop_event = threading.Event()

    def fake_read_version(_):
        return next(versions)

    def fake_sleep(_):
        sleeps.count += 1
        if sleeps.count >= 3:
            stop_event.set()

    class DummyManager:
        def restart(self):
            restart_count.value += 1

    monkeypatch.setattr(start, "read_project_version", fake_read_version)
    monkeypatch.setattr(start.time, "sleep", fake_sleep)

    manager = DummyManager()
    thread = start.start_version_monitor(manager, Path("."), interval_seconds=0.01, stop_event=stop_event)
    thread.join(timeout=1)

    assert restart_count.value == 0
