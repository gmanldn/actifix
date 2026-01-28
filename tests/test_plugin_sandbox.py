"""Tests for plugin sandboxing: isolation, capability control, timeout."""

import pytest
import time
from typing import Set

from actifix.plugins.sandbox import (
    PluginSandbox,
    PluginMetadata,
    PluginCapability,
    PluginExecutionContext,
    PluginFailure,
)


@pytest.fixture
def sandbox():
    """Create a test plugin sandbox."""
    return PluginSandbox("test_sandbox", max_workers=2, default_timeout_s=1.0)


class TestPluginMetadata:
    """Test PluginMetadata validation."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="test_author",
        )
        is_valid, errors = metadata.validate()
        assert is_valid
        assert errors == []

    def test_missing_name(self):
        """Test metadata with missing name."""
        metadata = PluginMetadata(name="", version="1.0.0", author="author")
        is_valid, errors = metadata.validate()
        assert not is_valid
        assert len(errors) > 0

    def test_capabilities(self):
        """Test metadata with capabilities."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="author",
            capabilities={PluginCapability.DATABASE, PluginCapability.NETWORK},
        )
        assert PluginCapability.DATABASE in metadata.capabilities
        assert PluginCapability.FILESYSTEM not in metadata.capabilities


class TestPluginExecutionContext:
    """Test PluginExecutionContext."""

    def test_context_creation(self):
        """Test creating execution context."""
        context = PluginExecutionContext(
            plugin_name="test",
            plugin_version="1.0.0",
            capabilities={PluginCapability.DATABASE},
        )
        assert context.plugin_name == "test"
        assert context.elapsed_seconds() >= 0

    def test_has_capability(self):
        """Test capability checking."""
        context = PluginExecutionContext(
            plugin_name="test",
            plugin_version="1.0.0",
            capabilities={PluginCapability.DATABASE},
        )
        assert context.has_capability(PluginCapability.DATABASE)
        assert not context.has_capability(PluginCapability.NETWORK)


class TestPluginSandbox:
    """Test PluginSandbox core functionality."""

    def test_sandbox_creation(self):
        """Test creating sandbox."""
        sandbox = PluginSandbox("test", max_workers=4, default_timeout_s=30.0)
        assert sandbox.name == "test"
        assert sandbox.API_VERSION == "1.0.0"

    def test_validate_metadata(self, sandbox):
        """Test metadata validation."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="author",
        )
        is_valid, errors = sandbox.validate_metadata(metadata)
        assert is_valid
        assert len(errors) == 0

    def test_validate_metadata_api_version_mismatch(self, sandbox):
        """Test metadata validation with API version mismatch."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="author",
            min_api_version="2.0.0",  # Incompatible
        )
        is_valid, errors = sandbox.validate_metadata(metadata)
        assert not is_valid
        assert any("API version" in err for err in errors)

    def test_execute_plugin_success(self, sandbox):
        """Test successful plugin execution."""
        def handler(name: str = "default"):
            return f"Hello {name}"

        result = sandbox.execute_plugin(
            "test_plugin",
            handler,
            name="world",
        )

        assert isinstance(result, str)
        assert "Hello world" in result

    def test_execute_plugin_with_capabilities(self, sandbox):
        """Test plugin execution with capabilities."""
        def handler(db_connection: str = None, name: str = "test"):
            return db_connection or "no_db"

        # Execute without capability - should be filtered out
        result = sandbox.execute_plugin(
            "test_plugin",
            handler,
            capabilities=set(),  # No capabilities
            db_connection="localhost:5432",
            name="test",
        )

        # db_connection should be filtered out
        assert result == "no_db"

    def test_execute_plugin_with_database_capability(self, sandbox):
        """Test plugin with database capability."""
        def handler(db_connection: str = None):
            return db_connection or "no_db"

        result = sandbox.execute_plugin(
            "test_plugin",
            handler,
            capabilities={PluginCapability.DATABASE},
            db_connection="localhost:5432",
        )

        assert result == "localhost:5432"

    def test_execute_plugin_timeout(self, sandbox):
        """Test plugin timeout."""
        def slow_handler():
            time.sleep(10)
            return "done"

        result = sandbox.execute_plugin(
            "slow_plugin",
            slow_handler,
            timeout_seconds=0.1,
        )

        assert isinstance(result, PluginFailure)
        assert result.timed_out
        assert "timeout" in result.error.lower()

    def test_execute_plugin_failure(self, sandbox):
        """Test plugin exception handling."""
        def failing_handler():
            raise RuntimeError("Intentional error")

        result = sandbox.execute_plugin(
            "failing_plugin",
            failing_handler,
        )

        assert isinstance(result, PluginFailure)
        assert not result.timed_out
        assert "error" in result.error.lower()

    def test_check_capability(self, sandbox):
        """Test capability checking."""
        context = PluginExecutionContext(
            plugin_name="test",
            plugin_version="1.0.0",
            capabilities={PluginCapability.DATABASE},
        )

        assert sandbox.check_capability(context, PluginCapability.DATABASE)
        assert not sandbox.check_capability(context, PluginCapability.NETWORK)

    def test_get_active_plugins(self, sandbox):
        """Test getting active plugins."""
        def slow_handler():
            time.sleep(0.2)

        # Start an async plugin
        import threading
        thread = threading.Thread(
            target=sandbox.execute_plugin,
            args=("async_plugin", slow_handler),
        )
        thread.start()

        # Check active plugins
        active = sandbox.get_active_plugins()
        # May or may not have started yet
        thread.join()

    def test_versions_compatible(self, sandbox):
        """Test version compatibility checking."""
        assert sandbox._versions_compatible("1.0.0", "1.2.0")
        assert sandbox._versions_compatible("1.0.0", "1.0.5")
        assert not sandbox._versions_compatible("1.0.0", "2.0.0")
        assert not sandbox._versions_compatible("2.0.0", "1.0.0")

    def test_filter_kwargs(self, sandbox):
        """Test keyword argument filtering."""
        kwargs = {
            "name": "test",
            "version": "1.0.0",
            "db_connection": "localhost",
            "net_endpoint": "example.com",
            "fs_path": "/tmp",
        }

        # No capabilities - only safe kwargs
        filtered = sandbox._filter_kwargs(kwargs, set())
        assert "name" in filtered
        assert "db_connection" not in filtered
        assert "net_endpoint" not in filtered

        # With database capability
        filtered = sandbox._filter_kwargs(
            kwargs,
            {PluginCapability.DATABASE}
        )
        assert "db_connection" in filtered
        assert "net_endpoint" not in filtered

    def test_plugin_failure_repr(self):
        """Test PluginFailure string representation."""
        failure = PluginFailure("test", "error message", timed_out=True)
        assert "TIMEOUT" in repr(failure)
        assert "test" in repr(failure)

        failure2 = PluginFailure("test2", "error", timed_out=False)
        assert "FAILED" in repr(failure2)

    def test_sandbox_shutdown(self, sandbox):
        """Test sandbox shutdown."""
        def handler():
            return "test"

        sandbox.execute_plugin("test", handler)
        sandbox.shutdown(wait=True)
        # After shutdown, executor should be shut down

    def test_multiple_concurrent_plugins(self, sandbox):
        """Test multiple concurrent plugins."""
        def quick_handler(n: int = 0):
            return n * 2

        results = []
        for i in range(3):
            result = sandbox.execute_plugin(
                f"plugin_{i}",
                quick_handler,
                n=i,
            )
            results.append(result)

        assert len(results) == 3
        assert all(isinstance(r, int) for r in results)

    def test_execution_context_elapsed_time(self):
        """Test execution context elapsed time tracking."""
        context = PluginExecutionContext(
            plugin_name="test",
            plugin_version="1.0.0",
            capabilities=set(),
        )

        time.sleep(0.05)
        elapsed = context.elapsed_seconds()

        assert elapsed >= 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
