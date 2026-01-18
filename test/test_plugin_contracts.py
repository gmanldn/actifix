#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contract tests for Plugin protocol implementation compliance.

Verifies that all plugins implement required methods and follow
the Plugin protocol specification.
"""

import inspect
import sys
from pathlib import Path
from typing import Type

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.plugins.builtin import CorePlugin
from actifix.plugins.protocol import Plugin, PluginMetadata, PluginHealthStatus


class PluginProtocolContract:
    """Defines the expected contract for Plugin implementations."""

    REQUIRED_METHODS = {
        "register",
        "unregister",
        "health",
    }

    REQUIRED_ATTRIBUTES = {
        "metadata",
    }

    @classmethod
    def check_implementation(cls, plugin_class: Type) -> dict:
        """Check if a plugin class implements the required contract."""
        results = {
            "valid": True,
            "missing_methods": [],
            "missing_attributes": [],
            "type_errors": [],
            "documentation": [],
        }

        # Check for required methods
        for method_name in cls.REQUIRED_METHODS:
            if not hasattr(plugin_class, method_name):
                results["missing_methods"].append(method_name)
                results["valid"] = False
            else:
                attr = getattr(plugin_class, method_name)
                if not callable(attr):
                    results["type_errors"].append(
                        f"{method_name} is not callable"
                    )
                    results["valid"] = False

        # Check for required attributes
        for attr_name in cls.REQUIRED_ATTRIBUTES:
            if not hasattr(plugin_class, attr_name):
                results["missing_attributes"].append(attr_name)
                # Note: Attributes might be properties, so not necessarily invalid

        # Check documentation
        if not inspect.getdoc(plugin_class):
            results["documentation"].append("Missing class docstring")

        return results


class TestPluginContracts:
    """Test plugin implementations conform to protocol."""

    def test_core_plugin_implements_protocol(self):
        """Test that CorePlugin implements the plugin protocol."""
        results = PluginProtocolContract.check_implementation(CorePlugin)

        assert results["valid"], (
            f"CorePlugin does not implement plugin protocol: "
            f"missing_methods={results['missing_methods']}, "
            f"type_errors={results['type_errors']}"
        )

    def test_core_plugin_has_required_methods(self):
        """Test CorePlugin has all required methods."""
        required = PluginProtocolContract.REQUIRED_METHODS

        for method in required:
            assert hasattr(
                CorePlugin, method
            ), f"CorePlugin missing required method: {method}"

    def test_core_plugin_method_signatures(self):
        """Test CorePlugin method signatures are correct."""
        # Check register method
        assert callable(CorePlugin.register), "register must be callable"

        # Check unregister method
        assert callable(CorePlugin.unregister), "unregister must be callable"

        # Check health method
        assert callable(CorePlugin.health), "health must be callable"

    def test_core_plugin_attributes(self):
        """Test CorePlugin has required attributes."""
        # Check metadata attribute on class
        assert hasattr(
            CorePlugin, "metadata"
        ), "Plugin must have 'metadata' attribute"

        # Verify metadata has required fields
        metadata = CorePlugin.metadata
        assert hasattr(metadata, "name"), "Metadata must have 'name' field"
        assert isinstance(metadata.name, str), "Plugin name must be string"
        assert len(metadata.name) > 0, "Plugin name must not be empty"

        assert hasattr(metadata, "version"), "Metadata must have 'version' field"
        assert isinstance(metadata.version, str), "Plugin version must be string"

        assert hasattr(
            metadata, "description"
        ), "Metadata must have 'description' field"

    def test_core_plugin_initialize(self):
        """Test CorePlugin register method works."""
        plugin = CorePlugin()

        # Register should not raise (using mock registry)
        try:
            from unittest.mock import Mock
            mock_app = Mock()
            mock_registry = Mock()
            plugin.register(mock_app, mock_registry)
            # Registration should complete without error
        except Exception as e:
            pytest.fail(f"Plugin register failed: {e}")

    def test_core_plugin_shutdown(self):
        """Test CorePlugin unregister method works."""
        plugin = CorePlugin()

        # Unregister should not raise
        try:
            plugin.unregister()
            # Should complete without error
        except Exception as e:
            pytest.fail(f"Plugin unregister failed: {e}")

    def test_core_plugin_get_features(self):
        """Test CorePlugin health returns valid status."""
        plugin = CorePlugin()

        health_status = plugin.health()

        assert health_status is not None, "health must return status object"
        assert hasattr(health_status, "plugin_name"), "Health status must have plugin_name"
        assert hasattr(health_status, "healthy"), "Health status must have healthy flag"
        assert hasattr(health_status, "checked_at"), "Health status must have checked_at timestamp"

    def test_core_plugin_handle_event(self):
        """Test CorePlugin metadata contains capabilities."""
        # Check that metadata includes capabilities
        metadata = CorePlugin.metadata

        assert hasattr(metadata, "capabilities"), "Metadata should have capabilities"
        if metadata.capabilities:
            assert isinstance(metadata.capabilities, dict), (
                "Capabilities must be a dict"
            )

    def test_core_plugin_protocol_compliance(self):
        """Verify CorePlugin conforms to the Plugin protocol."""
        plugin = CorePlugin()
        assert isinstance(plugin, Plugin)
        assert isinstance(plugin.metadata, PluginMetadata)
        health_status = plugin.health()
        if health_status is not None:
            assert isinstance(health_status, PluginHealthStatus)

    def test_plugin_docstrings(self):
        """Test plugin methods have documentation."""
        plugin = CorePlugin()

        methods = ["register", "unregister", "health"]

        for method_name in methods:
            method = getattr(plugin, method_name)
            doc = inspect.getdoc(method)
            assert doc, f"Method {method_name} must have docstring"


class TestPluginCompatibility:
    """Test plugin compatibility and version requirements."""

    def test_plugin_version_format(self):
        """Test plugin version follows semantic versioning."""
        metadata = CorePlugin.metadata
        version = metadata.version
        parts = version.split(".")

        assert len(parts) >= 2, (
            f"Version must be semver (major.minor[.patch]): {version}"
        )

        for part in parts:
            assert part.isdigit() or (
                part[0].isdigit()
            ), f"Invalid version part: {part}"

    def test_plugin_name_valid(self):
        """Test plugin name is valid."""
        metadata = CorePlugin.metadata
        name = metadata.name

        assert name, "Plugin name must not be empty"
        assert isinstance(name, str), "Plugin name must be string"
        assert len(name) <= 100, "Plugin name too long"
        assert not name.startswith("_"), "Plugin name should not start with underscore"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
