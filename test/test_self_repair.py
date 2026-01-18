#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the self-repair blueprint manager."""

from actifix.self_repair import describe_task, SelfRepairManager


def test_describe_task_includes_blueprint_details():
    description = describe_task("Auto-detect and repair database corruption")
    assert "Auto-detect" in description
    assert "Monitor the SQLite journal" in description


def test_describe_task_missing_blueprint():
    assert describe_task("Nonexistent recovery plan") == "Self-repair blueprint not found. Refer to documentation for manual remediation."


def test_self_repair_manager_finds_blueprint_by_name():
    manager = SelfRepairManager()
    blueprint = manager.find_blueprint("Automatic connection pool recovery")
    assert blueprint is not None
    assert blueprint.category == "Self-Healing Database"