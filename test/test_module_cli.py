"""Tests for module CLI management commands."""

import json
from pathlib import Path

import pytest

import actifix.main as main
from actifix.state_paths import get_actifix_paths, init_actifix_files


def _write_depgraph(project_root: Path) -> None:
    arch_dir = project_root / "docs" / "architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)
    depgraph = {
        "nodes": [
            {"id": "modules.yahtzee", "domain": "modules", "owner": "modules", "label": "yahtzee"},
            {"id": "modules.superquiz", "domain": "modules", "owner": "modules", "label": "superquiz"},
        ],
        "edges": [],
    }
    (arch_dir / "DEPGRAPH.json").write_text(json.dumps(depgraph), encoding="utf-8")


def test_modules_list_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    init_actifix_files(get_actifix_paths(project_root=tmp_path))
    _write_depgraph(tmp_path)

    code = main.main(["--project-root", str(tmp_path), "modules", "list"])
    captured = capsys.readouterr()

    assert code == 0
    assert "modules.yahtzee" in captured.out
    assert "modules.superquiz" in captured.out


def test_modules_enable_disable(tmp_path, monkeypatch):
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    init_actifix_files(get_actifix_paths(project_root=tmp_path))

    code = main.main(["--project-root", str(tmp_path), "modules", "disable", "modules.yahtzee"])
    assert code == 0

    status_file = tmp_path / ".actifix" / "module_statuses.json"
    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert "modules.yahtzee" in data["statuses"]["disabled"]

    code = main.main(["--project-root", str(tmp_path), "modules", "enable", "modules.yahtzee"])
    assert code == 0

    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert "modules.yahtzee" in data["statuses"]["active"]
