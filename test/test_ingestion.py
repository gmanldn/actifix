"""
Tests for Sentry-style error ingestion.
"""

import json
import os
import pytest

from actifix.ingestion import (
    ingest_sentry_event,
    _parse_sentry_level,
    _extract_source_location,
    _extract_error_message,
    _extract_error_type,
    _extract_stack_trace,
)
from actifix.raise_af import TicketPriority


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for ingestion tests."""
    # Ensure ACTIFIX_CHANGE_ORIGIN is set
    os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
    yield
    # Cleanup not needed as env persists for test session


def test_parse_sentry_level():
    """Test Sentry level to priority mapping."""
    assert _parse_sentry_level("fatal") == TicketPriority.P0
    assert _parse_sentry_level("error") == TicketPriority.P1
    assert _parse_sentry_level("warning") == TicketPriority.P2
    assert _parse_sentry_level("info") == TicketPriority.P3
    assert _parse_sentry_level("debug") == TicketPriority.P4

    # Case insensitive
    assert _parse_sentry_level("FATAL") == TicketPriority.P0
    assert _parse_sentry_level("Error") == TicketPriority.P1

    # Unknown defaults to P2
    assert _parse_sentry_level("unknown") == TicketPriority.P2


def test_extract_source_location_from_stacktrace():
    """Test source location extraction from exception stacktrace."""
    event = {
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "app.py",
                                "lineno": 42,
                                "function": "main",
                            }
                        ]
                    }
                }
            ]
        }
    }

    source = _extract_source_location(event)
    assert source == "app.py:42"


def test_extract_source_location_from_culprit():
    """Test source location extraction from culprit field."""
    event = {
        "culprit": "views.index"
    }

    source = _extract_source_location(event)
    assert source == "views.index"


def test_extract_source_location_fallback():
    """Test source location fallback to platform."""
    event = {
        "platform": "python"
    }

    source = _extract_source_location(event)
    assert source == "python:ingestion"


def test_extract_error_message_from_message():
    """Test error message extraction from message field."""
    event = {
        "message": "Something went wrong"
    }

    message = _extract_error_message(event)
    assert message == "Something went wrong"


def test_extract_error_message_from_exception():
    """Test error message extraction from exception value."""
    event = {
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "Invalid input"
                }
            ]
        }
    }

    message = _extract_error_message(event)
    assert message == "ValueError: Invalid input"


def test_extract_error_type_from_exception():
    """Test error type extraction from exception."""
    event = {
        "exception": {
            "values": [
                {
                    "type": "TypeError",
                    "value": "Expected string"
                }
            ]
        }
    }

    error_type = _extract_error_type(event)
    assert error_type == "TypeError"


def test_extract_error_type_fallback():
    """Test error type fallback to platform.level."""
    event = {
        "level": "error",
        "platform": "javascript"
    }

    error_type = _extract_error_type(event)
    assert error_type == "javascript.error"


def test_extract_stack_trace():
    """Test stack trace extraction."""
    event = {
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "test.py",
                                "lineno": 10,
                                "function": "foo",
                                "context_line": "    result = bar()",
                            },
                            {
                                "filename": "test.py",
                                "lineno": 20,
                                "function": "bar",
                                "context_line": "    raise ValueError('oops')",
                            }
                        ]
                    }
                }
            ]
        }
    }

    stack_trace = _extract_stack_trace(event)

    assert stack_trace is not None
    assert "test.py" in stack_trace
    assert "line 10" in stack_trace
    assert "foo" in stack_trace
    assert "result = bar()" in stack_trace
    assert "line 20" in stack_trace
    assert "bar" in stack_trace


def test_ingest_sentry_event_basic():
    """Test basic Sentry event ingestion - parsing only."""
    event = {
        "event_id": "test-event-123",
        "platform": "python",
        "level": "error",
        "message": "Test error message from ingestion test",
        "environment": "production",
        "server_name": "web-1",
    }

    # Test that parsing functions work correctly
    message = _extract_error_message(event)
    assert message == "Test error message from ingestion test"

    source = _extract_source_location(event)
    assert source == "python:ingestion"

    error_type = _extract_error_type(event)
    assert error_type == "python.error"

    priority = _parse_sentry_level(event["level"])
    assert priority == TicketPriority.P1


def test_ingest_sentry_event_with_exception():
    """Test Sentry event ingestion with exception details - parsing only."""
    event = {
        "event_id": "test-event-456-ingestion",
        "platform": "python",
        "level": "fatal",
        "environment": "production",
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "Invalid configuration from ingestion test",
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "config.py",
                                "lineno": 100,
                                "function": "load_config",
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Test parsing functions
    message = _extract_error_message(event)
    assert "ValueError" in message
    assert "Invalid configuration" in message

    source = _extract_source_location(event)
    assert source == "config.py:100"

    error_type = _extract_error_type(event)
    assert error_type == "ValueError"

    priority = _parse_sentry_level(event["level"])
    assert priority == TicketPriority.P0


def test_ingest_sentry_event_parsing_complete():
    """Test complete parsing pipeline for Sentry event."""
    event = {
        "event_id": "test-event-789",
        "platform": "javascript",
        "level": "warning",
        "environment": "staging",
        "server_name": "app-server-2",
        "exception": {
            "values": [
                {
                    "type": "ReferenceError",
                    "value": "undefined is not defined",
                }
            ]
        }
    }

    # Test all extraction functions work together
    message = _extract_error_message(event)
    assert "ReferenceError" in message

    source = _extract_source_location(event)
    assert isinstance(source, str)

    error_type = _extract_error_type(event)
    assert error_type == "ReferenceError"

    priority = _parse_sentry_level(event["level"])
    assert priority == TicketPriority.P2


def test_ingest_sentry_event_different_levels():
    """Test ingestion with different severity levels."""
    for level in ["fatal", "error", "warning", "info", "debug"]:
        event = {
            "event_id": f"test-{level}-event",
            "platform": "python",
            "level": level,
            "message": f"Test {level} message",
        }

        ticket_id = ingest_sentry_event(event)
        # All should create tickets (unless duplicate)
        # Just verifying it doesn't crash
        assert isinstance(ticket_id, (str, type(None)))
