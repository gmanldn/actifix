"""
Tests for diagnostics export.
"""

import json
import zipfile
from pathlib import Path
import pytest

from actifix.diagnostics import (
    export_diagnostics_bundle,
    print_diagnostics_summary,
    _get_system_info,
    _get_config_summary,
    _get_ticket_stats,
    _get_health_status,
)


def test_get_system_info():
    """Test system info collection."""
    info = _get_system_info()

    assert "platform" in info
    assert "python_version" in info
    assert "python_executable" in info
    assert "architecture" in info
    assert "hostname" in info
    assert "timestamp" in info


def test_get_config_summary():
    """Test config summary collection."""
    config = _get_config_summary()

    # Check for expected config fields
    assert "capture_enabled" in config
    assert "secret_redaction_enabled" in config
    assert "max_open_tickets" in config
    assert "ticket_throttling_enabled" in config
    assert "dispatch_enabled" in config
    assert "ai_enabled" in config

    # Ensure sensitive fields are not included
    assert "ai_api_key" not in config


def test_get_ticket_stats():
    """Test ticket stats collection."""
    stats = _get_ticket_stats()

    # Stats might be empty but should be a dict
    assert isinstance(stats, dict)


def test_get_health_status():
    """Test health status collection."""
    health = _get_health_status()

    assert isinstance(health, dict)
    # Should have at least a status field
    assert "overall_status" in health or "status" in health


def test_export_diagnostics_bundle_basic(tmp_path):
    """Test basic diagnostics bundle export."""
    output_path = tmp_path / "diagnostics.zip"

    bundle_path = export_diagnostics_bundle(
        output_path=output_path,
        include_logs=False,
        include_tickets=False,
    )

    assert bundle_path.exists()
    assert bundle_path.suffix == ".zip"
    assert bundle_path.stat().st_size > 0

    # Verify ZIP contents
    with zipfile.ZipFile(bundle_path, 'r') as zf:
        files = zf.namelist()

        assert "diagnostics.json" in files
        assert "system_info.txt" in files

        # Verify diagnostics.json content
        diagnostics_data = json.loads(zf.read("diagnostics.json"))
        assert "system_info" in diagnostics_data
        assert "config" in diagnostics_data
        assert "ticket_stats" in diagnostics_data
        assert "health" in diagnostics_data


def test_export_diagnostics_bundle_with_logs(tmp_path):
    """Test diagnostics bundle export with logs."""
    output_path = tmp_path / "diagnostics_with_logs.zip"

    bundle_path = export_diagnostics_bundle(
        output_path=output_path,
        include_logs=True,
        include_tickets=False,
    )

    assert bundle_path.exists()

    with zipfile.ZipFile(bundle_path, 'r') as zf:
        files = zf.namelist()
        assert "recent_logs.txt" in files


def test_export_diagnostics_bundle_with_tickets(tmp_path):
    """Test diagnostics bundle export with tickets."""
    output_path = tmp_path / "diagnostics_with_tickets.zip"

    bundle_path = export_diagnostics_bundle(
        output_path=output_path,
        include_logs=False,
        include_tickets=True,
    )

    assert bundle_path.exists()

    with zipfile.ZipFile(bundle_path, 'r') as zf:
        diagnostics_data = json.loads(zf.read("diagnostics.json"))
        assert "recent_tickets" in diagnostics_data
        assert isinstance(diagnostics_data["recent_tickets"], list)


def test_export_diagnostics_bundle_auto_naming(tmp_path):
    """Test automatic naming of diagnostics bundle."""
    from actifix.state_paths import get_actifix_paths
    from actifix.config import set_config, ActifixConfig

    # Temporarily set paths to tmp_path
    paths = get_actifix_paths(project_root=tmp_path)
    paths.base_dir.mkdir(parents=True, exist_ok=True)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)

    config = ActifixConfig(
        project_root=tmp_path,
        paths=paths,
    )
    set_config(config)

    try:
        bundle_path = export_diagnostics_bundle(
            output_path=None,  # Auto-generate name
            include_logs=False,
            include_tickets=False,
        )

        assert bundle_path.exists()
        assert "actifix_diagnostics_" in bundle_path.name
        assert bundle_path.suffix == ".zip"
    finally:
        from actifix.config import reset_config
        reset_config()


def test_print_diagnostics_summary(capsys):
    """Test printing diagnostics summary."""
    print_diagnostics_summary()

    captured = capsys.readouterr()
    output = captured.out

    # Verify output contains expected sections
    assert "ACTIFIX DIAGNOSTICS SUMMARY" in output
    assert "System Information:" in output
    assert "Configuration:" in output
    assert "Ticket Statistics:" in output
    assert "Health Status:" in output


def test_diagnostics_bundle_json_valid(tmp_path):
    """Test that diagnostics bundle contains valid JSON."""
    output_path = tmp_path / "diagnostics_valid.zip"

    bundle_path = export_diagnostics_bundle(
        output_path=output_path,
        include_logs=False,
        include_tickets=True,
    )

    with zipfile.ZipFile(bundle_path, 'r') as zf:
        # Verify diagnostics.json is valid JSON
        diagnostics_json = zf.read("diagnostics.json")
        data = json.loads(diagnostics_json)

        # Verify structure
        assert isinstance(data, dict)
        assert isinstance(data["system_info"], dict)
        assert isinstance(data["config"], dict)
        assert isinstance(data["ticket_stats"], dict)
        assert isinstance(data["health"], dict)


def test_diagnostics_bundle_sanitization(tmp_path):
    """Test that sensitive data is sanitized."""
    output_path = tmp_path / "diagnostics_sanitized.zip"

    bundle_path = export_diagnostics_bundle(
        output_path=output_path,
        include_logs=False,
        include_tickets=True,
    )

    with zipfile.ZipFile(bundle_path, 'r') as zf:
        diagnostics_data = json.loads(zf.read("diagnostics.json"))

        # Config should not contain API keys
        config = diagnostics_data["config"]
        assert "ai_api_key" not in config

        # Tickets should be sanitized
        if diagnostics_data.get("recent_tickets"):
            for ticket in diagnostics_data["recent_tickets"]:
                # Should have basic fields
                assert "id" in ticket
                assert "priority" in ticket
                # Should not have full message (only preview)
                if "message_preview" in ticket and ticket["message_preview"]:
                    assert len(ticket["message_preview"]) <= 200
