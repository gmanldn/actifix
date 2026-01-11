from pathlib import Path

import pytest

from actifix.raise_af import enforce_raise_af_only
from actifix.state_paths import get_actifix_paths, init_actifix_files


AGENT_FILES = ["AGENTS.md"]


def test_agent_instructions_remind_raise_af_usage():
    for path in AGENT_FILES:
        content = Path(path).read_text()
        assert "All Changes Must Start via Raise_AF" in content
        assert "Raise_AF" in content
        assert "actifix.raise_af.record_error" in content


def test_readme_documents_raise_af_ticket_flow():
    readme = Path("README.md").read_text()
    assert "Raise_AF Ticketing Requirement" in readme
    assert "actifix.raise_af.record_error" in readme
    assert "actifix.db" in readme or "SQLite" in readme


def test_enforce_raise_af_blocks_missing_origin(monkeypatch, tmp_path):
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    monkeypatch.setenv("ACTIFIX_ENFORCE_RAISE_AF", "1")
    monkeypatch.delenv("ACTIFIX_CHANGE_ORIGIN", raising=False)

    with pytest.raises(PermissionError):
        enforce_raise_af_only(paths)
