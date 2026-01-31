"""
Actifix Health Check - System health and SLA monitoring.

Provides health checks, SLA tracking, and system diagnostics.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .state_paths import get_actifix_paths, ActifixPaths
from .do_af import get_open_tickets, get_ticket_stats
from .raise_af import record_error, TicketPriority

_AGENT_STATUS_FILENAME = "doaf_agent_status.json"
_AGENT_STALE_MINUTES = 10


# SLA thresholds (hours)
SLA_P0 = 1    # 1 hour for critical
SLA_P1 = 4    # 4 hours for high
SLA_P2 = 24   # 24 hours for medium
SLA_P3 = 72   # 72 hours for low


@dataclass
class ActifixHealthCheck:
    """Health check result."""
    
    healthy: bool
    status: str
    timestamp: datetime
    
    # Ticket metrics
    open_tickets: int = 0
    completed_tickets: int = 0
    sla_breaches: int = 0
    oldest_ticket_age_hours: float = 0
    
    # File system checks
    files_exist: bool = True
    files_writable: bool = True
    
    # Detailed info
    details: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def database_ok(self) -> bool:
        """Return whether the database artifact check passed."""
        return self.files_exist


def _parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    try:
        # Handle various ISO formats
        iso_str = iso_str.strip()
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
        return datetime.fromisoformat(iso_str)
    except (ValueError, AttributeError):
        return None


def _get_ticket_age_hours(created_str: str) -> float:
    """Get ticket age in hours."""
    created = _parse_iso_datetime(created_str)
    if not created:
        return 0
    
    now = datetime.now(timezone.utc)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    
    age = now - created
    return age.total_seconds() / 3600


def _get_sla_threshold(priority: str) -> int:
    """Get SLA threshold in hours for priority."""
    thresholds = {
        "P0": SLA_P0,
        "P1": SLA_P1,
        "P2": SLA_P2,
        "P3": SLA_P3,
    }
    return thresholds.get(priority, SLA_P2)


def _read_agent_status(paths: ActifixPaths) -> Optional[dict]:
    status_path = paths.state_dir / _AGENT_STATUS_FILENAME
    if not status_path.exists():
        return None
    try:
        payload = status_path.read_text()
        return json.loads(payload)
    except Exception as exc:
        record_error(
            message=f"Failed to read DoAF agent status: {exc}",
            source="actifix/health.py:_read_agent_status",
            error_type=type(exc).__name__,
            priority=TicketPriority.P3,
        )
        return None


def _agent_status_stale(agent_status: dict, now: datetime) -> bool:
    timestamp = agent_status.get("timestamp")
    if not timestamp:
        return True
    parsed = _parse_iso_datetime(timestamp)
    if not parsed:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return now - parsed > timedelta(minutes=_AGENT_STALE_MINUTES)


def check_sla_breaches(paths: Optional[ActifixPaths] = None) -> list[dict]:
    """
    Check for SLA breaches in open tickets.
    
    Args:
        paths: Optional paths override.
    
    Returns:
        List of breach info dicts.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    breaches = []
    tickets = get_open_tickets(paths)
    
    for ticket in tickets:
        age_hours = _get_ticket_age_hours(ticket.created)
        sla_hours = _get_sla_threshold(ticket.priority)
        
        if age_hours > sla_hours:
            breaches.append({
                "ticket_id": ticket.ticket_id,
                "priority": ticket.priority,
                "age_hours": round(age_hours, 1),
                "sla_hours": sla_hours,
                "breach_hours": round(age_hours - sla_hours, 1),
            })
    
    return breaches


def get_disk_usage(dir_path: Path) -> Optional[float]:
    """Get disk usage percentage for directory."""
    try:
        stat = os.statvfs(dir_path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used_percent = ((total - free) / total) * 100
        return used_percent
    except Exception:
        return None


def get_health(paths: Optional[ActifixPaths] = None) -> ActifixHealthCheck:
    """
    Perform comprehensive health check.
    
    Args:
        paths: Optional paths override.
    
    Returns:
        ActifixHealthCheck with results.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    now = datetime.now(timezone.utc)
    warnings = []
    errors = []
    
    # Check file system
    files_exist = True
    files_writable = True
    
    for artifact in paths.all_artifacts:
        if not artifact.exists():
            files_exist = False
            warnings.append(f"Missing file: {artifact.name}")
    
    # Check writability
    try:
        test_file = paths.base_dir / ".health_check"
        test_file.write_text("test")
        test_file.unlink()
    except (OSError, PermissionError) as e:
        files_writable = False
        errors.append(f"Cannot write to {paths.base_dir}: {e}")
    
    # Disk usage monitoring for .actifix/ and data/
    disk_threshold_warn = 90.0
    disk_threshold_crit = 95.0
    actifix_disk = get_disk_usage(paths.state_dir)
    data_disk = get_disk_usage(paths.data_dir)
    
    if actifix_disk:
        if actifix_disk > disk_threshold_crit:
            errors.append(f".actifix/ disk usage critical: {actifix_disk:.1f}%")
        elif actifix_disk > disk_threshold_warn:
            warnings.append(f".actifix/ disk usage high: {actifix_disk:.1f}%")
    
    if actifix_disk:
        if actifix_disk > disk_threshold_crit:
            errors.append(f".actifix/ disk usage critical: {actifix_disk:.1f}%")
            from .log_utils import log_event
            log_event("DISK_CRITICAL_ACTIFIX", f".actifix/ usage {actifix_disk:.1f}% >95%", priority="P1")
        elif actifix_disk > disk_threshold_warn:
            warnings.append(f".actifix/ disk usage high: {actifix_disk:.1f}%")
    
    if data_disk:
        if data_disk > disk_threshold_crit:
            errors.append(f"data/ disk usage critical: {data_disk:.1f}%")
            from .log_utils import log_event
            log_event("DISK_CRITICAL_DATA", f"data/ usage {data_disk:.1f}% >95%", priority="P1")
        elif data_disk > disk_threshold_warn:
            warnings.append(f"data/ disk usage high: {data_disk:.1f}%")

    # Check database size growth
    try:
        from .persistence.database import check_database_growth
        db_growth = check_database_growth(
            warn_threshold_mb=100.0,
            error_threshold_mb=500.0
        )
        if db_growth["status"] == "error":
            errors.append(db_growth["message"])
            record_error(
                message=f"Database size critical: {db_growth['size_mb']}MB",
                source="health.get_health",
                error_type="DatabaseGrowthCritical",
                priority=TicketPriority.P1,
                capture_context=False,
            )
        elif db_growth["status"] == "warning":
            warnings.append(db_growth["message"])
    except Exception as e:
        warnings.append(f"Database size check failed: {e}")


    # Get ticket stats
    stats = get_ticket_stats(paths)
    open_tickets = stats.get("open", 0)
    completed_tickets = stats.get("completed", 0)
    
    # Check SLA breaches
    breaches = check_sla_breaches(paths)
    sla_breaches = len(breaches)
    
    if sla_breaches > 0:
        for breach in breaches[:3]:  # Show first 3
            warnings.append(
                f"SLA breach: {breach['ticket_id']} "
                f"({breach['priority']}, {breach['breach_hours']}h over)"
            )
    
    # Get oldest ticket age
    oldest_age = 0
    tickets = get_open_tickets(paths)
    for ticket in tickets:
        age = _get_ticket_age_hours(ticket.created)
        if age > oldest_age:
            oldest_age = age
    
    # Determine overall health
    healthy = True
    status = "OK"
    
    if errors:
        healthy = False
        status = "ERROR"
    elif sla_breaches > 0:
        healthy = False
        status = "SLA_BREACH"
    elif warnings:
        status = "WARNING"
    
    # High ticket count warning
    if open_tickets > 20:
        warnings.append(f"High open ticket count: {open_tickets}")

    agent_status = _read_agent_status(paths)
    if agent_status:
        if _agent_status_stale(agent_status, now):
            warnings.append("DoAF agent heartbeat is stale")
        details_agent = {
            "state": agent_status.get("state"),
            "agent_id": agent_status.get("agent_id"),
            "run_label": agent_status.get("run_label"),
            "processed": agent_status.get("processed"),
            "ticket_id": agent_status.get("ticket_id"),
            "use_ai": agent_status.get("use_ai"),
            "fallback_complete": agent_status.get("fallback_complete"),
            "timestamp": agent_status.get("timestamp"),
        }
    else:
        details_agent = {}
    
    return ActifixHealthCheck(
        healthy=healthy,
        status=status,
        timestamp=now,
        open_tickets=open_tickets,
        completed_tickets=completed_tickets,
        sla_breaches=sla_breaches,
        oldest_ticket_age_hours=round(oldest_age, 1),
        files_exist=files_exist,
        files_writable=files_writable,
        details={
            "stats": stats,
            "breaches": breaches,
            "paths": {
                "base_dir": str(paths.base_dir),
            },
            "doaf_agent": details_agent,
        },
        warnings=warnings,
        errors=errors,
    )


def format_health_report(health: ActifixHealthCheck) -> str:
    """
    Format health check as human-readable report.
    
    Args:
        health: ActifixHealthCheck result.
    
    Returns:
        Formatted report string.
    """
    lines = [
        "=" * 50,
        "ACTIFIX HEALTH CHECK REPORT",
        "=" * 50,
        "",
        f"Status: {health.status}",
        f"Healthy: {'Yes' if health.healthy else 'No'}",
        f"Timestamp: {health.timestamp.isoformat()}",
        "",
        "--- Ticket Metrics ---",
        f"Open Tickets: {health.open_tickets}",
        f"Completed Tickets: {health.completed_tickets}",
        f"SLA Breaches: {health.sla_breaches}",
        f"Oldest Ticket Age: {health.oldest_ticket_age_hours}h",
        "",
        "--- DoAF Agent ---",
        f"Agent State: {health.details.get('doaf_agent', {}).get('state', 'unknown')}",
        f"Agent Last Seen: {health.details.get('doaf_agent', {}).get('timestamp', 'n/a')}",
        "",
        "--- System Checks ---",
        f"Files Exist: {'Yes' if health.files_exist else 'No'}",
        f"Files Writable: {'Yes' if health.files_writable else 'No'}",
    ]
    
    if health.warnings:
        lines.extend(["", "--- Warnings ---"])
        for w in health.warnings:
            lines.append(f"  ⚠ {w}")
    
    if health.errors:
        lines.extend(["", "--- Errors ---"])
        for e in health.errors:
            lines.append(f"  ✗ {e}")
    
    lines.append("")
    lines.append("=" * 50)
    
    return "\n".join(lines)


def run_health_check(
    paths: Optional[ActifixPaths] = None,
    print_report: bool = True,
) -> ActifixHealthCheck:
    """
    Run health check and optionally print report.
    
    Args:
        paths: Optional paths override.
        print_report: Whether to print the report.
    
    Returns:
        ActifixHealthCheck result.
    """
    health = get_health(paths)

    if print_report:
        print(format_health_report(health))

    return health
