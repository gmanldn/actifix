"""Tests for module execution context env filtering."""

import actifix.modules as modules


def test_module_context_filters_sensitive_env():
    secret_suffix = "1234567890abcdef1234567890abcdef"
    secret_value = "sk-" + secret_suffix
    env = {
        "PATH": f"/bin:{secret_value}",
        "HOME": "/tmp/home",
        "LANG": "en_US.UTF-8",
        "ACTIFIX_CHANGE_ORIGIN": "raise_af",
        "ACTIFIX_DATA_DIR": "/tmp/actifix-agent-123/actifix",
        "ACTIFIX_SECRET_REDACTION": "0",
        "SECRET_KEY": "should-not-leak",
        "OPENAI_API_KEY": secret_value,
        "ACTIFIX_AI_API_KEY": secret_value,
        "NORMAL": "not-allowed",
    }

    context = modules.get_module_context(env=env)

    assert "PATH" in context.env
    assert "HOME" in context.env
    assert "LANG" in context.env
    assert context.env["ACTIFIX_CHANGE_ORIGIN"] == "raise_af"
    assert context.env["ACTIFIX_DATA_DIR"] == "/tmp/actifix-agent-123/actifix"
    assert context.env["ACTIFIX_SECRET_REDACTION"] == "0"
    assert "SECRET_KEY" not in context.env
    assert "OPENAI_API_KEY" not in context.env
    assert "ACTIFIX_AI_API_KEY" not in context.env
    assert "NORMAL" not in context.env
    assert "***API_KEY_REDACTED***" in context.env["PATH"]
