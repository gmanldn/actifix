#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

import pytest

from actifix.do_af import (
    get_open_tickets,
    mark_ticket_complete,
    fix_highest_priority_ticket,
    process_next_ticket,
    StatefulTicketManager,
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
from actifix.raise_af import TicketPriority


def _write_list(paths, content: str) -> None:
    atomic_write(paths.list_file, content)


def _basic_ticket_block(ticket_id: str, priority: str, message: str, status: str = "Open") -> str:
    return "\n".join(
        [
            f"### {ticket_id} - [{priority}] Error: {message}",
            f"- **Priority**: {priority}",
            "- **Error Type**: Error",
            "- **Source**: `tests.py:1`",
            "- **Run**: test-run",
            "- **Created**: 2026-01-11T00:00:00+00:00",
            "- **Duplicate Guard**: `ACTIFIX-test-guard`",
            f"- **Status**: {status}",
            "- **Owner**: None",
            "- **Branch**: None",
            "- **Lease Expires**: None",
            "",
            "**Checklist:**",
            "- [ ] Documented",
            "- [ ] Functioning",
            "- [ ] Tested",
            "- [ ] Completed",
            "",
        ]
    )


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


def test_stateful_ticket_manager_refreshes_and_replaces_completed(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    completed_id = "ACT-20260111-BBBBB"

    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            _basic_ticket_block(completed_id, "P2", "Open item"),
            "## Completed Items",
            _basic_ticket_block(completed_id, "P1", "Done item", status="Completed").replace(
                "- [ ] Completed", "- [x] Completed"
            ),
        ]
    )
    _write_list(paths, content)

    manager = StatefulTicketManager(paths=paths, cache_ttl=0)
    stats = manager.get_stats()
    assert stats["total"] == 1
    assert stats["completed"] == 1
    manager.invalidate_cache()


def test_get_open_tickets_uncached_parses_active_section(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-CCCC1"
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            _basic_ticket_block(ticket_id, "P0", "Priority item"),
            "## Completed Items",
        ]
    )
    _write_list(paths, content)

    tickets = get_open_tickets(paths=paths, use_cache=False)
    assert len(tickets) == 1
    assert tickets[0].ticket_id == ticket_id


def test_mark_ticket_complete_moves_and_updates_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-DDDD1"
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            _basic_ticket_block(ticket_id, "P2", "Needs fix"),
            "## Completed Items",
        ]
    )
    _write_list(paths, content)

    assert mark_ticket_complete(ticket_id, summary="Closed", paths=paths) is True
    updated = paths.list_file.read_text()
    assert "## Completed Items" in updated
    assert "- Summary: Closed" in updated


def test_mark_ticket_complete_updates_existing_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-EEEE1"
    block = _basic_ticket_block(ticket_id, "P3", "Summary change") + "- Summary: Old\n"
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            block,
            "## Completed Items",
        ]
    )
    _write_list(paths, content)

    assert mark_ticket_complete(ticket_id, summary="New summary", paths=paths) is True
    updated = paths.list_file.read_text()
    assert "- Summary: New summary" in updated


def test_mark_ticket_complete_idempotent_guard(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    ticket_id = "ACT-20260111-FFFF1"
    completed_block = _basic_ticket_block(ticket_id, "P2", "Already done", status="Completed").replace(
        "- [ ] Completed", "- [x] Completed"
    )
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            completed_block,
            "## Completed Items",
        ]
    )
    _write_list(paths, content)

    assert mark_ticket_complete(ticket_id, summary="Ignored", paths=paths) is False


def test_fix_highest_priority_ticket_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    empty_content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            "## Completed Items",
        ]
    )
    _write_list(paths, empty_content)

    result = fix_highest_priority_ticket(paths=paths)
    assert result["processed"] is False

    ticket_id = "ACT-20260111-ABCD1"
    content = "\n".join(
        [
            "# Actifix Ticket List",
            "## Active Items",
            _basic_ticket_block(ticket_id, "P1", "Needs attention"),
            "## Completed Items",
        ]
    )
    _write_list(paths, content)

    result = fix_highest_priority_ticket(paths=paths, summary="Handled")
    assert result["processed"] is True
    assert result["ticket_id"] == ticket_id


def test_process_next_ticket_no_tickets(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    _write_list(
        paths,
        "\n".join(
            [
                "# Actifix Ticket List",
                "## Active Items",
                "## Completed Items",
            ]
        ),
    )

    assert process_next_ticket(paths=paths) is None


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
