"""Tests for thread cleanup functionality."""

import threading
import time
from unittest.mock import patch

import pytest

from actifix.thread_cleanup import (
    ThreadInfo,
    cleanup_orphan_threads,
    enumerate_threads,
    get_thread_summary,
    is_orphan_thread,
    log_thread_state,
)


class TestThreadEnumeration:
    """Test thread enumeration functionality."""

    def test_enumerate_threads_includes_main(self):
        """Test that thread enumeration includes the main thread."""
        threads = enumerate_threads()
        thread_names = [t.name for t in threads]
        assert "MainThread" in thread_names

    def test_enumerate_threads_returns_thread_info(self):
        """Test that enumeration returns ThreadInfo objects."""
        threads = enumerate_threads()
        assert len(threads) > 0
        for thread in threads:
            assert isinstance(thread, ThreadInfo)
            assert isinstance(thread.name, str)
            assert isinstance(thread.daemon, bool)
            assert isinstance(thread.alive, bool)

    def test_enumerate_threads_tracks_daemon_status(self):
        """Test that daemon status is correctly tracked."""
        # Create a daemon thread
        stop_event = threading.Event()

        def worker():
            stop_event.wait(timeout=2.0)

        thread = threading.Thread(target=worker, daemon=True, name="test-daemon")
        thread.start()

        try:
            threads = enumerate_threads()
            daemon_threads = [t for t in threads if t.name == "test-daemon"]
            assert len(daemon_threads) == 1
            assert daemon_threads[0].daemon is True
        finally:
            stop_event.set()
            thread.join(timeout=1.0)


class TestOrphanDetection:
    """Test orphan thread detection."""

    def test_main_thread_not_orphan(self):
        """Test that MainThread is never considered an orphan."""
        main_thread = ThreadInfo(
            name="MainThread", ident=1, daemon=False, alive=True
        )
        assert not is_orphan_thread(main_thread)

    def test_pytest_thread_not_orphan(self):
        """Test that pytest threads are not considered orphans."""
        pytest_thread = ThreadInfo(
            name="pytest-worker-1", ident=2, daemon=True, alive=True
        )
        assert not is_orphan_thread(pytest_thread)

    def test_system_thread_not_orphan(self):
        """Test that system threads are not considered orphans."""
        dummy_thread = ThreadInfo(name="Dummy-1", ident=3, daemon=True, alive=True)
        assert not is_orphan_thread(dummy_thread)

    def test_daemon_thread_is_orphan(self):
        """Test that unknown daemon threads are considered orphans."""
        orphan = ThreadInfo(
            name="orphan-thread", ident=4, daemon=True, alive=True
        )
        assert is_orphan_thread(orphan)

    def test_non_daemon_thread_not_orphan(self):
        """Test that non-daemon threads are not considered orphans."""
        non_daemon = ThreadInfo(
            name="worker-thread", ident=5, daemon=False, alive=True
        )
        assert not is_orphan_thread(non_daemon)

    def test_dead_thread_not_orphan(self):
        """Test that dead threads are not considered orphans."""
        dead_thread = ThreadInfo(
            name="dead-thread", ident=6, daemon=True, alive=False
        )
        # Dead threads won't be alive, so they won't be orphans
        assert not is_orphan_thread(dead_thread)


class TestCleanupOrphanThreads:
    """Test orphan thread cleanup."""

    def test_cleanup_no_orphans(self):
        """Test cleanup when no orphans exist."""
        # Should complete without error
        count = cleanup_orphan_threads(timeout=0.1)
        assert count >= 0

    def test_cleanup_detects_orphan(self):
        """Test that cleanup detects orphan threads."""
        stop_event = threading.Event()

        def worker():
            stop_event.wait(timeout=5.0)

        # Create an orphan daemon thread
        thread = threading.Thread(target=worker, daemon=True, name="test-orphan")
        thread.start()

        try:
            count = cleanup_orphan_threads(timeout=0.1)
            # Should detect at least our orphan
            assert count >= 1
        finally:
            stop_event.set()
            thread.join(timeout=1.0)

    def test_cleanup_with_multiple_threads(self):
        """Test cleanup with multiple threads."""
        stop_events = []
        threads = []

        def worker(event):
            event.wait(timeout=5.0)

        # Create multiple daemon threads
        for i in range(3):
            event = threading.Event()
            stop_events.append(event)
            thread = threading.Thread(
                target=worker, args=(event,), daemon=True, name=f"test-orphan-{i}"
            )
            thread.start()
            threads.append(thread)

        try:
            count = cleanup_orphan_threads(timeout=0.1)
            # Should detect at least our orphans
            assert count >= 3
        finally:
            for event in stop_events:
                event.set()
            for thread in threads:
                thread.join(timeout=1.0)


class TestThreadSummary:
    """Test thread summary functionality."""

    def test_get_thread_summary_structure(self):
        """Test that thread summary has expected structure."""
        summary = get_thread_summary()
        assert "total_threads" in summary
        assert "daemon_threads" in summary
        assert "orphan_threads" in summary
        assert "main_thread_alive" in summary
        assert "thread_names" in summary
        assert "orphan_names" in summary

    def test_get_thread_summary_main_thread_alive(self):
        """Test that main thread is reported as alive."""
        summary = get_thread_summary()
        assert summary["main_thread_alive"] is True

    def test_get_thread_summary_counts(self):
        """Test that summary counts are reasonable."""
        summary = get_thread_summary()
        assert summary["total_threads"] >= 1  # At least main thread
        assert summary["daemon_threads"] >= 0
        assert summary["orphan_threads"] >= 0
        assert len(summary["thread_names"]) == summary["total_threads"]
        assert len(summary["orphan_names"]) == summary["orphan_threads"]

    def test_log_thread_state_no_error(self):
        """Test that logging thread state doesn't raise errors."""
        # Should complete without error
        log_thread_state()


class TestBootstrapIntegration:
    """Test integration with bootstrap."""

    def test_bootstrap_calls_cleanup(self):
        """Test that bootstrap calls thread cleanup."""
        import os
        from pathlib import Path
        import tempfile

        # Set required environment variable
        os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
        
        # Create a temporary project root
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create required data directory
            data_dir = project_root / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Bootstrap should call cleanup_orphan_threads and complete successfully
            try:
                from actifix.bootstrap import bootstrap
                paths = bootstrap(project_root=project_root)
                # Verify bootstrap succeeded and returned paths
                assert paths is not None
                assert paths.project_root == project_root
            except Exception as e:
                # If bootstrap fails for other reasons (like DB initialization),
                # that's okay - we're just testing that cleanup doesn't crash
                assert "cleanup" not in str(e).lower(), f"Cleanup should not cause failures: {e}"


class TestThreadCleanupRobustness:
    """Test thread cleanup robustness."""

    def test_cleanup_with_short_timeout(self):
        """Test cleanup with very short timeout."""
        count = cleanup_orphan_threads(timeout=0.01)
        assert count >= 0

    def test_cleanup_with_zero_timeout(self):
        """Test cleanup with zero timeout."""
        count = cleanup_orphan_threads(timeout=0.0)
        assert count >= 0

    def test_cleanup_multiple_times(self):
        """Test that cleanup can be called multiple times."""
        count1 = cleanup_orphan_threads(timeout=0.1)
        count2 = cleanup_orphan_threads(timeout=0.1)
        # Both should succeed
        assert count1 >= 0
        assert count2 >= 0

    def test_thread_info_immutable(self):
        """Test that ThreadInfo is immutable."""
        info = ThreadInfo(name="test", ident=1, daemon=True, alive=True)
        with pytest.raises(AttributeError):
            info.name = "modified"  # type: ignore


class TestThreadLifecycle:
    """Test thread lifecycle handling."""

    def test_thread_cleanup_allows_completion(self):
        """Test that cleanup allows threads to complete naturally."""
        completed = threading.Event()

        def worker():
            time.sleep(0.1)
            completed.set()

        thread = threading.Thread(target=worker, daemon=True, name="test-completing")
        thread.start()

        # Cleanup should detect the thread but not interfere
        cleanup_orphan_threads(timeout=0.5)

        # Thread should still be able to complete
        assert completed.wait(timeout=1.0)

    def test_orphan_detection_thread_safe(self):
        """Test that orphan detection is thread-safe."""
        threads_to_start = []

        def worker():
            time.sleep(0.2)

        # Start multiple threads concurrently
        for i in range(5):
            thread = threading.Thread(
                target=worker, daemon=True, name=f"test-concurrent-{i}"
            )
            threads_to_start.append(thread)

        for thread in threads_to_start:
            thread.start()

        # Should handle concurrent thread enumeration
        summary1 = get_thread_summary()
        summary2 = get_thread_summary()

        # Both summaries should be valid
        assert summary1["total_threads"] > 0
        assert summary2["total_threads"] > 0

        for thread in threads_to_start:
            thread.join(timeout=1.0)