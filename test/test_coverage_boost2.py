#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import actifix.api as api
import actifix.log_utils as log_utils
import actifix.persistence.atomic as atomic_module
from actifix.config import ActifixConfig, load_config, validate_config
from actifix.do_af import (
    get_completed_tickets,
    get_ticket_stats,
    process_tickets,
    main as do_af_main,
    _acquire_file_lock,
    _try_lock,
)
from actifix.health import (
    ActifixHealthCheck,
    _get_ticket_age_hours,
    check_sla_breaches,
    format_health_report,
    run_health_check,
)
from actifix.log_utils import atomic_write, atomic_write_bytes, append_with_guard
from actifix.persistence.atomic import atomic_write as atomic_core_write
from actifix.persistence.atomic import atomic_write_bytes as atomic_core_write_bytes
from actifix.persistence.atomic import trim_to_line_boundary
from actifix.persistence.manager import PersistenceManager, PersistenceError
from actifix.persistence.queue import PersistenceQueue
from actifix.persistence.storage import (
    FileStorageBackend,
    MemoryStorageBackend,
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
)
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.simple_ticket_attack import (
    _build_messages,
    _normalize_priority,
    attack_simple_tickets,
    main as simple_ticket_main,
)
from actifix.state_paths import get_actifix_paths, init_actifix_files
from actifix.raise_af import ActifixEntry, TicketPriority


def _seed_ticket(
    ticket_id: str,
    priority: TicketPriority = TicketPriority.P2,
    completed: bool = False,
    created_at: datetime | None = None,
) -> ActifixEntry:
    repo = get_ticket_repository()
    entry = ActifixEntry(
        message="Coverage helper",
        source="test/test_coverage_boost2.py",
        run_label="coverage",
        entry_id=ticket_id,
        created_at=created_at or datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        duplicate_guard=f"{ticket_id}-{uuid.uuid4().hex}",
    )
    repo.create_ticket(entry)
    if completed:
        repo.mark_complete(
            ticket_id,
            completion_notes="Coverage boost 2 test ticket completed via seed",
            test_steps="Ran coverage boost 2 test suite",
            test_results="All coverage boost 2 tests passed"
        )
    return entry


def test_api_helpers_and_parse_branches(tmp_path, monkeypatch):
    modules = api._load_modules(tmp_path)
    assert modules == {"system": [], "user": []}

    def raise_read(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_text", raise_read, raising=False)
    modules = api._load_modules(tmp_path)
    assert modules == {"system": [], "user": []}

    assert api._run_git_command(["git", "not-a-command"], tmp_path) is None

    assert api._map_event_type_to_level("", "✓ ok") == "SUCCESS"
    assert api._map_event_type_to_level("", "✗ bad") == "ERROR"
    assert api._map_event_type_to_level("", "⚠ warn") == "WARNING"
    assert api._map_event_type_to_level("ASCII_BANNER", "ok") == "BANNER"

    assert api._parse_log_line("") is None
    parsed = api._parse_log_line("2024-01-01 | EVENT | ACT-1 | hello | extra")
    assert parsed["event"] == "EVENT"

    parsed = api._parse_log_line("✓ done")
    assert parsed["level"] == "SUCCESS"

    parsed = api._parse_log_line("WARN: message")
    assert parsed["event"] == "WARN"


def test_api_endpoints_fix_ticket_and_logs(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    repo = get_ticket_repository()
    entry = ActifixEntry(
        message="API log fix required",
        source="test/test_coverage_boost2.py:api",
        run_label="api",
        entry_id="ACT-20260111-ABCD1",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P1,
        error_type="TestError",
        stack_trace="",
        duplicate_guard="api-guard",
    )
    repo.create_ticket(entry)

    app = api.create_app(tmp_path)
    client = app.test_client()

    response = client.post("/api/fix-ticket")
    data = response.get_json()
    assert data["processed"] is True

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    setup_log = logs_dir / "setup.log"
    atomic_write(setup_log, "setup ok\n")

    response = client.get("/api/logs?type=setup")
    assert response.status_code == 200

    def raise_read(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_text", raise_read, raising=False)
    response = client.get("/api/logs?type=list")
    payload = response.get_json()
    assert payload.get("content") is not None


def test_api_system_handles_psutil_exception(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    class FakePsutil:
        def virtual_memory(self):
            raise RuntimeError("boom")

        def cpu_percent(self, interval=0.1):
            raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "psutil", FakePsutil())

    app = api.create_app(tmp_path)
    client = app.test_client()
    response = client.get("/api/system")
    assert response.status_code == 200


def test_api_run_server_uses_create_app(monkeypatch):
    called = {}

    class DummyApp:
        def run(self, host, port, debug, threaded):
            called["host"] = host
            called["port"] = port
            called["debug"] = debug
            called["threaded"] = threaded

    monkeypatch.setattr(api, "create_app", lambda *_args, **_kwargs: DummyApp())
    api.run_api_server(host="127.0.0.1", port=5050, debug=True)
    assert called["port"] == 5050


def test_config_validation_and_fail_fast(tmp_path, monkeypatch):
    project_root = tmp_path / "missing"
    paths = get_actifix_paths(project_root=project_root)

    config = ActifixConfig(
        project_root=project_root,
        paths=paths,
        sla_p0_hours=0,
        sla_p1_hours=0,
        sla_p2_hours=0,
        sla_p3_hours=0,
        min_coverage_percent=101,
        max_log_size_bytes=0,
        max_list_entries=0,
        test_timeout_seconds=0,
        dispatch_timeout_seconds=0,
    )
    errors = validate_config(config)
    assert any("Project root" in err for err in errors)
    assert any("SLA P0" in err for err in errors)

    monkeypatch.setenv("ACTIFIX_SLA_P0_HOURS", "0")
    with pytest.raises(ValueError):
        load_config(project_root=tmp_path, fail_fast=True)


def test_health_helpers_and_report(tmp_path, capsys):
    assert _get_ticket_age_hours("not-a-date") == 0
    _get_ticket_age_hours(datetime.now().isoformat())

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    _seed_ticket("ACT-20260111-BEAC1", TicketPriority.P0, created_at=datetime.fromisoformat(old_time))

    breaches = check_sla_breaches(paths)
    assert breaches

    report = format_health_report(
        ActifixHealthCheck(
            healthy=False,
            status="ERROR",
            timestamp=datetime.now(timezone.utc),
            warnings=["warn"],
            errors=["err"],
        )
    )
    assert "Warnings" in report
    assert "Errors" in report

    run_health_check(paths, print_report=True)
    captured = capsys.readouterr().out
    assert "ACTIFIX HEALTH CHECK REPORT" in captured


def test_log_utils_error_paths(tmp_path, monkeypatch):
    target = tmp_path / "log.txt"
    original_replace = log_utils.os.replace

    def raise_replace(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(log_utils.os, "replace", raise_replace)
    with pytest.raises(OSError):
        atomic_write(target, "data")

    monkeypatch.setattr(log_utils.os, "replace", raise_replace)
    with pytest.raises(OSError):
        atomic_write_bytes(target, b"data")

    monkeypatch.setattr(log_utils.os, "replace", original_replace)
    append_with_guard(target, "alpha", max_size_bytes=3)
    assert target.read_text() == "pha"


def test_atomic_core_error_paths(tmp_path, monkeypatch):
    target = tmp_path / "core.txt"
    original_open = atomic_module.os.open

    def selective_open(path, flags, *args):
        if flags == atomic_module.os.O_RDONLY:
            raise OSError("boom")
        return original_open(path, flags, *args)

    monkeypatch.setattr(atomic_module.os, "open", selective_open)
    atomic_core_write(target, "ok")
    assert target.exists()

    def raise_replace(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr("actifix.persistence.atomic.os.replace", raise_replace)
    with pytest.raises(OSError):
        atomic_core_write_bytes(target, b"bytes")

    assert trim_to_line_boundary("short", max_bytes=10) == "short"
    assert trim_to_line_boundary("nosplit", max_bytes=3) == "nos"


def test_persistence_manager_additional_paths(tmp_path):
    backend = MemoryStorageBackend()
    queue_file = tmp_path / "queue.json"
    queue = PersistenceQueue(queue_file)
    queue.enqueue("write", "doc.txt", "value")
    queue.enqueue("append", "doc.txt", "++")
    queue.enqueue("delete", "doc.txt", "")

    manager = PersistenceManager(backend, queue_file=queue_file, enable_queue=True, auto_replay=True)
    assert manager.queue is not None

    assert manager.update_document("new.txt", lambda value: value + "x", create_if_missing=True) is None

    class DeleteFailBackend(MemoryStorageBackend):
        def delete(self, key: str) -> bool:
            raise StorageError("fail")

    failing = PersistenceManager(DeleteFailBackend(), enable_queue=False)
    with pytest.raises(PersistenceError):
        failing.delete_document("missing")

    assert PersistenceManager(MemoryStorageBackend(), enable_queue=False).get_queue_stats() is None
    assert PersistenceManager(MemoryStorageBackend(), enable_queue=False).clear_queue() == 0

    with pytest.raises(PersistenceError):
        PersistenceManager(MemoryStorageBackend(), enable_queue=False).get_size("missing")


def test_persistence_manager_append_queue(tmp_path):
    class AppendFailBackend(MemoryStorageBackend):
        def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
            raise StorageError("fail")

    backend = AppendFailBackend()
    manager = PersistenceManager(backend, queue_file=tmp_path / "queue.json", enable_queue=True, auto_replay=False)
    appended = manager.append_to_document("log.txt", "data", use_queue_on_failure=True)
    assert appended is False


def test_storage_backend_error_branches(tmp_path, monkeypatch):
    base_dir = tmp_path / "storage"
    backend = FileStorageBackend(base_dir)

    path = base_dir / "data.txt"
    atomic_write(path, "data")

    def raise_permission(*_args, **_kwargs):
        raise PermissionError("no")

    monkeypatch.setattr(Path, "read_bytes", raise_permission, raising=False)
    with pytest.raises(StoragePermissionError):
        backend.read_bytes("data.txt")

    def raise_generic(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("actifix.persistence.storage.atomic_write", raise_generic)
    with pytest.raises(StorageError):
        backend.write("data.txt", "data")

    monkeypatch.setattr(Path, "unlink", raise_permission, raising=False)
    with pytest.raises(StoragePermissionError):
        backend.delete("data.txt")

    with pytest.raises(StorageNotFoundError):
        backend.size("missing.txt")

    mem = MemoryStorageBackend()
    mem.write_bytes("bin", b"data")
    assert mem.read_bytes("bin") == b"data"
    assert mem.list_keys(prefix="b") == ["bin"]
    mem.clear()
    assert mem.list_keys() == []


def test_do_af_fallback_stats_and_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    _seed_ticket("ACT-20260111-ABCD1", TicketPriority.P2)
    _seed_ticket("ACT-20260111-FFFF1", TicketPriority.P2, completed=True)

    completed = get_completed_tickets(paths=paths, use_cache=False)
    assert completed

    stats = get_ticket_stats(paths=paths, use_cache=False)
    assert stats["completed"] >= 1

    processed = process_tickets(max_tickets=1, ai_handler=lambda _ticket: True, paths=paths)
    assert processed

    monkeypatch.setattr("actifix.do_af.process_tickets", lambda *args, **kwargs: [])
    result = do_af_main(["--project-root", str(tmp_path), "process", "--max-tickets", "1"])
    assert result == 0


def test_do_af_lock_helpers(monkeypatch):
    calls = {"count": 0}

    def flaky_try_lock(_lock_file):
        calls["count"] += 1
        if calls["count"] == 1:
            raise BlockingIOError("blocked")
        return True

    monkeypatch.setattr("actifix.do_af._try_lock", flaky_try_lock)

    with open(__file__, "r") as lock_file:
        _acquire_file_lock(lock_file, timeout=0.1)

    monkeypatch.setattr("actifix.do_af._has_fcntl", lambda: False)
    monkeypatch.setattr("actifix.do_af._has_msvcrt", lambda: False)
    with open(__file__, "r") as lock_file:
        assert _try_lock(lock_file) is True


def test_simple_ticket_attack_non_dry_run(monkeypatch, capsys):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    class DummyContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return None

    class DummyEntry:
        ticket_id = "ACT-TEST"

    monkeypatch.setattr("actifix.simple_ticket_attack.ActifixContext", DummyContext)
    monkeypatch.setattr("actifix.simple_ticket_attack.record_error", lambda **_kwargs: DummyEntry())

    results = attack_simple_tickets(count=1, dry_run=False, priority=TicketPriority.P1)
    assert results[0].ticket_id == "ACT-TEST"

    assert _normalize_priority(TicketPriority.P2) == TicketPriority.P2
    assert _build_messages(0, 1, ["one"]) == []

    monkeypatch.setattr(
        "actifix.simple_ticket_attack.attack_simple_tickets",
        lambda **_kwargs: [type("R", (), {"created": True, "ticket_id": "ONE"})()],
    )
    simple_ticket_main(["--count", "1"])
    captured = capsys.readouterr().out
    assert "Created" in captured
