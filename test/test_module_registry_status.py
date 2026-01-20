"""Tests for ModuleRegistry status persistence."""

from __future__ import annotations

import json

from actifix.modules.registry import ModuleRegistry, _read_module_status_payload


def test_module_registry_status_transitions(tmp_path):
    status_file = tmp_path / "module_statuses.json"
    registry = ModuleRegistry(project_root=tmp_path, status_file=status_file)

    assert registry.get_status("modules.test") == "active"

    registry.mark_status("modules.test", "disabled")
    assert registry.get_status("modules.test") == "disabled"

    registry.mark_status("modules.test", "active")
    assert registry.get_status("modules.test") == "active"

    payload = _read_module_status_payload(status_file)
    assert "modules.test" in payload["statuses"]["active"]
