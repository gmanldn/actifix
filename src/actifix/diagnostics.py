"""
Diagnostics bundle export for support.

Collects system state, recent tickets, logs, and configuration for troubleshooting.
"""

import json
import platform
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from .log_utils import log_event
from .config import get_config
from .state_paths import get_actifix_paths


def _get_system_info() -> Dict[str, Any]:
    """
    Collect system information.

    Returns:
        Dictionary with system details.
    """
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_config_summary() -> Dict[str, Any]:
    """
    Collect sanitized configuration summary.

    Returns:
        Dictionary with config (secrets redacted).
    """
    config = get_config()

    # Only include non-sensitive config values
    return {
        "capture_enabled": config.capture_enabled,
        "secret_redaction_enabled": config.secret_redaction_enabled,
        "max_open_tickets": config.max_open_tickets,
        "ticket_throttling_enabled": config.ticket_throttling_enabled,
        "dispatch_enabled": config.dispatch_enabled,
        "ai_enabled": config.ai_enabled,
        "ai_provider": config.ai_provider if config.ai_provider else "default",
        "webhook_enabled": config.webhook_enabled,
        "completion_hooks_enabled": config.completion_hooks_enabled,
    }


def _get_recent_tickets(limit: int = 50) -> list[Dict[str, Any]]:
    """
    Get recent tickets for diagnostics.

    Args:
        limit: Maximum number of tickets to include.

    Returns:
        List of recent tickets (sanitized).
    """
    try:
        from .persistence.ticket_repo import get_ticket_repository

        repo = get_ticket_repository()
        tickets = repo.get_recent_tickets(limit=limit)

        # Sanitize ticket data (remove potentially sensitive fields)
        sanitized = []
        for ticket in tickets:
            sanitized.append({
                "id": ticket.get("id", ""),
                "priority": ticket.get("priority", ""),
                "error_type": ticket.get("error_type", ""),
                "source": ticket.get("source", ""),
                "status": ticket.get("status", ""),
                "created_at": ticket.get("created_at", ""),
                "message_preview": ticket.get("message", "")[:200] if ticket.get("message") else "",
            })

        return sanitized
    except Exception:
        return []


def _get_ticket_stats() -> Dict[str, Any]:
    """
    Get ticket statistics.

    Returns:
        Dictionary with ticket counts by status and priority.
    """
    try:
        from .do_af import get_ticket_stats

        return get_ticket_stats()
    except Exception:
        return {}


def _get_health_status() -> Dict[str, Any]:
    """
    Get system health status.

    Returns:
        Dictionary with health check results.
    """
    try:
        from .health import get_health

        health = get_health()
        return {
            "overall_status": health.get("status", "unknown"),
            "components": health.get("components", {}),
        }
    except Exception:
        return {"status": "error", "error": "Health check failed"}


def _get_recent_logs(max_lines: int = 500) -> str:
    """
    Get recent log entries.

    Args:
        max_lines: Maximum number of log lines to include.

    Returns:
        Recent log content.
    """
    try:
        paths = get_actifix_paths()
        log_files = list(paths.logs_dir.glob("actifix*.log"))

        if not log_files:
            return "No log files found"

        # Get most recent log file
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)

        # Read last N lines
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            return ''.join(recent_lines)
    except Exception as e:
        return f"Error reading logs: {e}"


def export_diagnostics_bundle(
    output_path: Optional[Path] = None,
    include_logs: bool = True,
    include_tickets: bool = True,
) -> Path:
    """
    Export a diagnostics bundle for support.

    Args:
        output_path: Optional output path for the bundle.
        include_logs: Whether to include recent logs.
        include_tickets: Whether to include recent tickets.

    Returns:
        Path to the created diagnostics bundle (ZIP file).
    """
    paths = get_actifix_paths()

    # Generate output filename
    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = paths.base_dir / f"actifix_diagnostics_{timestamp}.zip"

    # Collect diagnostics data
    diagnostics = {
        "system_info": _get_system_info(),
        "config": _get_config_summary(),
        "ticket_stats": _get_ticket_stats(),
        "health": _get_health_status(),
    }

    if include_tickets:
        diagnostics["recent_tickets"] = _get_recent_tickets(limit=50)

    # Create ZIP bundle
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add diagnostics JSON
        diagnostics_json = json.dumps(diagnostics, indent=2, default=str)
        zf.writestr("diagnostics.json", diagnostics_json)

        # Add recent logs if requested
        if include_logs:
            logs_content = _get_recent_logs(max_lines=500)
            zf.writestr("recent_logs.txt", logs_content)

        # Add system info as text
        system_info_text = "\n".join(
            f"{k}: {v}" for k, v in diagnostics["system_info"].items()
        )
        zf.writestr("system_info.txt", system_info_text)

    log_event(
        "DIAGNOSTICS_EXPORTED",
        f"Diagnostics bundle exported to {output_path}",
        extra={
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "include_logs": include_logs,
            "include_tickets": include_tickets,
        },
    )

    return output_path


def print_diagnostics_summary() -> None:
    """
    Print a diagnostics summary to stdout.
    """
    print("=" * 80)
    print("ACTIFIX DIAGNOSTICS SUMMARY")
    print("=" * 80)
    print()

    # System info
    print("System Information:")
    print("-" * 80)
    system_info = _get_system_info()
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    print()

    # Configuration
    print("Configuration:")
    print("-" * 80)
    config_summary = _get_config_summary()
    for key, value in config_summary.items():
        print(f"  {key}: {value}")
    print()

    # Ticket stats
    print("Ticket Statistics:")
    print("-" * 80)
    ticket_stats = _get_ticket_stats()
    if ticket_stats:
        for key, value in ticket_stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    else:
        print("  No ticket statistics available")
    print()

    # Health
    print("Health Status:")
    print("-" * 80)
    health = _get_health_status()
    print(f"  Overall: {health.get('overall_status', 'unknown')}")
    if "components" in health:
        for component, status in health["components"].items():
            print(f"  {component}: {status}")
    print()

    print("=" * 80)
