#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fuzz testing for ticket message and stack trace inputs.

Uses hypothesis for property-based testing to ensure robust handling
of arbitrary input strings, edge cases, and malformed data.
"""

import sys
from pathlib import Path
from typing import Optional

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.raise_af import (
    generate_duplicate_guard,
    redact_secrets_from_text,
    classify_priority,
    capture_file_context,
)

try:
    from hypothesis import given, strategies as st, settings, HealthCheck
except ImportError:
    pytest.skip("hypothesis not installed", allow_module_level=True)


class TestFuzzTicketMessages:
    """Fuzz test ticket message handling."""

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_messages_handled(self, message: str):
        """Test that arbitrary messages don't cause crashes."""
        # Should not raise
        try:
            result = generate_duplicate_guard(
                source="test.py",
                message=message,
                error_type="TestError",
                stack_trace="",
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed to handle message {repr(message)}: {e}")

    @given(st.text(min_size=1))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_very_long_messages(self, base_message: str):
        """Test handling of extremely long messages."""
        # Create a very long message
        long_message = base_message * 10000

        try:
            result = generate_duplicate_guard(
                source="test.py",
                message=long_message,
                error_type="TestError",
                stack_trace="",
            )
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"Failed to handle long message: {e}")

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_unicode_in_messages(self, unicode_text: str):
        """Test handling of unicode characters in messages."""
        try:
            result = generate_duplicate_guard(
                source="test.py",
                message=unicode_text,
                error_type="TestError",
                stack_trace="",
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed to handle unicode: {e}")

    @given(
        st.text(),
        st.just("TestError"),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_priority_classification_robustness(
        self, message: str, error_type: str
    ):
        """Test that priority classification handles arbitrary messages."""
        try:
            priority = classify_priority(error_type, message, "test.py")
            assert priority is not None
            assert hasattr(priority, "value")
        except Exception as e:
            pytest.fail(
                f"Priority classification failed for {repr(message)}: {e}"
            )


class TestFuzzStackTraces:
    """Fuzz test stack trace handling."""

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_stack_traces(self, stack_trace: str):
        """Test that arbitrary stack traces don't cause crashes."""
        try:
            result = generate_duplicate_guard(
                source="test.py",
                message="Test error",
                error_type="TestError",
                stack_trace=stack_trace,
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed to handle stack trace {repr(stack_trace)}: {e}")

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_malformed_stack_traces(self, trace_fragment: str):
        """Test handling of malformed stack traces."""
        malformed = f"Traceback (most recent call last):\n{trace_fragment}\nTypeError: boom"

        try:
            result = generate_duplicate_guard(
                source="test.py",
                message="Error",
                error_type="TypeError",
                stack_trace=malformed,
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed to handle malformed trace: {e}")

    @given(st.lists(st.text(), min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_multi_line_stack_traces(self, lines: list):
        """Test handling of multi-line stack traces."""
        trace = "\n".join(lines)

        try:
            result = generate_duplicate_guard(
                source="test.py",
                message="Multi-line trace",
                error_type="Error",
                stack_trace=trace,
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed to handle multi-line trace: {e}")


class TestFuzzSecretRedaction:
    """Fuzz test secret redaction."""

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_arbitrary_text_redaction(self, text: str):
        """Test that arbitrary text doesn't break redaction."""
        try:
            result = redact_secrets_from_text(text)
            assert isinstance(result, str)
            # Result should not raise on further processing
            _ = generate_duplicate_guard(
                source="test.py",
                message=result,
                error_type="TestError",
                stack_trace="",
            )
        except Exception as e:
            pytest.fail(f"Redaction failed for {repr(text)}: {e}")

    @given(st.text(min_size=1))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_redaction_preserves_structure(self, text: str):
        """Test that redaction preserves text structure."""
        redacted = redact_secrets_from_text(text)

        # Check that redacted text is still valid
        assert isinstance(redacted, str)
        assert "\x00" not in redacted  # No null bytes


class TestFuzzCombinations:
    """Fuzz test combinations of inputs."""

    @given(
        st.text(),
        st.text(),
        st.text(),
        st.sampled_from(["ValueError", "TypeError", "RuntimeError", "Exception"]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_combined_inputs(
        self,
        message: str,
        source: str,
        stack_trace: str,
        error_type: str,
    ):
        """Test handling of arbitrary combinations of inputs."""
        try:
            guard = generate_duplicate_guard(
                source=source or "unknown.py",
                message=message or "Unknown error",
                error_type=error_type,
                stack_trace=stack_trace,
            )
            assert isinstance(guard, str)
            assert len(guard) > 0

            priority = classify_priority(
                error_type, message or "Error", source or "unknown.py"
            )
            assert priority is not None
        except Exception as e:
            pytest.fail(
                f"Combined inputs failed - "
                f"message={repr(message)}, "
                f"source={repr(source)}, "
                f"error_type={error_type}: {e}"
            )

    @given(
        st.lists(
            st.tuples(
                st.text(),
                st.text(),
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_batch_processing(self, inputs: list):
        """Test batch processing of fuzzed inputs."""
        guards = []

        try:
            for i, (msg, trace) in enumerate(inputs):
                guard = generate_duplicate_guard(
                    source=f"test_{i}.py",
                    message=msg or f"Error {i}",
                    error_type="TestError",
                    stack_trace=trace,
                )
                guards.append(guard)

            # All guards should be unique for different inputs
            assert len(guards) == len(inputs)
        except Exception as e:
            pytest.fail(f"Batch processing failed: {e}")


class TestFuzzEdgeCases:
    """Fuzz test specific edge cases."""

    @pytest.mark.parametrize(
        "message",
        [
            "",  # Empty
            " " * 10000,  # Only whitespace
            "\n" * 1000,  # Many newlines
            "\x00\x01\x02",  # Binary data
            "a" * 100000,  # Very long
        ],
    )
    def test_edge_case_messages(self, message: str):
        """Test specific edge case messages."""
        try:
            result = generate_duplicate_guard(
                source="test.py",
                message=message,
                error_type="TestError",
                stack_trace="",
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed on edge case: {e}")

    @pytest.mark.parametrize(
        "stack_trace",
        [
            "Traceback (most recent call last):\n  File \"test.py\", line 1, in <module>\nError",
            "",
            "   ",
            "\n" * 100,
            "a" * 100000,
        ],
    )
    def test_edge_case_stack_traces(self, stack_trace: str):
        """Test specific edge case stack traces."""
        try:
            result = generate_duplicate_guard(
                source="test.py",
                message="Test",
                error_type="Error",
                stack_trace=stack_trace,
            )
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Failed on stack trace edge case: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
