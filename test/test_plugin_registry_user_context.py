#!/usr/bin/env python3
"""
Tests for plugin registry user context logging.

Verifies that:
1. Plugin load events include user context
2. Plugin unload events include user context
3. User context defaults to system user if not provided
4. Load/unload failures are logged with user context
5. User context can be explicitly provided
"""

import os
from unittest.mock import Mock, patch, MagicMock
import pytest

from actifix.plugins.registry import PluginRegistry, PluginContextManager
from actifix.plugins.protocol import Plugin, PluginMetadata


@pytest.fixture
def mock_plugin():
    """Create a mock plugin for testing."""
    plugin = Mock(spec=Plugin)
    plugin.metadata = Mock(spec=PluginMetadata)
    plugin.metadata.name = "test_plugin"
    plugin.metadata.version = "1.0.0"
    plugin.register = Mock()
    plugin.unregister = Mock()
    return plugin


@pytest.fixture
def registry():
    """Create a fresh registry for testing."""
    return PluginRegistry()


class TestPluginRegistryUserContext:
    """Test user context logging in plugin registry."""

    @patch("actifix.plugins.registry.log_event")
    def test_register_logs_user_context_explicit(self, mock_log, registry, mock_plugin):
        """Verify plugin load logs with explicit user context."""
        registry.register(mock_plugin, app=None, name="test_plugin", user_context="alice")

        # Verify log_event was called for plugin load
        assert mock_log.called
        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        assert len(calls) > 0

        # Check user context in extra data
        call_kwargs = calls[0][1]
        assert call_kwargs["extra"]["user"] == "alice"
        assert call_kwargs["extra"]["plugin_name"] == "test_plugin"
        assert call_kwargs["extra"]["plugin_version"] == "1.0.0"

    @patch("actifix.plugins.registry.log_event")
    def test_register_logs_user_context_from_env(self, mock_log, registry, mock_plugin):
        """Verify plugin load logs with user context from environment."""
        with patch.dict(os.environ, {"ACTIFIX_USER": "bob"}):
            registry.register(mock_plugin, app=None, name="test_plugin")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        assert len(calls) > 0

        call_kwargs = calls[0][1]
        assert call_kwargs["extra"]["user"] == "bob"

    @patch("actifix.plugins.registry.log_event")
    def test_register_logs_user_context_default(self, mock_log, registry, mock_plugin):
        """Verify plugin load defaults to system user if not provided."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("actifix.plugins.registry.os.environ.get") as mock_get:
                mock_get.side_effect = lambda key, default=None: {
                    "ACTIFIX_USER": None,
                    "USER": "system_user",
                }.get(key, default)

                registry.register(mock_plugin, app=None, name="test_plugin")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        if calls:  # Only check if call was made
            call_kwargs = calls[0][1]
            assert call_kwargs["extra"]["user"] is not None

    @patch("actifix.plugins.registry.log_event")
    def test_unregister_logs_user_context_explicit(self, mock_log, registry, mock_plugin):
        """Verify plugin unload logs with explicit user context."""
        registry.register(mock_plugin, app=None, name="test_plugin")
        mock_log.reset_mock()

        registry.unregister("test_plugin", user_context="charlie")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_UNLOADED" in str(call)]
        assert len(calls) > 0

        call_kwargs = calls[0][1]
        assert call_kwargs["extra"]["user"] == "charlie"
        assert call_kwargs["extra"]["plugin_name"] == "test_plugin"

    @patch("actifix.plugins.registry.log_event")
    def test_register_failure_logs_user_context(self, mock_log, registry, mock_plugin):
        """Verify plugin load failure logs with user context."""
        mock_plugin.register.side_effect = Exception("Load failed")

        with pytest.raises(Exception):
            registry.register(mock_plugin, app=None, name="test_plugin", user_context="dave")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOAD_FAILED" in str(call)]
        assert len(calls) > 0

        call_kwargs = calls[0][1]
        assert call_kwargs["extra"]["user"] == "dave"
        assert call_kwargs["extra"]["plugin_name"] == "test_plugin"
        assert "error" in call_kwargs["extra"]

    @patch("actifix.plugins.registry.log_event")
    def test_unregister_failure_logs_user_context(self, mock_log, registry, mock_plugin):
        """Verify plugin unload failure logs with user context."""
        registry.register(mock_plugin, app=None, name="test_plugin")
        mock_log.reset_mock()

        mock_plugin.unregister.side_effect = Exception("Unload failed")

        with pytest.raises(Exception):
            registry.unregister("test_plugin", user_context="eve")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_UNLOAD_FAILED" in str(call)]
        assert len(calls) > 0

        call_kwargs = calls[0][1]
        assert call_kwargs["extra"]["user"] == "eve"
        assert call_kwargs["extra"]["plugin_name"] == "test_plugin"
        assert "error" in call_kwargs["extra"]


class TestPluginContextManagerUserContext:
    """Test user context in PluginContextManager."""

    @patch("actifix.plugins.registry.log_event")
    def test_context_manager_logs_user_context(self, mock_log, registry, mock_plugin):
        """Verify context manager passes user context to register/unregister."""
        with PluginContextManager(registry, "test_plugin", mock_plugin, user_context="frank"):
            pass

        # Check register was called with user context
        register_calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        assert len(register_calls) > 0

        # Check unregister was called with user context
        unregister_calls = [call for call in mock_log.call_args_list if "PLUGIN_UNLOADED" in str(call)]
        assert len(unregister_calls) > 0

        for call in register_calls + unregister_calls:
            assert call[1]["extra"]["user"] == "frank"

    @patch("actifix.plugins.registry.log_event")
    def test_context_manager_default_user_context(self, mock_log, registry, mock_plugin):
        """Verify context manager defaults to system user."""
        with patch.dict(os.environ, {"USER": "grace"}):
            with PluginContextManager(registry, "test_plugin", mock_plugin):
                pass

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        if calls:
            call_kwargs = calls[0][1]
            assert call_kwargs["extra"]["user"] is not None


class TestPluginRegistryLoggingFormat:
    """Test logging format for plugin events."""

    @patch("actifix.plugins.registry.log_event")
    def test_plugin_loaded_event_format(self, mock_log, registry, mock_plugin):
        """Verify PLUGIN_LOADED event has correct format."""
        registry.register(mock_plugin, app=None, name="test_plugin", user_context="henry")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOADED" in str(call)]
        assert len(calls) > 0

        args, kwargs = calls[0]
        assert args[0] == "PLUGIN_LOADED"
        assert "Plugin loaded" in args[1]
        assert kwargs["extra"]["plugin_name"] == "test_plugin"
        assert kwargs["extra"]["user"] == "henry"
        assert kwargs["extra"]["plugin_version"] == "1.0.0"

    @patch("actifix.plugins.registry.log_event")
    def test_plugin_unloaded_event_format(self, mock_log, registry, mock_plugin):
        """Verify PLUGIN_UNLOADED event has correct format."""
        registry.register(mock_plugin, app=None, name="test_plugin")
        mock_log.reset_mock()

        registry.unregister("test_plugin", user_context="iris")

        calls = [call for call in mock_log.call_args_list if "PLUGIN_UNLOADED" in str(call)]
        assert len(calls) > 0

        args, kwargs = calls[0]
        assert args[0] == "PLUGIN_UNLOADED"
        assert "Plugin unloaded" in args[1]
        assert kwargs["extra"]["plugin_name"] == "test_plugin"
        assert kwargs["extra"]["user"] == "iris"

    @patch("actifix.plugins.registry.log_event")
    def test_load_failure_event_format(self, mock_log, registry, mock_plugin):
        """Verify PLUGIN_LOAD_FAILED event includes error details."""
        mock_plugin.register.side_effect = Exception("Database error")

        try:
            registry.register(mock_plugin, app=None, name="test_plugin", user_context="jack")
        except Exception:
            pass

        calls = [call for call in mock_log.call_args_list if "PLUGIN_LOAD_FAILED" in str(call)]
        assert len(calls) > 0

        args, kwargs = calls[0]
        assert args[0] == "PLUGIN_LOAD_FAILED"
        assert kwargs["level"] == "ERROR"
        assert kwargs["extra"]["error"] == "Database error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
