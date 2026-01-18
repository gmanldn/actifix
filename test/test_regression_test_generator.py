#!/usr/bin/env python3
"""Tests for regression test generator helpers."""

from __future__ import annotations

from scripts.regression_test_generator import build_regression_test_content


def test_build_regression_test_content_includes_ticket_details():
    ticket = {
        "id": "ACT-TEST-123",
        "message": "Sample regression issue",
        "source": "module.py:42",
    }
    content = build_regression_test_content(ticket)

    assert "ACT-TEST-123" in content
    assert "Sample regression issue" in content
    assert "module.py:42" in content
