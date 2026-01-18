#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Actifix API endpoints.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.api import create_app
from actifix.persistence.database import reset_database_pool
from actifix.persistence.ticket_repo import (
    get_ticket_repository,
    reset_ticket_repository,
)
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files
from actifix.log_utils import log_event


def _write_log(paths):
    log_event(
        "TICKET_COMPLETED",
        "Completed via API",
        ticket_id="ACT-1",
        level="SUCCESS",
    )
    log_event(
        "ASCII_BANNER",
        "✓ Banner line",
        ticket_id="ACT-1",
    )


def _build_ticket(ticket_id, priority=TicketPriority.P2):
    return ActifixEntry(
        message="api ticket",
        source="api.tests:1",
        run_label="api",
        entry_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type="APITest",
        stack_trace="",
        duplicate_guard=f"{ticket_id}-guard",
    )


@pytest.fixture
def api_workspace(tmp_path, monkeypatch):
    base = tmp_path
    data_dir = base / "actifix"
    state_dir = base / ".actifix"
    db_dir = base / "data"
    logs_dir = base / "logs"
    arch_dir = base / "Arch"

    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(db_dir / "actifix.db"))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_AI_PROVIDER", "openai")
    monkeypatch.setenv("ACTIFIX_AI_API_KEY", "sk-api")
    monkeypatch.setenv("ACTIFIX_AI_MODEL", "gpt-4")
    monkeypatch.setenv("ACTIFIX_AI_ENABLED", "1")

    paths = get_actifix_paths(project_root=base)
    init_actifix_files(paths)

    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "Actifix" / "dummy").mkdir(parents=True, exist_ok=True)
    docs_arch_dir = base / "docs" / "architecture"
    docs_arch_dir.mkdir(parents=True, exist_ok=True)
    (docs_arch_dir / "MODULES.md").write_text(
        "## runtime-utils\n**Domain:** runtime\n**Owner:** runtime\n**Summary:** system helper\n"
        "## tooling-play\n**Domain:** tooling\n**Owner:** tooling\n**Summary:** user helper\n",
        encoding="utf-8",
    )

    _write_log(paths)
    yield base

    reset_database_pool()
    reset_ticket_repository()


@pytest.mark.api
def test_api_version_and_modules(api_workspace, monkeypatch):
    app = create_app(project_root=api_workspace)

    def fake_git(cmd, project_root):
        if "--porcelain" in cmd:
            return ""
        if "--abbrev-ref" in cmd:
            return "develop"
        if "rev-parse" in cmd and cmd[-1] == "HEAD":
            return "commit-hash"
        if "--tags" in cmd:
            return "v2.7.3"
        return None

    monkeypatch.setattr("actifix.api._run_git_command", fake_git)

    client = app.test_client()
    resp = client.get("/api/version")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["branch"] == "develop"
    assert data["git_checked"] is True

    modules = client.get("/api/modules").get_json()
    assert "system" in modules and "user" in modules
    assert any(m["name"] == "runtime-utils" for m in modules["system"])


@pytest.mark.api
def test_api_logs_stats_and_tickets(api_workspace, monkeypatch):
    app = create_app(project_root=api_workspace)
    client = app.test_client()
    paths = get_actifix_paths(project_root=api_workspace)
    repo = get_ticket_repository()

    open_entry = _build_ticket("ACT-OPEN", TicketPriority.P1)
    repo.create_ticket(open_entry)
    completed_entry = _build_ticket("ACT-CLOSE", TicketPriority.P2)
    repo.create_ticket(completed_entry)
    repo.mark_complete(
        completed_entry.entry_id,
        completion_notes="API endpoint test ticket completed successfully",
        test_steps="Tested API endpoints with client",
        test_results="API stats and tickets endpoints working correctly",
        summary="completed"
    )

    stats = client.get("/api/stats").get_json()
    assert stats["total"] >= 2
    assert stats["open"] >= 1

    tickets = client.get("/api/tickets?limit=5").get_json()
    assert tickets["total_open"] >= 1
    assert len(tickets["tickets"]) >= 1

    logs_resp = client.get("/api/logs?type=audit&lines=2").get_json()
    assert logs_resp["total_lines"] >= 2
    assert any(line["level"] == "SUCCESS" for line in logs_resp["content"])


@pytest.mark.api
def test_api_settings_and_ping(api_workspace):
    app = create_app(project_root=api_workspace)
    client = app.test_client()

    current = client.get("/api/settings").get_json()
    assert current["ai_provider"] == "openai"
    assert "*" in current["ai_api_key"]

    update_resp = client.post("/api/settings", json={
        "ai_provider": "claude_api",
        "ai_enabled": False,
    })
    assert update_resp.status_code == 200
    new_settings = client.get("/api/settings").get_json()
    assert new_settings["ai_provider"] == "claude_api"
    assert new_settings["ai_enabled"] is False

    ping = client.get("/api/ping").get_json()
    assert ping["status"] == "ok"


@pytest.mark.api
def test_api_fix_and_system(api_workspace):
    app = create_app(project_root=api_workspace)
    client = app.test_client()
    paths = get_actifix_paths(project_root=api_workspace)
    repo = get_ticket_repository()
    entry = _build_ticket("ACT-FIX", TicketPriority.P0)
    repo.create_ticket(entry)

    resp = client.post("/api/fix-ticket")
    data = resp.get_json()
    assert data["processed"] is True
    assert repo.get_ticket(entry.entry_id)["status"] == "Completed"

    system = client.get("/api/system").get_json()
    assert "platform" in system
    assert "resources" in system