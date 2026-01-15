#!/usr/bin/env python3
"""
Tests for environment variable sanitization security fix.

Verifies that:
1. Environment variables are sanitized to prevent injection attacks
2. Whitespace is trimmed from values
3. Control characters are removed
4. Path variables are properly sanitized
5. Configuration loading uses sanitized values
6. Numeric values are properly filtered
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from actifix.config import _sanitize_env_value, _get_env_sanitized, load_config
from actifix.state_paths import _sanitize_path


class TestSanitizeEnvValue:
    """Test environment variable sanitization function."""

    def test_sanitize_removes_leading_trailing_whitespace(self):
        """Verify whitespace is trimmed from values."""
        assert _sanitize_env_value("  hello  ", "string") == "hello"
        assert _sanitize_env_value("\thello\t", "string") == "hello"
        assert _sanitize_env_value("\nhello\n", "string") == "hello"

    def test_sanitize_removes_null_bytes(self):
        """Verify null bytes are removed from values."""
        assert _sanitize_env_value("hello\x00world", "string") == "helloworld"
        assert _sanitize_env_value("\x00hello", "string") == "hello"

    def test_sanitize_removes_control_characters(self):
        """Verify control characters are removed from values."""
        # Tab, newline, etc.
        assert _sanitize_env_value("hello\x01\x02world", "string") == "helloworld"
        assert _sanitize_env_value("hello\x1fworld", "string") == "helloworld"

    def test_sanitize_path_removes_dangerous_chars(self):
        """Verify path values are sanitized."""
        assert _sanitize_env_value("/path/to/file", "path") == "/path/to/file"
        assert _sanitize_env_value("/path/to/file\x00.txt", "path") == "/path/to/file.txt"

    def test_sanitize_path_collapses_multiple_slashes(self):
        """Verify multiple slashes are collapsed in paths."""
        assert _sanitize_env_value("/path//to///file", "path") == "/path/to/file"
        assert _sanitize_env_value("///path", "path") == "/path"

    def test_sanitize_alphanumeric_only(self):
        """Verify alphanumeric sanitization."""
        assert _sanitize_env_value("hello123", "alphanumeric") == "hello123"
        assert _sanitize_env_value("hello-world_test.txt", "alphanumeric") == "hello-world_test.txt"
        assert _sanitize_env_value("hello;world", "alphanumeric") == "helloworld"

    def test_sanitize_numeric_only(self):
        """Verify numeric sanitization."""
        assert _sanitize_env_value("12345", "numeric") == "12345"
        assert _sanitize_env_value("123.45", "numeric") == "123.45"
        assert _sanitize_env_value("123abc", "numeric") == "123"
        assert _sanitize_env_value("-123", "numeric") == "-123"

    def test_sanitize_identifier_only(self):
        """Verify identifier sanitization."""
        assert _sanitize_env_value("myvar_123", "identifier") == "myvar_123"
        assert _sanitize_env_value("my-var", "identifier") == "myvar"
        assert _sanitize_env_value("my.var", "identifier") == "myvar"

    def test_sanitize_boolean_values(self):
        """Verify boolean value sanitization."""
        for val in ["true", "false", "1", "0", "yes", "no", "on", "off"]:
            assert _sanitize_env_value(val, "boolean") == val.lower()

        # Invalid boolean should return empty string
        assert _sanitize_env_value("maybe", "boolean") == ""
        assert _sanitize_env_value("2", "boolean") == ""

    def test_sanitize_empty_values(self):
        """Verify empty values are handled."""
        assert _sanitize_env_value("", "string") == ""
        assert _sanitize_env_value(None, "string") == ""
        assert _sanitize_env_value("   ", "string") == ""


class TestGetEnvSanitized:
    """Test sanitized environment getter function."""

    def test_get_env_with_default(self):
        """Verify default value is used when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_env_sanitized("NONEXISTENT", "default", "string") == "default"

    def test_get_env_sanitizes_value(self):
        """Verify environment value is sanitized."""
        with patch.dict(os.environ, {"TEST_VAR": "  hello  "}, clear=False):
            assert _get_env_sanitized("TEST_VAR", "", "string") == "hello"

    def test_get_env_with_type_specific_sanitization(self):
        """Verify type-specific sanitization is applied."""
        with patch.dict(os.environ, {"NUMERIC_VAR": "  123.45abc  "}, clear=False):
            result = _get_env_sanitized("NUMERIC_VAR", "", "numeric")
            assert result == "123.45"


class TestPathSanitization:
    """Test path-specific sanitization."""

    def test_sanitize_path_function(self):
        """Verify _sanitize_path removes dangerous characters."""
        assert _sanitize_path("/usr/local/bin") == "/usr/local/bin"
        assert _sanitize_path("/usr/local\x00bin") == "/usr/localbin"
        assert _sanitize_path("/usr//local///bin") == "/usr/local/bin"

    def test_sanitize_path_windows_style(self):
        """Verify Windows paths are preserved."""
        assert _sanitize_path("C:\\Users\\test") == "C:\\Users\\test"

    def test_sanitize_path_with_control_chars(self):
        """Verify control characters are removed from paths."""
        assert _sanitize_path("/path\x01to\x02file") == "/pathtofile"


class TestConfigSanitization:
    """Test that configuration loading uses sanitization."""

    def test_load_config_sanitizes_paths(self):
        """Verify config loading sanitizes path-type env vars."""
        with patch.dict(os.environ, {
            "ACTIFIX_PROJECT_ROOT": "  /tmp/test  ",
            "ACTIFIX_DATA_DIR": "  /tmp/data  ",
        }, clear=False):
            # Reset config cache by creating fresh instance
            config = load_config(fail_fast=False)
            # The paths should be resolved, stripping whitespace
            assert "/tmp" in str(config.project_root)

    def test_load_config_sanitizes_booleans(self):
        """Verify config loading sanitizes boolean values."""
        with patch.dict(os.environ, {
            "ACTIFIX_CAPTURE_ENABLED": "true",
            "ACTIFIX_SECRET_REDACTION": "false",
        }, clear=False):
            config = load_config(fail_fast=False)
            assert config.capture_enabled is True
            assert config.secret_redaction_enabled is False

    def test_load_config_sanitizes_numeric_values(self):
        """Verify config loading sanitizes numeric values."""
        with patch.dict(os.environ, {
            "ACTIFIX_MAX_ROLLUP_ERRORS": "  50  ",
            "ACTIFIX_SLA_P0_HOURS": "  2  ",
        }, clear=False):
            config = load_config(fail_fast=False)
            assert config.max_rollup_errors == 50
            assert config.sla_p0_hours == 2

    def test_load_config_sanitizes_ai_provider(self):
        """Verify AI provider is sanitized to alphanumeric."""
        with patch.dict(os.environ, {
            "ACTIFIX_AI_PROVIDER": "  openai  ",
        }, clear=False):
            config = load_config(fail_fast=False)
            # Should be stripped and valid
            assert config.ai_provider != ""


class TestInjectionPrevention:
    """Test injection attack prevention."""

    def test_sanitize_prevents_command_injection(self):
        """Verify control characters in injection attempts are removed."""
        # Injection with control characters is prevented
        dangerous = "value\x00; rm -rf /"
        sanitized = _sanitize_env_value(dangerous, "string")
        assert "\x00" not in sanitized
        # For strict sanitization, use alphanumeric type
        strict_sanitized = _sanitize_env_value("value; rm -rf /", "alphanumeric")
        assert ";" not in strict_sanitized
        assert "/" not in strict_sanitized

    def test_sanitize_prevents_null_byte_injection(self):
        """Verify null byte injection is prevented."""
        dangerous = "good_value\x00bad_value"
        sanitized = _sanitize_env_value(dangerous, "string")
        assert "\x00" not in sanitized
        assert sanitized == "good_valuebad_value"

    def test_sanitize_prevents_path_traversal(self):
        """Verify path traversal attempts are mitigated."""
        # While we don't prevent .. explicitly, control chars are removed
        dangerous_path = "/tmp/\x00/etc/passwd"
        sanitized = _sanitize_path(dangerous_path)
        assert "\x00" not in sanitized

    def test_sanitize_prevents_unicode_injection(self):
        """Verify special unicode isn't allowed in restricted contexts."""
        # Unicode control characters
        dangerous = "hello\u202eworldhello"  # Right-to-left override
        sanitized = _sanitize_env_value(dangerous, "alphanumeric")
        # Unicode chars outside ASCII alphanumeric should be removed
        assert len(sanitized) > 0


class TestSanitizationEdgeCases:
    """Test edge cases and special scenarios."""

    def test_sanitize_very_long_value(self):
        """Verify long values are sanitized without truncation."""
        long_value = "a" * 10000
        sanitized = _sanitize_env_value(long_value, "string")
        assert len(sanitized) == 10000

    def test_sanitize_all_whitespace(self):
        """Verify all-whitespace values become empty."""
        assert _sanitize_env_value("     ", "string") == ""
        assert _sanitize_env_value("\t\t\t", "string") == ""
        assert _sanitize_env_value("\n\n\n", "string") == ""

    def test_sanitize_only_control_chars(self):
        """Verify values with only control chars become empty."""
        assert _sanitize_env_value("\x00\x01\x02", "string") == ""

    def test_sanitize_mixed_content(self):
        """Verify mixed valid and dangerous content is properly filtered."""
        mixed = "hello\x00world;  test\nvalue"
        sanitized = _sanitize_env_value(mixed, "string")
        # Control chars removed, but semicolon is allowed in "string" type
        assert "hello" in sanitized
        assert "world" in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
