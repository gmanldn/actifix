"""
Additional coverage tests for core modules with low coverage.
"""

import builtins
import importlib
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import actifix
import actifix.api as api
from actifix.api import create_app
from actifix.bootstrap import (
    ActifixContext,
    bootstrap,
    disable_actifix_capture,
    enable_actifix_capture,
    install_exception_handler,
    uninstall_exception_handler,
)
from actifix.health import (
    _parse_iso_datetime,
    _get_ticket_age_hours,
    check_sla_breaches,
    get_health,
)
from actifix.log_utils import atomic_write, append_with_guard
from actifix.persistence.manager import PersistenceManager, PersistenceError
from actifix.persistence.queue import PersistenceQueue, QueueError
from actifix.persistence.storage import (
    FileStorageBackend,
    MemoryStorageBackend,
    StorageError,
    StorageNotFoundError,
)
from actifix.persistence.paths import configure_storage_paths, reset_storage_paths
from actifix.testing import TestRunner, run_tests
from actifix.testing.system import build_system_tests
from actifix.state_paths import get_actifix_paths, init_actifix_files


def test_quick_start_output(capsys):
    actifix.quick_start()
    out = capsys.readouterr().out
    assert "Actifix Quick Start" in out
    assert "record_error" in out


def test_actifix_all_exports():
    assert "record_error" in actifix.__all__
    assert "generate_ticket_id" in actifix.__all__


def test_api_modules_parsing(tmp_path):
    modules_dir = tmp_path / "Arch"
    modules_dir.mkdir()
    modules_md = modules_dir / "MODULES.md"
    modules_md.write_text(
        "\n".join(
            [
                "## Core",
                "**Domain:** runtime",
                "**Owner:** core",
                "**Summary:** Core services",
                "",
                "## Feature",
                "**Domain:** app",
                "**Owner:** user",
                "**Summary:** User module",
            ]
        )
    )
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/modules")
        data = response.get_json()
        assert len(data["system"]) == 1
        assert len(data["user"]) == 1


def test_api_logs_missing_file(tmp_path):
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/logs?type=setup")
        data = response.get_json()
        assert data.get("error") == "Log file not found"


def test_api_logs_invalid_type(tmp_path):
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/logs?type=unknown")
        data = response.get_json()
        assert data.get("error") == "Log file not found"


def test_api_system_with_psutil(tmp_path, monkeypatch):
    fake_psutil = SimpleNamespace(
        virtual_memory=lambda: SimpleNamespace(total=1024**3, used=512 * 1024**2, percent=50),
        cpu_percent=lambda interval=0.1: 12.5,
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/system")
        data = response.get_json()
        assert data["resources"]["memory"] is not None
        assert data["resources"]["cpu_percent"] == 12.5


def test_api_system_without_psutil(tmp_path, monkeypatch):
    """Test that system endpoint falls back to defaults when psutil is missing."""
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("psutil missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/system")
        assert response.status_code == 200
        data = response.get_json()
        resources = data["resources"]
        assert resources["cpu_percent"] == 0.0
        memory = resources["memory"]
        assert memory["percent"] == 0.0
        assert memory["used_gb"] == 0.0
        assert memory["total_gb"] == 0.0


def test_api_version_endpoint(tmp_path):
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/version")
        data = response.get_json()
        assert data["version"] == actifix.__version__
        assert isinstance(data["git_checked"], bool)
        assert "branch" in data
        assert "clean" in data
        assert "dirty" in data


def test_api_version_endpoint_git_unchecked(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "_run_git_command", lambda *args, **kwargs: None)
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/api/version")
        data = response.get_json()
        assert data["git_checked"] is False
        assert data["clean"] is False
        assert data["dirty"] is False

def test_bootstrap_context_creates_paths(tmp_path):
    paths = bootstrap(project_root=tmp_path)
    assert paths.list_file.exists()

    with ActifixContext(project_root=tmp_path) as ctx_paths:
        assert ctx_paths.base_dir.exists()


def test_bootstrap_enable_disable_capture(monkeypatch):
    enable_actifix_capture()
    assert os.environ.get("ACTIFIX_CAPTURE_ENABLED") == "1"
    disable_actifix_capture()
    assert os.environ.get("ACTIFIX_CAPTURE_ENABLED") is None


def test_exception_handler_install_uninstall():
    original = install_exception_handler()
    uninstall_exception_handler(original)
    assert sys.excepthook is original


def test_health_parsing_and_breaches(tmp_path):
    assert _parse_iso_datetime("invalid") is None
    created = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    assert _get_ticket_age_hours(created) >= 1.9

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    paths.list_file.write_text(
        "\n".join(
            [
                "# Actifix Ticket List",
                "",
                "## Active Items",
                "",
                "### ACT-20260101-AAAAAA - [P0] Error: Old",
                "- **Priority**: P0",
                "- **Error Type**: Error",
                "- **Source**: `test.py:1`",
                "- **Run**: test-run",
                f"- **Created**: {created}",
                "- **Duplicate Guard**: `guard`",
                "",
                "**Checklist:**",
                "- [ ] Documented",
                "- [ ] Functioning",
                "- [ ] Tested",
                "- [ ] Completed",
                "",
                "## Completed Items",
                "",
            ]
        )
    )

    breaches = check_sla_breaches(paths)
    assert len(breaches) >= 1

    health = get_health(paths)
    assert health.open_tickets == 1


def test_health_missing_artifacts(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    paths.list_file.unlink()
    health = get_health(paths)
    assert any("Missing file" in warning for warning in health.warnings)


def test_log_atomic_write_failure_cleanup(tmp_path, monkeypatch):
    file_path = tmp_path / "fail.txt"
    temp_dir = file_path.parent

    def boom(*_args, **_kwargs):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", boom)

    with pytest.raises(OSError):
        atomic_write(file_path, "data")

    assert not list(temp_dir.glob(".*.tmp"))


def test_append_with_guard_overflow(tmp_path):
    log_file = tmp_path / "guard.log"
    log_file.write_text("line1\nline2\n")
    append_with_guard(log_file, "line3\n", max_size_bytes=10)
    assert "line3" in log_file.read_text()


def test_queue_basic_operations(tmp_path):
    queue_file = tmp_path / "queue.json"
    queue = PersistenceQueue(queue_file, max_entries=1, max_age_hours=0.0001)
    entry_id = queue.enqueue("write", "key", "value")
    assert queue.size() == 1

    queue.enqueue("write", "key", "value2")
    assert queue.size() == 1
    assert queue.peek()[0].entry_id == entry_id

    assert queue.dequeue(entry_id) is not None
    assert queue.size() == 0


def test_queue_invalid_operation(tmp_path):
    queue = PersistenceQueue(tmp_path / "queue.json")
    with pytest.raises(QueueError):
        queue.enqueue("invalid", "key", "value")


def test_queue_replay_skips(tmp_path):
    queue = PersistenceQueue(tmp_path / "queue.json")
    entry_id = queue.enqueue("write", "key", "value")
    entry = queue.peek()[0]
    entry.retry_count = 3
    queue._save()

    stats = queue.replay(lambda _entry: True, max_retries=3)
    assert stats["skipped"] == 1
    assert queue.peek()[0].entry_id == entry_id


def test_persistence_manager_operations(tmp_path):
    reset_storage_paths()
    configure_storage_paths(project_root=tmp_path)
    backend = MemoryStorageBackend()
    manager = PersistenceManager(backend, enable_queue=False)

    assert manager.write_document("k1", "v1") is True
    assert manager.read_document("k1") == "v1"
    assert manager.read_document_safe("missing", default="fallback") == "fallback"

    manager.append_to_document("k1", "\nline2", max_size_bytes=10)
    assert "line2" in manager.read_document("k1")

    manager.update_document("k1", lambda content: content + "\nline3")
    assert "line3" in manager.read_document("k1")

    assert manager.delete_document("k1") is True

    with pytest.raises(PersistenceError):
        manager.read_document("k1")


def test_persistence_manager_queue_on_failure(tmp_path):
    class FailingBackend(MemoryStorageBackend):
        def write(self, key: str, content: str, encoding: str = "utf-8") -> None:
            raise StorageError("write failed")

    reset_storage_paths()
    configure_storage_paths(project_root=tmp_path)
    manager = PersistenceManager(FailingBackend(), enable_queue=True, auto_replay=False)

    result = manager.write_document("k1", "v1")
    assert result is False
    assert manager.get_queue_stats()["size"] == 1


def test_persistence_manager_transaction(tmp_path):
    reset_storage_paths()
    configure_storage_paths(project_root=tmp_path)
    backend = MemoryStorageBackend()
    manager = PersistenceManager(backend, enable_queue=False)

    with manager.transaction() as txn:
        txn.write("k1", "v1")
        txn.append("k1", "\nline2")
        txn.commit()

    assert "line2" in manager.read_document("k1")

    with pytest.raises(PersistenceError):
        txn.commit()


def test_storage_backend_bytes_and_size(tmp_path):
    storage = FileStorageBackend(tmp_path)
    storage.write_bytes("bin", b"data")
    assert storage.read_bytes("bin") == b"data"
    assert storage.size("bin") == 4
    assert "bin" in storage.list_keys(prefix="b")

    memory = MemoryStorageBackend()
    memory.write("text", "value")
    assert memory.read_bytes("text") == b"value"
    assert memory.size("text") == 5

    with pytest.raises(StorageNotFoundError):
        memory.read("missing")


def test_testing_framework_runner(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    runner = TestRunner("core", paths=paths)

    runner.add_test("pass", lambda: None, tags=["fast"])

    def fail():
        assert False

    def error():
        raise RuntimeError("boom")

    runner.add_test("fail", fail, tags=["slow"])
    runner.add_test("error", error, tags=["slow"])

    plan = runner.declare_plan(filter_tags=["slow"])
    assert len(plan.tests) == 2

    result = runner.execute()
    assert result.failed == 1
    assert result.errors == 1

    report = runner.format_report()
    assert "FAILURE" in report


def test_testing_framework_duplicate_and_execute_guard(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    runner = TestRunner("dup", paths=paths)
    runner.add_test("one", lambda: None)

    with pytest.raises(ValueError):
        runner.add_test("one", lambda: None)

    runner = TestRunner("no-plan", paths=paths)
    with pytest.raises(RuntimeError):
        runner.execute()


def test_run_tests_helper(tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    result = run_tests("helper", [("ok", lambda: None)], paths=paths)
    assert result.success is True


def test_system_build_and_execute(tmp_path):
    base_paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(base_paths)
    tests = build_system_tests(base_paths)

    # Execute a subset to cover basic paths
    for name, func, _desc, _tags in tests[:3]:
        func()
