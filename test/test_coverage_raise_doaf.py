"""
Coverage tests for raise_af and do_af modules.
"""

from __future__ import annotations

import runpy
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import actifix.do_af as do_af
import actifix.raise_af as raise_af
from actifix.do_af import TicketInfo
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


def _seed_ticket(
    ticket_id: str,
    priority: TicketPriority = TicketPriority.P2,
    completed: bool = False,
    summary: str | None = None,
) -> ActifixEntry:
    repo = get_ticket_repository()
    entry = ActifixEntry(
        message="Seeded test ticket",
        source="test/test_coverage_raise_doaf.py:seed",
        run_label="raise-af",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-{uuid.uuid4().hex}",
    )
    repo.create_ticket(entry)
    if completed:
        repo.mark_complete(
            ticket_id,
            completion_notes="Test ticket completed in seed helper function",
            test_steps="Seeded with test harness",
            test_results="All test seeds passed successfully",
            summary=summary
        )
    return entry


def test_ticket_manager_cache_and_parse(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    do_af._global_manager = None

    _seed_ticket("ACT-20250101-AAAAA", TicketPriority.P1)
    _seed_ticket("ACT-20250101-BBBBB", TicketPriority.P0)
    _seed_ticket("ACT-20250101-CCCCC", TicketPriority.P2, completed=True)
    _seed_ticket("ACT-20250101-DDDDD", TicketPriority.P3, completed=True)

    manager = do_af.StatefulTicketManager(paths=paths, cache_ttl=60)
    open_tickets = manager.get_open_tickets()
    completed_tickets = manager.get_completed_tickets()
    stats = manager.get_stats()

    assert len(open_tickets) >= 2
    assert len(completed_tickets) >= 2
    assert stats["open"] >= 2
    manager.invalidate_cache()
    assert len(manager.get_open_tickets()) >= 2


def test_get_tickets_fallbacks(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    do_af._global_manager = None

    assert do_af.get_open_tickets(paths, use_cache=False) == []
    assert do_af.get_completed_tickets(paths, use_cache=False) == []
    stats = do_af.get_ticket_stats(paths, use_cache=False)
    assert stats["total"] == 0


def test_mark_ticket_complete_and_idempotent(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    do_af._global_manager = None

    ticket_id = "ACT-20250102-AAAAA"
    _seed_ticket(ticket_id, completed=True)
    # Try to complete already-completed ticket (should return False)
    assert do_af.mark_ticket_complete(
        ticket_id,
        completion_notes="Dummy notes for idempotency test",
        test_steps="Dummy test steps",
        test_results="Dummy test results",
        paths=paths
    ) is False
    assert "TICKET_ALREADY_COMPLETED" in paths.aflog_file.read_text()

    ticket_id = "ACT-20250102-BBBBB"
    repo = get_ticket_repository()
    _seed_ticket(ticket_id)

    assert do_af.mark_ticket_complete(
        ticket_id,
        completion_notes="Fixed critical bug in ticket completion workflow",
        test_steps="Ran full test suite for ticket completion",
        test_results="All 450+ tests passed with 95% coverage",
        summary="New summary",
        paths=paths
    ) is True
    stored = repo.get_ticket(ticket_id)
    assert stored["completion_summary"] == "New summary"


def test_process_next_ticket_handlers(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    do_af._global_manager = None

    ticket_id = "ACT-20250103-AAAAA"
    _seed_ticket(ticket_id, TicketPriority.P0)
    _seed_ticket("ACT-20250103-BBBBB", TicketPriority.P1)

    def handler(ticket: TicketInfo) -> bool:
        return ticket.ticket_id == ticket_id

    ticket = do_af.process_next_ticket(handler, paths=paths)
    assert ticket is not None
    assert "TICKET_COMPLETED" in paths.aflog_file.read_text()

    def fail_handler(_ticket: TicketInfo) -> bool:
        raise RuntimeError("boom")

    ticket = do_af.process_next_ticket(fail_handler, paths=paths)
    assert ticket is not None
    assert "DISPATCH_FAILED" in paths.aflog_file.read_text()


def test_ticket_lock_behaviors(tmp_path, monkeypatch):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    with do_af._ticket_lock(paths, enabled=False):
        assert True

    original_try_lock = do_af._try_lock
    monkeypatch.setattr(do_af, "_try_lock", lambda _lock: False)
    monkeypatch.setattr(do_af.time, "sleep", lambda _x: None)

    calls = {"count": 0}

    def fake_monotonic():
        calls["count"] += 1
        return calls["count"] * 0.1

    monkeypatch.setattr(do_af.time, "monotonic", fake_monotonic)
    with pytest.raises(TimeoutError):
        with do_af._ticket_lock(paths, timeout=0.15):
            pass

    lock_file = (paths.state_dir / "dummy.lock").open("w")
    monkeypatch.setattr(do_af, "_has_fcntl", lambda: False)
    monkeypatch.setattr(do_af, "_has_msvcrt", lambda: False)
    monkeypatch.setattr(do_af, "_try_lock", original_try_lock)
    assert do_af._try_lock(lock_file) is True
    lock_file.close()


def test_doaf_cli_commands(tmp_path, capsys):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    do_af._global_manager = None

    args = do_af._build_cli_parser().parse_args(["--project-root", str(tmp_path), "stats"])
    resolved = do_af._resolve_paths_from_args(args)

    assert do_af.main(["--project-root", str(tmp_path), "stats"]) == 0
    out = capsys.readouterr().out
    assert "Total Tickets" in out

    assert do_af.main(["--project-root", str(tmp_path), "list"]) == 0
    out = capsys.readouterr().out
    assert "No open tickets" in out

    assert do_af.main(["--project-root", str(tmp_path), "process"]) == 0
    out = capsys.readouterr().out
    assert "No open tickets to process" in out

    _seed_ticket("ACT-20250104-AAAAA", TicketPriority.P0)
    _seed_ticket("ACT-20250104-BBBBB", TicketPriority.P2)

    assert do_af.main(["--project-root", str(tmp_path), "list", "--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert "more not shown" in out

    with pytest.raises(SystemExit):
        do_af.main(["--project-root", str(tmp_path), "process", "--max-tickets", "0"])


def test_raise_af_capture_disabled(monkeypatch):
    monkeypatch.delenv("ACTIFIX_CAPTURE_ENABLED", raising=False)
    raise_af._capture_disabled_log_count = raise_af._capture_disabled_log_max - 1

    assert raise_af.record_error("msg", "source") is None
    assert raise_af.record_error("msg", "source") is None
    assert raise_af._capture_disabled_log_count == raise_af._capture_disabled_log_max


def test_raise_af_capture_disabled_logging_error(monkeypatch):
    class FaultyLogger:
        def debug(self, _msg: str) -> None:
            raise RuntimeError("logger failed")

    fake_logging = SimpleNamespace(getLogger=lambda _name: FaultyLogger())
    monkeypatch.setitem(sys.modules, "logging", fake_logging)
    raise_af._capture_disabled_log_count = 0

    raise_af._log_capture_disabled("source", "error")
    assert raise_af._capture_disabled_log_count == 1


def test_raise_af_correlation_id(monkeypatch):
    import threading

    threading.actifix_correlation_id = "thread-cid"
    assert raise_af._get_current_correlation_id() == "thread-cid"
    delattr(threading, "actifix_correlation_id")

    try:
        raise RuntimeError("boom")
    except Exception as exc:
        exc.correlation_id = "exc-cid"
        assert raise_af._get_current_correlation_id() == "exc-cid"


def test_raise_af_redaction_and_priority():
    assert raise_af.redact_secrets_from_text("") == ""
    assert raise_af.classify_priority("fatal", "boom", "src") == TicketPriority.P0
    assert raise_af.classify_priority("database", "boom", "src") == TicketPriority.P1
    assert raise_af.classify_priority("warning", "boom", "src") == TicketPriority.P3
    assert raise_af.classify_priority("format", "boom", "src") == TicketPriority.P4
    assert raise_af.classify_priority("other", "boom", "src") == TicketPriority.P2


def test_raise_af_ai_notes_truncation(monkeypatch):
    entry = ActifixEntry(
        message="msg",
        source="src",
        run_label="run",
        entry_id="ACT-TEST",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P2,
        error_type="error",
        stack_trace="x" * 500,
    )
    monkeypatch.setattr(raise_af, "MAX_CONTEXT_CHARS", 50)
    notes = raise_af.generate_ai_remediation_notes(entry)
    assert "truncated" in notes


def test_raise_af_file_context_and_system_state(tmp_path, monkeypatch):
    file_path = tmp_path / "sample.py"
    file_path.write_text("line1\nline2\nline3\n")

    context = raise_af.capture_file_context(f"{file_path}:2")
    assert str(file_path) in context

    context = raise_af.capture_file_context(f"{file_path}:xx")
    assert str(file_path) in context

    monkeypatch.setattr(raise_af.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError()))
    state = raise_af.capture_system_state()
    assert "python_version" in state


def test_raise_af_duplicate_guards(tmp_path):
    from actifix.persistence.ticket_repo import get_ticket_repository

    repo = get_ticket_repository()
    entry = ActifixEntry(
        message="dup guard test",
        source="src",
        run_label="run",
        entry_id="ACT-TEST",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P2,
        error_type="error",
        duplicate_guard="ACTIFIX-test-1234",
    )
    repo.create_ticket(entry)
    assert repo.check_duplicate_guard("ACTIFIX-test-1234") is not None


def test_raise_af_recent_entries_and_fallback_queue(tmp_path, monkeypatch):
    base_dir = tmp_path / "actifix"
    base_dir.mkdir()
    recent_path = base_dir / "ACTIFIX.md"
    assert raise_af._read_recent_entries(recent_path) == []

    entry = ActifixEntry(
        message="msg",
        source="src",
        run_label="run",
        entry_id="ACT-TEST",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P2,
        error_type="error",
    )
    raise_af._append_recent(entry, base_dir)
    assert "ACT-TEST" in recent_path.read_text()

    queue_file = raise_af._get_fallback_queue_file(base_dir)
    assert queue_file.parent.exists()

    legacy_file = base_dir / raise_af.LEGACY_FALLBACK_QUEUE
    legacy_file.write_text("not-json")
    queue, source_path = raise_af._load_existing_queue(queue_file, legacy_file)
    assert queue == []
    assert source_path == queue_file

    def fail_persist(*_args, **_kwargs):
        raise RuntimeError("persist failed")

    monkeypatch.setattr(raise_af, "_persist_queue", fail_persist)
    assert raise_af._queue_to_fallback(entry, base_dir) is False


def test_raise_af_persist_queue_legacy_cleanup(tmp_path, monkeypatch):
    base_dir = tmp_path / "actifix"
    base_dir.mkdir()
    target = base_dir / "queue.json"
    legacy = base_dir / "legacy.json"
    legacy.write_text("[]")

    def fake_unlink(self, *args, **kwargs):
        if self == legacy:
            raise OSError("unlink failed")
        return Path.unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fake_unlink)
    raise_af._persist_queue([], target, legacy)
    assert legacy.exists()


def test_raise_af_replay_queue_paths(tmp_path, monkeypatch):
    base_dir = tmp_path / "actifix"
    base_dir.mkdir()

    sample_entry = (
        "[{\"message\": \"msg\", \"source\": \"src\", \"run_label\": \"run\", "
        "\"entry_id\": \"ACT-TEST\", \"created_at\": \"2024-01-01T00:00:00+00:00\", "
        "\"priority\": \"P2\", \"error_type\": \"error\", \"stack_trace\": \"\", "
        "\"duplicate_guard\": \"guard\"}]"
    )

    queue_file = raise_af._get_fallback_queue_file(base_dir)
    queue_file.unlink(missing_ok=True)
    legacy_file = base_dir / raise_af.LEGACY_FALLBACK_QUEUE
    legacy_file.write_text(sample_entry)

    assert raise_af.replay_fallback_queue(base_dir) == 1
    assert not legacy_file.exists()
    assert not queue_file.exists()

    queue_file.write_text(sample_entry)

    from actifix.persistence import ticket_repo
    original_repo = ticket_repo.get_ticket_repository

    class BoomRepo:
        def create_ticket(self, *_args, **_kwargs):
            raise RuntimeError("append failed")

        def check_duplicate_guard(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(ticket_repo, "get_ticket_repository", lambda: BoomRepo())
    replayed = raise_af.replay_fallback_queue(base_dir)
    assert replayed == 0
    assert queue_file.exists()

    monkeypatch.setattr(ticket_repo, "get_ticket_repository", original_repo)

    def bad_load(*_args, **_kwargs):
        raise RuntimeError("load failed")

    monkeypatch.setattr(raise_af, "_load_existing_queue", bad_load)
    assert raise_af.replay_fallback_queue(base_dir) == 0


def test_raise_af_record_error_duplicate_and_priority(tmp_path, monkeypatch):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "1")
    guard_value = "ACTIFIX-src-1234"
    monkeypatch.setattr(raise_af, "generate_duplicate_guard", lambda *_args, **_kwargs: guard_value)

    repo = get_ticket_repository()
    repo.create_ticket(
        ActifixEntry(
            message="Existing item",
            source="test",
            run_label="run",
            entry_id="ACT-20260111-INIT",
            created_at=datetime.now(timezone.utc),
            priority=TicketPriority.P2,
            error_type="TestError",
            duplicate_guard="ACTIFIX-src-1234",
        )
    )

    assert raise_af.record_error(
        "msg",
        "src",
        run_label="run",
        error_type="warning",
        paths=paths,
    ) is None

    monkeypatch.setattr(raise_af, "generate_duplicate_guard", lambda *_args, **_kwargs: "ACTIFIX-src-UNIQUE")
    entry = raise_af.record_error(
        "msg",
        "src",
        run_label="run",
        error_type="warning",
        priority="BAD",
        skip_duplicate_check=True,
        skip_ai_notes=True,
        paths=paths,
    )
    assert entry is not None
    assert entry.priority == TicketPriority.P3


def test_raise_af_cli_main(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "1")
    raise_af.main(
        [
            "--message",
            "msg",
            "--source",
            "src.py:1",
            "--run",
            "run",
            "--error-type",
            "error",
            "--no-context",
            "--base-dir",
            str(tmp_path / "actifix"),
        ]
    )
    out = capsys.readouterr().out
    assert "Recorded" in out


def test_raise_af_parse_args():
    args = raise_af.parse_args(
        ["--message", "msg", "--source", "src", "--run", "run", "--error-type", "err"]
    )
    assert args.message == "msg"


def test_bootstrap_main_exec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runpy.run_module("actifix.bootstrap", run_name="__main__")
