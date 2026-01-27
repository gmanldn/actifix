"""Tests for module config defaults and overrides."""

import json

import pytest

from actifix.modules import get_module_config
from actifix.modules import yahtzee, superquiz


def test_module_config_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    config = get_module_config(
        "yahtzee",
        {"host": "127.0.0.1", "port": 8000},
        project_root=str(tmp_path),
    )
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 8000


def test_module_config_override(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv(
        "ACTIFIX_MODULE_CONFIG_OVERRIDES",
        json.dumps({"yahtzee": {"port": 9101}}),
    )
    config = get_module_config(
        "yahtzee",
        {"host": "127.0.0.1", "port": 8000},
        project_root=str(tmp_path),
    )
    assert config["port"] == 9101
    assert config["host"] == "127.0.0.1"


def test_modules_use_config_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv(
        "ACTIFIX_MODULE_CONFIG_OVERRIDES",
        json.dumps(
            {
                "yahtzee": {"port": 9102, "host": "127.0.0.2"},
                "superquiz": {"port": 9103},
            }
        ),
    )
    host, port = yahtzee._resolve_module_config(str(tmp_path), None, None)
    assert host == "127.0.0.2"
    assert port == 9102

    host, port = superquiz._resolve_module_config(str(tmp_path), None, None)
    assert host == "127.0.0.1"
    assert port == 9103
