"""Tests for start.py surfacing API-hosted modules."""

from __future__ import annotations


def test_start_surfaces_expected_api_module_paths():
    from scripts import start

    assert start.API_MODULE_HEALTH_PATHS["Hollogram"] == "/modules/hollogram/health"
    assert start.API_MODULE_HEALTH_PATHS["Dev_Assistant"] == "/modules/dev-assistant/health"

