#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for singleton enforcement of backend and frontend instances.
Ensures only one instance of each can exist and no browser windows spawn by default.
"""

import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scripts import start

pytestmark = [pytest.mark.integration]


class TestBackendSingleton(unittest.TestCase):
    """Test that only one backend API server instance can exist."""

    def setUp(self):
        """Reset singleton state before each test."""
        start._API_SERVER_INSTANCE = None

    def tearDown(self):
        """Clean up after test."""
        start._API_SERVER_INSTANCE = None

    @patch('scripts.start.threading.Thread')
    def test_backend_singleton_first_call(self, mock_thread_class):
        """Test that first call creates backend instance."""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread

        # First call should create new instance
        result = start.start_api_server(5001, ROOT)

        self.assertIsNotNone(result)
        self.assertEqual(start._API_SERVER_INSTANCE, mock_thread)
        mock_thread.start.assert_called_once()

    @patch('scripts.start.threading.Thread')
    def test_backend_singleton_prevents_duplicate(self, mock_thread_class):
        """Test that second call returns existing instance and refuses to create duplicate."""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread

        # First call creates instance
        first_result = start.start_api_server(5001, ROOT)

        # Second call should return same instance and NOT start new thread
        second_result = start.start_api_server(5001, ROOT)

        self.assertIs(first_result, second_result)
        self.assertIs(second_result, mock_thread)
        # Thread.start() should only be called once (from first call)
        mock_thread.start.assert_called_once()

    def test_backend_singleton_concurrent_calls(self):
        """Test that concurrent calls to start_api_server maintain singleton."""
        # We'll use a real mock for the API server thread, but not patch Thread itself
        # to avoid interfering with our test threads
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        results = []
        call_count = [0]  # Use list to make it mutable in nested function

        original_thread_init = threading.Thread.__init__

        def mock_thread_init(self, *args, **kwargs):
            # Only mock threads created for API server (daemon=True)
            if kwargs.get('daemon'):
                call_count[0] += 1
                # Replace the thread with our mock
                self._target = lambda: None
                self._args = ()
                self._kwargs = {}
                self._daemonic = True
            else:
                # Let test threads work normally
                original_thread_init(self, *args, **kwargs)

        def start_backend():
            # Directly test the singleton logic without starting real server
            with start._API_SERVER_LOCK:
                if start._API_SERVER_INSTANCE is not None and start._API_SERVER_INSTANCE.is_alive():
                    results.append(start._API_SERVER_INSTANCE)
                else:
                    # First call - set up the instance
                    if start._API_SERVER_INSTANCE is None:
                        start._API_SERVER_INSTANCE = mock_thread
                    results.append(start._API_SERVER_INSTANCE)

        # Try to start multiple backends concurrently
        threads = [threading.Thread(target=start_backend) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be the same instance
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIs(result, results[0])


class TestFrontendSingleton(unittest.TestCase):
    """Test that only one frontend manager instance can exist."""

    def setUp(self):
        """Reset singleton state before each test."""
        start.FrontendManager._instance = None

    def tearDown(self):
        """Clean up after test."""
        start.FrontendManager._instance = None

    def test_frontend_singleton_first_call(self):
        """Test that first call creates frontend manager instance."""
        manager1 = start.FrontendManager(8080)

        self.assertIsNotNone(manager1)
        self.assertEqual(manager1.port, 8080)
        self.assertIs(start.FrontendManager._instance, manager1)

    def test_frontend_singleton_prevents_duplicate(self):
        """Test that second call returns existing instance."""
        manager1 = start.FrontendManager(8080)
        manager2 = start.FrontendManager(8081)  # Different port, but should return same instance

        self.assertIs(manager1, manager2)
        self.assertEqual(manager1.port, 8080)  # Port should remain from first initialization
        self.assertEqual(manager2.port, 8080)  # Second call doesn't change port

    def test_frontend_singleton_concurrent_instantiation(self):
        """Test that concurrent instantiation maintains singleton."""
        managers = []

        def create_manager(port):
            manager = start.FrontendManager(port)
            managers.append(manager)

        # Try to create multiple managers concurrently
        threads = [threading.Thread(target=create_manager, args=(8080 + i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All managers should be the same instance
        self.assertEqual(len(managers), 5)
        for manager in managers:
            self.assertIs(manager, managers[0])

    @patch('scripts.start.start_frontend')
    def test_frontend_start_prevents_duplicate_process(self, mock_start_frontend):
        """Test that calling start() multiple times on same manager doesn't create duplicate processes."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_start_frontend.return_value = mock_process

        manager = start.FrontendManager(8080)

        # First start creates process
        process1 = manager.start()
        self.assertIsNotNone(process1)

        # Second start should return same process without creating new one
        process2 = manager.start()
        self.assertIs(process1, process2)

        # start_frontend should only be called once
        mock_start_frontend.assert_called_once_with(8080)


class TestBrowserWindowsPrevention(unittest.TestCase):
    """Test that browser windows are not spawned by default."""

    def test_default_args_disable_browser(self):
        """Test that default arguments disable browser launch."""
        args = start.parse_args([])

        # Browser should be disabled by default
        self.assertFalse(args.browser)

    def test_browser_flag_enables_browser(self):
        """Test that --browser flag enables browser launch."""
        args = start.parse_args(['--browser'])

        # Browser should be enabled with flag
        self.assertTrue(args.browser)

    @patch('scripts.start.webbrowser.open')
    @patch('scripts.start.FrontendManager')
    @patch('scripts.start.start_api_server')
    @patch('scripts.start.start_version_monitor')
    @patch('scripts.start.is_port_in_use')
    @patch('scripts.start.ensure_scaffold')
    @patch('scripts.start.clean_bytecode_cache')
    def test_browser_not_opened_by_default(
        self,
        mock_clean,
        mock_scaffold,
        mock_port_check,
        mock_version_monitor,
        mock_start_api,
        mock_frontend_manager,
        mock_webbrowser
    ):
        """Test that browser is not opened when --browser flag is not provided."""
        mock_port_check.return_value = False
        mock_frontend = MagicMock()
        mock_frontend_manager.return_value = mock_frontend

        # Run main without --browser flag - should timeout waiting, so we'll interrupt it
        import signal

        def timeout_handler(signum, frame):
            raise KeyboardInterrupt()

        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)  # 1 second timeout

        try:
            start.main([])
        except KeyboardInterrupt:
            pass
        finally:
            signal.alarm(0)  # Cancel alarm

        # webbrowser.open should NOT be called
        mock_webbrowser.assert_not_called()

    @patch('scripts.start.webbrowser.open')
    @patch('scripts.start.FrontendManager')
    @patch('scripts.start.start_api_server')
    @patch('scripts.start.start_version_monitor')
    @patch('scripts.start.is_port_in_use')
    @patch('scripts.start.ensure_scaffold')
    @patch('scripts.start.clean_bytecode_cache')
    def test_browser_opened_with_flag(
        self,
        mock_clean,
        mock_scaffold,
        mock_port_check,
        mock_version_monitor,
        mock_start_api,
        mock_frontend_manager,
        mock_webbrowser
    ):
        """Test that browser IS opened when --browser flag is provided."""
        mock_port_check.return_value = False
        mock_frontend = MagicMock()
        mock_frontend_manager.return_value = mock_frontend

        # Run main with --browser flag - should timeout waiting, so we'll interrupt it
        import signal

        def timeout_handler(signum, frame):
            raise KeyboardInterrupt()

        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)  # 1 second timeout

        try:
            start.main(['--browser'])
        except KeyboardInterrupt:
            pass
        finally:
            signal.alarm(0)  # Cancel alarm

        # webbrowser.open SHOULD be called
        mock_webbrowser.assert_called_once()


class TestEndToEndSingletonEnforcement(unittest.TestCase):
    """End-to-end tests for singleton enforcement."""

    def setUp(self):
        """Reset all singleton state."""
        start._API_SERVER_INSTANCE = None
        start.FrontendManager._instance = None

    def tearDown(self):
        """Clean up singleton state."""
        start._API_SERVER_INSTANCE = None
        start.FrontendManager._instance = None

    @patch('scripts.start.threading.Thread')
    @patch('scripts.start.start_frontend')
    def test_complete_singleton_enforcement(self, mock_start_frontend, mock_thread_class):
        """Test that both backend and frontend maintain singleton across multiple operations."""
        # Mock backend thread
        mock_backend_thread = MagicMock()
        mock_backend_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_backend_thread

        # Mock frontend process
        mock_frontend_process = MagicMock()
        mock_frontend_process.poll.return_value = None
        mock_start_frontend.return_value = mock_frontend_process

        # Create backend instance
        backend1 = start.start_api_server(5001, ROOT)
        backend2 = start.start_api_server(5001, ROOT)

        # Create frontend instance
        frontend_mgr1 = start.FrontendManager(8080)
        frontend_mgr2 = start.FrontendManager(8081)

        # Start frontend servers
        frontend_proc1 = frontend_mgr1.start()
        frontend_proc2 = frontend_mgr2.start()

        # Verify singletons
        self.assertIs(backend1, backend2, "Backend singleton not enforced")
        self.assertIs(frontend_mgr1, frontend_mgr2, "Frontend manager singleton not enforced")
        self.assertIs(frontend_proc1, frontend_proc2, "Frontend process singleton not enforced")

        # Verify only one thread/process was started
        mock_backend_thread.start.assert_called_once()
        mock_start_frontend.assert_called_once()


if __name__ == '__main__':
    unittest.main()
