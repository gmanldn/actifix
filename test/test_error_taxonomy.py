#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the enhanced Actifix error taxonomy/classification helpers.
"""

import importlib
from dataclasses import replace

import pytest

from actifix.error_taxonomy import (
    ErrorCategory,
    ErrorPattern,
    ErrorSeverity,
    add_custom_pattern,
    classify_error,
    get_error_patterns,
)
from actifix.raise_af import TicketPriority


@pytest.fixture(autouse=True)
def reset_classifier():
    """Reset the global classifier between tests to avoid cross-test pollution."""
    module = importlib.import_module("actifix.error_taxonomy")
    module._classifier = None
    yield
    module._classifier = None


def test_classify_system_crash_pattern():
    """A fatal SystemError should match the system crash pattern."""
    result = classify_error("SystemError", "Fatal crash caused by segmentation fault")
    assert result["category"] == ErrorCategory.SYSTEM.value
    assert result["severity"] == ErrorSeverity.CRITICAL.value
    assert result["priority"] == TicketPriority.P0
    assert "Restart system immediately" in result["remediation_hints"]
    assert result["classification_confidence"] == "high"


def test_classify_fallback_connection():
    """Fallback logic should classify unknown errors mentioning the network."""
    result = classify_error("NetworkDrop", "Service became unreachable without specific keywords")
    assert result["category"] == ErrorCategory.NETWORK.value
    assert result["severity"] == ErrorSeverity.HIGH.value
    assert result["priority"] == TicketPriority.P1
    assert "Check network connectivity" in result["remediation_hints"]


def test_add_custom_pattern_precedence():
    """Custom patterns should take precedence over built-in fallback logic."""
    pattern = ErrorPattern(
        name="custom_integration",
        category=ErrorCategory.INTEGRATION,
        severity=ErrorSeverity.HIGH,
        priority=TicketPriority.P1,
        keywords=["custom fail"],
        regex_patterns=[r"custom error"],
        description="Custom pattern",
        remediation_hints=["Check custom integration"],
    )

    add_custom_pattern(pattern)

    result = classify_error(
        "CustomError",
        "The custom error always says custom error and custom fail"
    )

    assert result["category"] == ErrorCategory.INTEGRATION.value
    assert result["severity"] == ErrorSeverity.HIGH.value
    assert result["priority"] == TicketPriority.P1
    assert "Check custom integration" in result["remediation_hints"]


def test_get_error_patterns_contains_defaults():
    """Ensure the default patterns are exposed through the accessor."""
    patterns = get_error_patterns()
    assert any(p.name == "system_crash" for p in patterns)
    assert any(p.name == "database_connection" for p in patterns)
