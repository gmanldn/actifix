"""Tests for module sandboxing on registration failures."""

import json

import pytest

import actifix.api as api


def test_module_registration_failure_marks_error(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    import actifix.modules.yhatzee as yhatzee

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(yhatzee, "create_blueprint", boom)

    app = api.create_app(project_root=tmp_path)
    assert app is not None

    status_file = tmp_path / ".actifix" / "module_statuses.json"
    assert status_file.exists()

    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert "modules.yhatzee" in data["statuses"]["error"]
