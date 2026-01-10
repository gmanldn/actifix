#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from actifix.persistence.manager import PersistenceManager, PersistenceError
from actifix.persistence.storage import MemoryStorageBackend, StorageError
from actifix.persistence.paths import StoragePaths


class FailingOnceBackend(MemoryStorageBackend):
    """Backend that fails the first write to trigger queueing logic."""

    def __init__(self):
        super().__init__()
        self._fail_next = True

    def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
        if self._fail_next:
            self._fail_next = False
            raise StorageError("simulated failure")
        return super().write(key, content, encoding=encoding)


def build_paths(tmp_path: Path) -> StoragePaths:
    """Helper to create isolated storage paths for tests."""
    return StoragePaths(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        state_dir=tmp_path / ".state",
    )


def test_persistence_manager_read_write_cycle(tmp_path: Path):
    paths = build_paths(tmp_path)
    backend = MemoryStorageBackend()
    manager = PersistenceManager(backend, paths=paths, queue_file=paths.get_state_path("queue.json"))

    assert manager.write_document("doc.txt", "hello") is True
    assert manager.read_document("doc.txt") == "hello"
    assert manager.exists("doc.txt") is True
    assert manager.list_documents() == ["doc.txt"]
    assert manager.get_size("doc.txt") == len("hello".encode("utf-8"))

    with manager.transaction() as txn:
        txn.write("doc2.txt", "txn")
        txn.commit()
    assert manager.read_document("doc2.txt") == "txn"


def test_queue_on_failure_and_replay(tmp_path: Path):
    paths = build_paths(tmp_path)
    backend = FailingOnceBackend()
    queue_file = paths.get_state_path("persistence_queue.json")
    manager = PersistenceManager(
        backend,
        paths=paths,
        queue_file=queue_file,
        enable_queue=True,
        auto_replay=False,
    )

    # First write queues due to simulated failure
    wrote = manager.write_document("queued.txt", "queued-content", use_queue_on_failure=True)
    assert wrote is False
    assert queue_file.exists()

    # Swap backend to healthy and replay
    manager.backend = MemoryStorageBackend()
    replay_result = manager.replay_queue()
    assert replay_result["succeeded"] == 1
    assert manager.read_document("queued.txt") == "queued-content"
    assert manager.queue.is_empty() is True  # type: ignore[attr-defined]
