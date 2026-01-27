import json
import os
from pathlib import Path

import pytest


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        return False


class DummyManager:
    def retrieve_credential(self, name: str) -> str:
        assert name == "github_token"
        return "ghp_dummy-token"


def _prepare_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(tmp_path / ".actifix"))
    monkeypatch.setenv("ACTIFIX_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("ACTIFIX_GITHUB_REPO", "owner/repo")


def test_github_issue_sync_creates_issue(tmp_path, monkeypatch):
    _prepare_env(monkeypatch, tmp_path)

    monkeypatch.setattr(
        "actifix.security.credentials.get_credential_manager",
        lambda: DummyManager(),
    )

    def fake_urlopen(request, timeout: int):
        return DummyResponse({"number": 123, "html_url": "https://github.com/owner/repo/issues/123"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    from actifix import enable_actifix_capture, record_error
    from actifix.persistence.ticket_repo import get_ticket_repository
    from scripts.github_issue_sync import main as github_sync_main

    enable_actifix_capture()
    entry = record_error(
        error_type="GitHubSyncTest",
        message="Test ticket for GitHub sync",
        source="test/test_github_sync.py:1",
        priority="P0",
    )

    assert entry is not None

    rc = github_sync_main(["--tickets", entry.ticket_id])
    assert rc == 0

    repo = get_ticket_repository()
    ticket = repo.get_ticket(entry.ticket_id)
    assert ticket is not None
    assert ticket["github_issue_number"] == 123
    assert ticket["github_issue_url"] == "https://github.com/owner/repo/issues/123"
    assert ticket["github_sync_state"] == "synced"
    assert ticket["github_sync_message"].startswith("Synced at")


def test_github_issue_sync_dry_run(tmp_path, monkeypatch):
    _prepare_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "actifix.security.credentials.get_credential_manager",
        lambda: DummyManager(),
    )
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: DummyResponse({"number": 321, "html_url": "ignore"}))

    from actifix import enable_actifix_capture, record_error
    from actifix.persistence.ticket_repo import get_ticket_repository
    from scripts.github_issue_sync import main as github_sync_main

    enable_actifix_capture()
    entry = record_error(
        error_type="GitHubSyncTest",
        message="Dry-run ticket",
        source="test/test_github_sync.py:2",
        priority="P1",
    )

    rc = github_sync_main(["--tickets", entry.ticket_id, "--dry-run"])
    assert rc == 0

    repo = get_ticket_repository()
    ticket = repo.get_ticket(entry.ticket_id)
    assert ticket is not None
    # Dry run should leave sync state untouched
    assert ticket["github_sync_state"] in (None, "", "pending")
