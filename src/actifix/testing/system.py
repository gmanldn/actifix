"""
System-level dependency and bootstrap tests for Actifix.

These tests are intentionally generic and validate that:
- Core paths and artifacts are created and writable
- Configuration loads and validates
- Persistence backends function (file + memory)
- Queues replay successfully
- Health checks run end-to-end
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional

from . import assert_true, assert_equals
from ..config import load_config, validate_config
from ..state_paths import (
    ActifixPaths,
    get_actifix_paths,
    ensure_actifix_dirs,
    init_actifix_files,
    reset_actifix_paths,
)
from ..health import run_health_check
from ..persistence.storage import FileStorageBackend, MemoryStorageBackend
from ..persistence.health import check_storage_health, detect_corruption, compute_hash, verify_integrity
from ..persistence.queue import PersistenceQueue
from ..log_utils import atomic_write


def _sandbox_paths(base_paths: ActifixPaths) -> ActifixPaths:
    """Create isolated paths for system tests to avoid polluting user data."""
    sandbox_root = base_paths.state_dir / "system_tests"
    sandbox_data = sandbox_root / "actifix"
    sandbox_state = sandbox_root / ".state"
    sandbox_logs = sandbox_root / "logs"
    
    reset_actifix_paths()
    return get_actifix_paths(
        project_root=base_paths.project_root,
        base_dir=sandbox_data,
        state_dir=sandbox_state,
        logs_dir=sandbox_logs,
    )


def build_system_tests(
    base_paths: Optional[ActifixPaths] = None,
) -> list[tuple[str, callable, str, list[str]]]:
    """
    Build the generic system and dependency tests used by the custom test runner.
    
    Returns:
        List of (name, func, description, tags) tuples.
    """
    paths = _sandbox_paths(base_paths or get_actifix_paths())
    ensure_actifix_dirs(paths)
    init_actifix_files(paths)
    
    tests: list[tuple[str, callable, str, list[str]]] = []
    
    def register(name: str, func, description: str, tags: list[str]) -> None:
        tests.append((name, func, description, tags))
    
    def test_python_version() -> None:
        assert_true(sys.version_info >= (3, 10), "Python 3.10+ is required")
    
    def test_paths_and_files() -> None:
        for artifact in paths.all_artifacts:
            assert_true(artifact.exists(), f"Missing artifact {artifact.name}")
        # Ensure writability
        probe = paths.base_dir / ".writable_probe"
        atomic_write(probe, "ok")
        assert_true(probe.exists(), "Failed to write probe file")
        probe.unlink()
    
    def test_config_validation() -> None:
        config = load_config(project_root=paths.project_root)
        errors = validate_config(config)
        assert_equals(errors, [], f"Config validation errors: {errors}")
    
    def test_file_storage_round_trip() -> None:
        storage = FileStorageBackend(paths.state_dir / "storage")
        key = "sample.txt"
        storage.write(key, "hello")
        assert_equals(storage.read(key), "hello")
        assert_true(storage.exists(key))
        assert_true(key in storage.list_keys())
        storage.delete(key)
        assert_true(not storage.exists(key))
    
    def test_queue_replay() -> None:
        queue_path = paths.state_dir / "queue.json"
        queue = PersistenceQueue(queue_path)
        queue.enqueue("write", "queue-key", "payload")
        
        def handler(entry):
            return entry.content == "payload"
        
        stats = queue.replay(handler)
        assert_equals(stats["succeeded"], 1)
        assert_equals(queue.size(), 0)
    
    def test_storage_health_and_corruption() -> None:
        storage = MemoryStorageBackend()
        storage.write("good", "value")
        storage.write("utf8", "text-unicode")
        
        status = check_storage_health(storage, test_key="health_probe")
        assert_true(status.healthy, f"Storage health failed: {status.errors}")
        
        corruption = detect_corruption(storage, sample_keys=["good", "utf8"])
        assert_equals(corruption["corrupted"], 0)
        assert_equals(corruption["unreadable"], 0)
    
    def test_integrity_hashing() -> None:
        storage = MemoryStorageBackend()
        storage.write("payload", "abc")
        digest = compute_hash(storage, "payload")
        assert_true(digest is not None, "Expected digest")
        assert_true(verify_integrity(storage, "payload", digest or ""), "Hash verification failed")
    
    def test_health_check_runs() -> None:
        health = run_health_check(paths=paths, print_report=False)
        assert_true(health.status in {"OK", "WARNING", "ERROR", "SLA_BREACH"})
    
    register("python_version", test_python_version, "Python version check", ["system", "dependencies"])
    register("paths_bootstrap", test_paths_and_files, "Path and artifact bootstrap", ["system", "bootstrap"])
    register("config_validation", test_config_validation, "Configuration validation", ["config"])
    register("file_storage_round_trip", test_file_storage_round_trip, "File storage backend", ["persistence"])
    register("queue_replay", test_queue_replay, "Persistence queue replay", ["persistence"])
    register("storage_health", test_storage_health_and_corruption, "Storage health and corruption detection", ["persistence", "health"])
    register("integrity_hashing", test_integrity_hashing, "Integrity hashing verification", ["persistence"])
    register("health_check", test_health_check_runs, "Actifix health execution", ["health"])
    
    return tests
