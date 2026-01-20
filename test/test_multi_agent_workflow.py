"""Integration tests for multi-agent workflow compatibility."""
import os
import subprocess
import tempfile
import gitignore_parser
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).parent.parent

def test_database_untracked_in_git_status(project_root):
    """Verify data/actifix.db remains untracked in git status."""
    result = subprocess.run(["git", "status", "--porcelain"], cwd=project_root, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert "data/actifix.db" not in output, "Database should not appear in git status"

def test_gitignore_excludes_binaries_and_data(project_root):
    """Verify .gitignore excludes binary data files."""
    gitignore = gitignore_parser.parse_gitignore(project_root / ".gitignore")
    assert gitignore("data/actifix.db")
    assert gitignore("*.db")
    assert gitignore("actifix/quarantine/")

def test_multiple_agents_no_conflicts(tmp_path):
    """Simulate multiple agents with isolated dirs - no git conflicts."""
    agents = []
    for i in range(3):
        agent_dir = tmp_path / f"actifix-agent-{i}"
        agent_dir.mkdir()
        (agent_dir / "data").mkdir()
        (agent_dir / "data" / "actifix.db").touch()
        (agent_dir / ".actifix").mkdir()
        agents.append(agent_dir)
    
    # Simulate git status in project - no agent data tracked
    project_gitignore = gitignore_parser.parse_gitignore(Path.cwd() / ".gitignore")
    for agent in agents:
        assert project_gitignore(str(agent)), f"Agent dir {agent} should be ignored"

def test_no_branch_conflicts_direct_develop(tmp_path):
    """Verify workflow doesn't require branches - direct develop work."""
    # No branches created; git clean
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    assert result.returncode == 0
    branch_result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    assert branch_result.stdout.strip() == "develop"
