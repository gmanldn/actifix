"""Tests for module error log redaction."""

import importlib

import pytest


@pytest.mark.parametrize(
    "module_path",
    ["actifix.modules.yahtzee", "actifix.modules.superquiz"],
)
def test_module_error_redaction(monkeypatch, module_path):
    module = importlib.import_module(module_path)
    captured = {}

    def fake_record_error(*_args, **kwargs):
        captured["message"] = kwargs.get("message")

    monkeypatch.setattr(module, "record_error", fake_record_error)

    secret_suffix = "1234567890abcdef1234567890abcdef"
    secret_value = "sk-" + secret_suffix
    module._record_module_error(
        message="Failed with " + secret_value,
        source="modules.test",
        run_label="module-test",
        error_type="ValueError",
        priority=module.TicketPriority.P2,
    )

    assert "***API_KEY_REDACTED***" in captured["message"]
