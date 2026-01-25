#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timezone
import uuid
from pathlib import Path

import pytest

import actifix.api as api
import actifix.log_utils as log_utils
import actifix.persistence.atomic as atomic_module
import actifix.do_af as do_af
from actifix.config import set_config, reset_config, load_config
from actifix.persistence.paths import (
    StoragePaths,
    configure_storage_paths,
    get_storage_paths,
    set_storage_paths,
    reset_storage_paths,
)
from actifix.persistence.storage import (
    FileStorageBackend,
    MemoryStorageBackend,
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
    JSONStorageMixin,
)
from actifix.persistence.ticket_repo import get_ticket_repository

pytestmark = [pytest.mark.integration]
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.testing import (
    TestRunner,
    assert_equals,
    assert_true,
    assert_false,
    assert_raises,
    assert_contains,
)
from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files
from actifix.log_utils import atomic_write, atomic_write_bytes


def _seed_ticket(
    ticket_id: str,
    priority: TicketPriority = TicketPriority.P2,
    completed: bool = False,
    created_at=None,
) -> ActifixEntry:
    repo = get_ticket_repository()
    entry = ActifixEntry(
        message="DoAF path helper",
        source="test/test_coverage_boost3.py",
        run_label="coverage",
        entry_id=ticket_id,
        created_at=created_at or datetime.now(timezone.utc),
        priority=priority,
        error_type="TestError",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-{uuid.uuid4().hex}",
    )
    repo.create_ticket(entry)
    if completed:
        repo.mark_complete(
            ticket_id,
            completion_notes=(
                "Implementation: Coverage boost test ticket completed via seed.\n"
                "Files:\n"
                "- src/actifix/do_af.py"
            ),
            test_steps="Ran coverage boost test suite",
            test_results="All coverage boost tests passed successfully"
        )
    return entry


def test_storage_paths_optional_dirs(tmp_path, monkeypatch):
    paths = StoragePaths(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        state_dir=tmp_path / ".state",
        logs_dir=None,
        cache_dir=None,
        temp_dir=None,
        backup_dir=None,
    )

    with pytest.raises(ValueError):
        paths.get_log_path("log.txt")
    with pytest.raises(ValueError):
        paths.get_cache_path("cache.txt")
    with pytest.raises(ValueError):
        paths.get_temp_path("temp.txt")
    with pytest.raises(ValueError):
        paths.get_backup_path("backup.txt")

    monkeypatch.setenv("STORAGE_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("STORAGE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("STORAGE_TEMP_DIR", str(tmp_path / "tmp"))
    monkeypatch.setenv("STORAGE_BACKUP_DIR", str(tmp_path / "backup"))

    configured = configure_storage_paths(project_root=tmp_path)
    assert configured.logs_dir is not None
    assert configured.cache_dir is not None
    assert configured.temp_dir is not None
    assert configured.backup_dir is not None

    reset_storage_paths()
    set_storage_paths(configured)
    assert get_storage_paths().logs_dir == configured.logs_dir


def test_test_runner_failure_and_assert_helpers(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    runner = TestRunner("failure", paths=paths)
    runner.add_test("fail", lambda: assert_false(True))
    runner.add_test("error", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    statuses = []

    def progress(index, total, test_case, status):
        statuses.append(status)

    runner.set_progress_callback(progress)
    runner.declare_plan()
    result = runner.execute()
    assert result.failed == 1
    assert result.errors == 1
    assert statuses

    empty_runner = TestRunner("empty", paths=paths)
    assert empty_runner.format_report() == "No test results available."

    with pytest.raises(AssertionError):
        assert_equals(1, 2)
    with pytest.raises(AssertionError):
        assert_true(False)
    with pytest.raises(AssertionError):
        assert_false(True)

    assert_raises(ValueError, lambda: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(AssertionError):
        assert_contains(["a"], "b")


def test_log_utils_cleanup_errors(tmp_path, monkeypatch):
    target = tmp_path / "cleanup.txt"

    def raise_replace(*_args, **_kwargs):
        raise OSError("boom")

    def raise_unlink(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(log_utils.os, "replace", raise_replace)
    monkeypatch.setattr(log_utils.os, "unlink", raise_unlink)
    with pytest.raises(OSError):
        atomic_write(target, "data")

    monkeypatch.setattr(log_utils.os, "replace", raise_replace)
    monkeypatch.setattr(log_utils.os, "unlink", raise_unlink)
    with pytest.raises(OSError):
        atomic_write_bytes(target, b"data")


def test_atomic_cleanup_errors(tmp_path, monkeypatch):
    target = tmp_path / "atomic.txt"

    def raise_replace(*_args, **_kwargs):
        raise OSError("boom")

    def raise_unlink(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(atomic_module.os, "replace", raise_replace)
    monkeypatch.setattr(atomic_module.os, "unlink", raise_unlink)
    with pytest.raises(OSError):
        atomic_module.atomic_write(target, "data")

    monkeypatch.setattr(atomic_module.os, "replace", raise_replace)
    monkeypatch.setattr(atomic_module.os, "unlink", raise_unlink)
    with pytest.raises(OSError):
        atomic_module.atomic_write_bytes(target, b"data")


def test_storage_backend_additional_errors(tmp_path, monkeypatch):
    base_dir = tmp_path / "files"
    backend = FileStorageBackend(base_dir)
    path = base_dir / "data.txt"
    atomic_write(path, "data")

    def raise_read(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(Path, "read_text", raise_read, raising=False)
    with pytest.raises(StorageError):
        backend.read("data.txt")

    def raise_bytes(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(Path, "read_bytes", raise_bytes, raising=False)
    with pytest.raises(StorageError):
        backend.read_bytes("data.txt")

    def raise_write_bytes(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("actifix.persistence.storage.atomic_write_bytes", raise_write_bytes)
    with pytest.raises(StorageError):
        backend.write_bytes("data.txt", b"data")

    def raise_unlink(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(Path, "unlink", raise_unlink, raising=False)
    with pytest.raises(StorageError):
        backend.delete("data.txt")

    mem = MemoryStorageBackend()
    with pytest.raises(StorageNotFoundError):
        mem.read_bytes("missing")
    assert mem.delete("missing") is False

    class JsonBackend(JSONStorageMixin, MemoryStorageBackend):
        pass

    json_backend = JsonBackend()
    json_backend.write_json("data", {"a": 1})
    assert json_backend.read_json("data") == {"a": 1}


def test_do_af_paths_none_and_mark_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    entry = _seed_ticket("ACT-20260111-ABCD1", TicketPriority.P1)

    monkeypatch.setattr(do_af, "get_actifix_paths", lambda *args, **kwargs: paths)

    open_tickets = do_af.get_open_tickets(paths=None, use_cache=False)
    assert any(ticket.ticket_id == entry.entry_id for ticket in open_tickets)

    ticket = do_af.process_next_ticket(paths=None)
    assert ticket is not None

    processed = do_af.process_tickets(max_tickets=1, paths=None)
    assert len(processed) == 1

    assert do_af.get_completed_tickets(paths=None, use_cache=False) == []
    stats = do_af.get_ticket_stats(paths=None, use_cache=False)
    assert stats["total"] == 1

    def fail_mark(*_args, **_kwargs):
        return False

    monkeypatch.setattr(do_af, "mark_ticket_complete", fail_mark)
    result = do_af.fix_highest_priority_ticket(paths=paths)
    assert result["processed"] is False


def test_api_event_level_and_no_flask(monkeypatch):
    assert api._map_event_type_to_level("ACTION_DECIDED", "go") == "ACTION"
    assert api._map_event_type_to_level("THOUGHT_PROCESS", "think") == "THOUGHT"
    assert api._map_event_type_to_level("TESTING", "run") == "TEST"
    assert api._map_event_type_to_level("TICKET_CLOSED", "done") == "SUCCESS"

    # Mock _ensure_web_dependencies to return False (simulating failed install)
    monkeypatch.setattr(api, "_ensure_web_dependencies", lambda: False)
    with pytest.raises(ImportError):
        api.create_app()


def test_config_set_and_reset(tmp_path):
    config = load_config(project_root=tmp_path, fail_fast=False)
    set_config(config)
    reset_config()

from actifix.persistence.queue import PersistenceQueue, QueueEntry
from datetime import datetime, timezone
import json


def test_persistence_queue_edge_cases(tmp_path):
    queue_file = tmp_path / "queue.json"
    atomic_write(queue_file, "{bad json")
    queue = PersistenceQueue(queue_file)
    assert queue.is_empty()

    queue = PersistenceQueue(queue_file, max_entries=1, deduplication=True)
    entry_id = queue.enqueue("write", "key", "one")
    updated_id = queue.enqueue("write", "key", "two")
    assert entry_id == updated_id
    assert queue.size() == 1

    queue.enqueue("write", "key2", "three")
    assert queue.size() == 1

    assert queue.dequeue("missing") is None

    entry = QueueEntry(
        entry_id="QE-FAIL",
        operation="write",
        key="fail",
        content="x",
        created_at=datetime.now(timezone.utc),
    )
    entry_error = QueueEntry(
        entry_id="QE-ERR",
        operation="write",
        key="err",
        content="x",
        created_at=datetime.now(timezone.utc),
    )
    queue._entries = [entry, entry_error]

    def handler(entry):
        if entry.entry_id == "QE-ERR":
            raise RuntimeError("boom")
        return False

    stats = queue.replay(handler, max_retries=1)
    assert stats["failed"] == 2

    assert queue.clear() >= 0

    empty = PersistenceQueue(tmp_path / "empty.json")
    assert empty.get_stats()["size"] == 0
