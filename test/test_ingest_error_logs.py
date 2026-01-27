import os
from pathlib import Path


def _prepare_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(tmp_path / ".actifix"))
    monkeypatch.setenv("ACTIFIX_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("ACTIFIX_DB_PATH", str(tmp_path / "data" / "actifix.db"))


def _read_messages(repo):
    tickets = repo.get_tickets()
    return {ticket["message"]: ticket for ticket in tickets}


def test_ingest_plain_logs(tmp_path, monkeypatch):
    _prepare_env(monkeypatch, tmp_path)

    log_path = tmp_path / "errors.log"
    log_path.write_text("First error\nSecond error\n", encoding="utf-8")

    from scripts.ingest_error_logs import main as ingest_main
    from actifix.persistence.ticket_repo import get_ticket_repository

    rc = ingest_main([str(log_path), "--priority", "P1", "--run-label", "plain-run"])
    assert rc == 0

    repo = get_ticket_repository()
    messages = _read_messages(repo)
    assert "First error" in messages
    assert "Second error" in messages
    assert messages["First error"]["priority"] == "P1"
    assert messages["First error"]["run_label"] == "plain-run"


def test_ingest_jsonl_logs(tmp_path, monkeypatch):
    _prepare_env(monkeypatch, tmp_path)

    log_path = tmp_path / "errors.jsonl"
    log_path.write_text(
        "\n".join(
            [
                '{"message": "JSON error", "priority": "P0", "error_type": "ExternalJson", "source": "unit:test"}',
                '{"message": "Fallback error"}',
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ingest_error_logs import main as ingest_main
    from actifix.persistence.ticket_repo import get_ticket_repository

    rc = ingest_main([str(log_path), "--format", "jsonl", "--error-type", "ExternalLog"])
    assert rc == 0

    repo = get_ticket_repository()
    messages = _read_messages(repo)
    assert "JSON error" in messages
    assert messages["JSON error"]["priority"] == "P0"
    assert messages["JSON error"]["error_type"] == "ExternalJson"
    assert messages["JSON error"]["source"] == "unit:test"
    assert "Fallback error" in messages
    assert messages["Fallback error"]["error_type"] == "ExternalLog"
