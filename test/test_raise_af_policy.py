from pathlib import Path


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
    assert "actifix/ACTIFIX-LIST.md" in readme
