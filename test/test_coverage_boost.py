#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from pathlib import Path
import uuid

import pytest

from actifix.do_af import (
    get_open_tickets,
    mark_ticket_complete,
    fix_highest_priority_ticket,
    process_next_ticket,
    StatefulTicketManager,
    TicketInfo,
)
from actifix.log_utils import atomic_write
from actifix.persistence.atomic import (
    atomic_update,
    atomic_append,
    trim_to_line_boundary,
)
from actifix.persistence.manager import PersistenceManager, PersistenceError
from actifix.persistence.storage import (
    FileStorageBackend,
    MemoryStorageBackend,
    StorageBackend,
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
)
from actifix.simple_ticket_attack import (
    _build_messages,
    _normalize_priority,
    attack_simple_tickets,
    main as simple_ticket_main,
)
from actifix.state_paths import get_actifix_paths, init_actifix_files
from actifix.testing import TestRunner
from actifix.testing.system import build_system_tests
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.persistence.event_repo import get_event_repository, EventFilter
from actifix.raise_af import ActifixEntry, TicketPriority

pytestmark = [pytest.mark.integration]


def _create_ticket(ticket_id: str, priority: TicketPriority, message: str = "Test issue") -> ActifixEntry:
    repo = get_ticket_repository()
    entry = ActifixEntry(
        message=message,
        source="test/test_coverage_boost.py:helper",
        run_label="test-run",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-{uuid.uuid4().hex}",
    )
    repo.create_ticket(entry)
    return entry


def test_simple_ticket_attack_builds_messages_and_dry_run(monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    messages = _build_messages(2, 3, ["Alpha", "Beta"])
    assert messages[0][0] == 3
    assert messages[0][1].startswith("Simple ticket #3")

    resolved = _normalize_priority("P2")
    assert resolved == TicketPriority.P2
    fallback = _normalize_priority("nope")
    assert fallback == TicketPriority.P3

    results = attack_simple_tickets(count=2, priority="P1", start_index=5, dry_run=True)
    assert len(results) == 2
    assert results[0].created is False
    assert results[0].message.startswith("Simple ticket #5")


def test_simple_ticket_attack_main_dry_run(monkeypatch, capsys):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    assert simple_ticket_main(["--count", "1", "--dry-run"]) == 0
    captured = capsys.readouterr().out
    assert "Prepared" in captured


def test_stateful_ticket_manager_refreshes_and_replaces_completed(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-BBBBB"
    _create_ticket(ticket_id, TicketPriority.P2)
    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Closed", paths=paths)

    manager = StatefulTicketManager(paths=paths, cache_ttl=0)
    stats = manager.get_stats()
    assert stats["total"] == 1
    assert stats["completed"] == 1
    assert not manager.get_open_tickets()
    manager.invalidate_cache()


def test_get_open_tickets_uncached_reads_database(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-CCCC1"
    created_entry = _create_ticket(ticket_id, TicketPriority.P0)

    tickets = get_open_tickets(paths=paths, use_cache=False)
    assert any(ticket.ticket_id == created_entry.ticket_id for ticket in tickets)


def test_mark_ticket_complete_records_summary(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-DDDD1"
    created_entry = _create_ticket(ticket_id, TicketPriority.P2)

    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Closed", paths=paths)
    stored = get_ticket_repository().get_ticket(ticket_id)
    assert stored["status"] == "Completed"
    assert stored["completion_summary"] == "Closed"


def test_mark_ticket_complete_can_reapply_summary_after_reopen(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-EEEE1"
    _create_ticket(ticket_id, TicketPriority.P3)

    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="First summary", paths=paths)
    repo = get_ticket_repository()
    repo.update_ticket(ticket_id, {"status": "Open", "completed": 0})

    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Second summary", paths=paths)
    stored = repo.get_ticket(ticket_id)
    assert stored["completion_summary"] == "Second summary"


def test_mark_ticket_complete_idempotent_guard(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-FFFF1"
    _create_ticket(ticket_id, TicketPriority.P2)
    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="First pass", paths=paths)

    assert mark_ticket_complete(ticket_id, completion_notes="Fixed critical test ticket successfully validated", test_steps="Test validation", test_results="Test passed", summary="Ignored", paths=paths) is False
    repo = get_event_repository()
    events = repo.get_events(EventFilter(event_type="TICKET_ALREADY_COMPLETED", limit=10))
    assert any(event.get("event_type") == "TICKET_ALREADY_COMPLETED" for event in events)
    assert any("idempotency_guard" in (event.get("extra_json") or "") for event in events)


def test_fix_highest_priority_ticket_paths(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    result = fix_highest_priority_ticket(paths=paths)
    assert result["processed"] is False

    low_ticket = _create_ticket("ACT-20260111-ABCD1", TicketPriority.P1)
    high_ticket = _create_ticket("ACT-20260111-ABCD2", TicketPriority.P0)
    result = fix_highest_priority_ticket(
        paths=paths,
        completion_notes="Fixed highest priority ticket with validated changes",
        test_steps="Ran ticket completion path validation",
        test_results="Completion flow passed",
        summary="Handled",
    )
    assert result["processed"] is True
    assert result["ticket_id"] == high_ticket.ticket_id


def test_process_next_ticket_no_tickets(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    assert process_next_ticket(paths=paths, use_ai=False) is None


def test_process_next_ticket_with_handler(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    entry = _create_ticket("ACT-20260111-ZZZZ", TicketPriority.P3)

    def handler(info: TicketInfo) -> bool:
        assert info.ticket_id == entry.ticket_id
        return True

    ticket = process_next_ticket(ai_handler=handler, paths=paths, use_ai=False)
    assert ticket is not None
    stored = get_ticket_repository().get_ticket(entry.ticket_id)
    assert stored["status"] == "Completed"


class FailingStorageBackend(StorageBackend):
    def __init__(self):
        self._data = {}

    def read(self, key: str) -> str:
        raise StorageNotFoundError("missing")

    def read_bytes(self, key: str) -> bytes:
        raise StorageNotFoundError("missing")

    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        raise StorageError("write failed")

    def write_bytes(self, key: str, content: bytes) -> None:
        raise StorageError("write failed")

    def exists(self, key: str) -> bool:
        return False

    def delete(self, key: str) -> bool:
        raise StorageError("delete failed")

    def list_keys(self, prefix: str | None = None):
        raise StorageError("list failed")

    def size(self, key: str) -> int:
        raise StorageError("size failed")


def test_persistence_manager_queue_and_replay(tmp_path):
    backend = FailingStorageBackend()
    queue_file = tmp_path / "queue.json"
    manager = PersistenceManager(backend, queue_file=queue_file, enable_queue=True, auto_replay=False)

    queued = manager.write_document("doc.txt", "payload", use_queue_on_failure=True)
    assert queued is False
    assert manager.queue is not None
    assert manager.queue.size() == 1

    manager.backend = MemoryStorageBackend()
    stats = manager.replay_queue()
    assert stats["succeeded"] == 1


def test_persistence_manager_errors_and_updates(tmp_path):
    backend = MemoryStorageBackend()
    manager = PersistenceManager(backend, enable_queue=False)

    with pytest.raises(PersistenceError):
        manager.read_document("missing")

    with pytest.raises(PersistenceError):
        manager.update_document("missing", lambda value: value, create_if_missing=False)

    manager.append_to_document("log", "alpha\n", max_size_bytes=10)
    manager.append_to_document("log", "beta\n", max_size_bytes=10)
    assert manager.read_document("log").endswith("beta\n")


def test_persistence_transaction_commit_and_failure(tmp_path):
    backend = MemoryStorageBackend()
    manager = PersistenceManager(backend, enable_queue=False)

    with manager.transaction() as txn:
        txn.write("a.txt", "value")
        txn.commit()

    assert manager.read_document("a.txt") == "value"

    failing_manager = PersistenceManager(FailingStorageBackend(), enable_queue=False)
    with failing_manager.transaction() as txn:
        txn.write("b.txt", "value")
        with pytest.raises(PersistenceError):
            txn.commit()


def test_persistence_list_and_size_errors():
    manager = PersistenceManager(FailingStorageBackend(), enable_queue=False)

    with pytest.raises(PersistenceError):
        manager.list_documents()

    with pytest.raises(PersistenceError):
        manager.get_size("missing")


def test_storage_permission_and_listing_errors(tmp_path, monkeypatch):
    base_dir = tmp_path / "storage"
    backend = FileStorageBackend(base_dir)

    def raise_permission(*_args, **_kwargs):
        raise PermissionError("no")

    monkeypatch.setattr("actifix.persistence.storage.atomic_write", raise_permission)
    with pytest.raises(StoragePermissionError):
        backend.write("file.txt", "data")

    monkeypatch.setattr("actifix.persistence.storage.atomic_write_bytes", raise_permission)
    with pytest.raises(StoragePermissionError):
        backend.write_bytes("file.bin", b"data")

    path = base_dir / "exists.txt"
    atomic_write(path, "data")

    def raise_read(*_args, **_kwargs):
        raise PermissionError("no")

    monkeypatch.setattr(Path, "read_text", raise_read, raising=False)
    with pytest.raises(StoragePermissionError):
        backend.read("exists.txt")

    monkeypatch.setattr(Path, "rglob", lambda *_args, **_kwargs: (_ for _ in ()).throw(Exception("boom")))
    with pytest.raises(StorageError):
        backend.list_keys()

    monkeypatch.setattr(Path, "stat", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(StorageError):
        backend.size("exists.txt")


def test_atomic_helpers_and_system_tests(tmp_path):
    trimmed = trim_to_line_boundary("one\ntwo\n", max_bytes=5)
    assert trimmed.endswith("\n")

    log_path = tmp_path / "log.txt"
    atomic_append(log_path, "alpha\n", max_size_bytes=6)
    atomic_append(log_path, "beta\n", max_size_bytes=6)
    assert log_path.read_text().endswith("beta\n")

    atomic_update(log_path, lambda value: value + "gamma\n")
    assert "gamma" in log_path.read_text()

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    tests = build_system_tests(paths)
    for name, func, _desc, _tags in tests:
        func()


def test_test_runner_progress_callback(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    runner = TestRunner("progress", paths=paths)
    runner.add_test("ok", lambda: None)

    seen = []

    def legacy_progress(index, total, test_case):
        seen.append((index, total, test_case.name))

    runner.set_progress_callback(legacy_progress)
    runner.declare_plan()
    result = runner.execute()

    assert result.success is True
    assert seen
