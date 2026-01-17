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


class PluginProtocolContract:
    """Defines the expected contract for Plugin implementations."""

    REQUIRED_METHODS = {
        "name",
        "version",
        "initialize",
        "shutdown",
        "get_features",
        "handle_event",
    }

    REQUIRED_ATTRIBUTES = {
        "name",
        "version",
        "description",
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
        # Check initialize method
        assert callable(CorePlugin.initialize), "initialize must be callable"

        # Check shutdown method
        assert callable(CorePlugin.shutdown), "shutdown must be callable"

        # Check get_features method
        assert callable(CorePlugin.get_features), "get_features must be callable"

        # Check handle_event method
        assert callable(CorePlugin.handle_event), "handle_event must be callable"

    def test_core_plugin_attributes(self):
        """Test CorePlugin has required attributes."""
        # Create instance to test attributes
        plugin = CorePlugin()

        assert hasattr(
            plugin, "name"
        ), "Plugin must have 'name' attribute"
        assert isinstance(plugin.name, str), "Plugin name must be string"
        assert len(plugin.name) > 0, "Plugin name must not be empty"

        assert hasattr(
            plugin, "version"
        ), "Plugin must have 'version' attribute"
        assert isinstance(plugin.version, str), "Plugin version must be string"

        assert hasattr(
            plugin, "description"
        ), "Plugin must have 'description' attribute"

    def test_core_plugin_initialize(self):
        """Test CorePlugin initialize method works."""
        plugin = CorePlugin()

        # Initialize should not raise
        try:
            result = plugin.initialize()
            # Should return truthy value or None
            assert result is None or result
        except Exception as e:
            pytest.fail(f"Plugin initialize failed: {e}")

    def test_core_plugin_shutdown(self):
        """Test CorePlugin shutdown method works."""
        plugin = CorePlugin()

        # Shutdown should not raise
        try:
            result = plugin.shutdown()
            # Should return truthy value or None
            assert result is None or result
        except Exception as e:
            pytest.fail(f"Plugin shutdown failed: {e}")

    def test_core_plugin_get_features(self):
        """Test CorePlugin get_features returns valid feature list."""
        plugin = CorePlugin()

        features = plugin.get_features()

        assert isinstance(features, (list, dict)), (
            "get_features must return list or dict"
        )

        if isinstance(features, list):
            for feature in features:
                assert isinstance(feature, str), (
                    "Features must be strings"
                )

        if isinstance(features, dict):
            for key, value in features.items():
                assert isinstance(key, str), "Feature keys must be strings"

    def test_core_plugin_handle_event(self):
        """Test CorePlugin handle_event accepts events."""
        plugin = CorePlugin()

        # Should accept various event types
        test_events = [
            {"type": "error", "data": "test"},
            {"type": "warning", "message": "warning"},
            {"type": "info"},
        ]

        for event in test_events:
            try:
                result = plugin.handle_event(event)
                # Should not raise
                assert result is None or isinstance(result, (bool, dict))
            except Exception as e:
                pytest.fail(f"Failed to handle event {event}: {e}")

    def test_plugin_docstrings(self):
        """Test plugin methods have documentation."""
        plugin = CorePlugin()

        methods = ["initialize", "shutdown", "get_features", "handle_event"]

        for method_name in methods:
            method = getattr(plugin, method_name)
            doc = inspect.getdoc(method)
            assert doc, f"Method {method_name} must have docstring"


class TestPluginCompatibility:
    """Test plugin compatibility and version requirements."""

    def test_plugin_version_format(self):
        """Test plugin version follows semantic versioning."""
        plugin = CorePlugin()

        version = plugin.version
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
        plugin = CorePlugin()

        name = plugin.name

        assert name, "Plugin name must not be empty"
        assert isinstance(name, str), "Plugin name must be string"
        assert len(name) <= 100, "Plugin name too long"
        assert not name.startswith("_"), "Plugin name should not start with underscore"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
