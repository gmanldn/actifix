"""Tests for ModuleRegistry status persistence."""

from __future__ import annotations

import json

from actifix.modules.registry import (
    ModuleRegistry,
    ModuleRuntimeContext,
    _read_module_status_payload,
)


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


def test_module_registry_clears_error_status_on_registration(tmp_path):
    """Verify error status is cleared when module successfully registers."""
    status_file = tmp_path / "module_statuses.json"
    registry = ModuleRegistry(project_root=tmp_path, status_file=status_file)

    module_id = "modules.test_module"

    # Simulate a previous failed registration by marking module as error
    registry.mark_status(module_id, "error")
    assert registry.get_status(module_id) == "error"

    # Create a mock module and context
    class MockModule:
        pass

    context = ModuleRuntimeContext(
        module_name="test_module",
        module_id=module_id,
        module_path="test/module",
        project_root=str(tmp_path),
        host="127.0.0.1",
        port=9999,
    )

    # Simulate successful registration
    registry.on_registered(MockModule(), context, app=None, blueprint=None)

    # Verify error status was cleared and module is now active
    assert registry.get_status(module_id) == "active"
    payload = _read_module_status_payload(status_file)
    assert module_id in payload["statuses"]["active"]
    assert module_id not in payload["statuses"]["error"]
