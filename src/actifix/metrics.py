#!/usr/bin/env python3
"""
Prometheus-compatible metrics export for Actifix.

Provides:
- Ticket statistics (open, completed, by priority)
- Health check status
- System performance metrics

Usage:
    from actifix.metrics import export_prometheus_metrics

    metrics = export_prometheus_metrics()
    # Returns text in Prometheus exposition format
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
from .state_paths import get_actifix_paths, ActifixPaths
from .do_af import get_ticket_stats
from .health import get_health
from .log_utils import log_event


def export_prometheus_metrics(paths: Optional[ActifixPaths] = None) -> str:
    """
    Export Actifix metrics in Prometheus exposition format.

    Args:
        paths: Actifix paths (if None, will use get_actifix_paths())

    Returns:
        str: Metrics in Prometheus text format

    Raises:
        Exception: If metrics collection fails
    """
    if paths is None:
        paths = get_actifix_paths()

    try:
        lines = []

        # Add header comment
        lines.append("# HELP actifix_info Actifix system information")
        lines.append("# TYPE actifix_info gauge")
        lines.append('actifix_info{version="7.0.12"} 1')
        lines.append("")

        # Ticket metrics
        # Get ticket counts by status
        ticket_stats = get_ticket_stats(paths)

        lines.append("# HELP actifix_tickets_total Total number of tickets")
        lines.append("# TYPE actifix_tickets_total counter")
        lines.append(f"actifix_tickets_total {ticket_stats.get('total', 0)}")
        lines.append("")

        lines.append("# HELP actifix_tickets_open Number of open tickets")
        lines.append("# TYPE actifix_tickets_open gauge")
        lines.append(f"actifix_tickets_open {ticket_stats.get('open', 0)}")
        lines.append("")

        lines.append("# HELP actifix_tickets_completed Number of completed tickets")
        lines.append("# TYPE actifix_tickets_completed counter")
        lines.append(f"actifix_tickets_completed {ticket_stats.get('completed', 0)}")
        lines.append("")

        # Tickets by priority
        lines.append("# HELP actifix_tickets_by_priority Tickets grouped by priority")
        lines.append("# TYPE actifix_tickets_by_priority gauge")
        for priority in ["P0", "P1", "P2", "P3", "P4"]:
            count = ticket_stats.get('by_priority', {}).get(priority, 0)
            lines.append(f'actifix_tickets_by_priority{{priority="{priority}"}} {count}')
        lines.append("")

        # Health check metrics
        health_data = get_health(paths)

        lines.append("# HELP actifix_health_status System health status (1=healthy, 0=unhealthy)")
        lines.append("# TYPE actifix_health_status gauge")
        health_status = 1 if health_data.healthy else 0
        lines.append(f"actifix_health_status {health_status}")
        lines.append("")

        # Database health
        lines.append("# HELP actifix_database_healthy Database health status (1=healthy, 0=unhealthy)")
        lines.append("# TYPE actifix_database_healthy gauge")
        db_healthy = 1 if health_data.database_ok else 0
        lines.append(f"actifix_database_healthy {db_healthy}")
        lines.append("")

        # Storage health
        lines.append("# HELP actifix_storage_healthy Storage health status (1=healthy, 0=unhealthy)")
        lines.append("# TYPE actifix_storage_healthy gauge")
        storage_healthy = 1 if health_data.files_writable else 0
        lines.append(f"actifix_storage_healthy {storage_healthy}")
        lines.append("")

        # Metrics generation timestamp
        lines.append("# HELP actifix_metrics_generated_timestamp_seconds Unix timestamp when metrics were generated")
        lines.append("# TYPE actifix_metrics_generated_timestamp_seconds gauge")
        lines.append(f"actifix_metrics_generated_timestamp_seconds {int(time.time())}")
        lines.append("")

        return "\n".join(lines)

    except Exception as e:
        log_event(
            "METRICS_EXPORT_FAILED",
            f"Failed to export Prometheus metrics: {e}",
            extra={"error": str(e)},
        )
        raise


def get_metrics_summary(paths: Optional[ActifixPaths] = None) -> Dict[str, Any]:
    """
    Get metrics summary as a dictionary.

    Useful for internal consumption or JSON API endpoints.

    Args:
        paths: Actifix paths (if None, will use get_actifix_paths())

    Returns:
        Dict containing metrics summary
    """
    if paths is None:
        paths = get_actifix_paths()

    try:
        ticket_stats = get_ticket_stats(paths)
        health_data = get_health(paths)

        return {
            "version": "7.0.12",
            "tickets": {
                "total": ticket_stats.get('total', 0),
                "open": ticket_stats.get('open', 0),
                "completed": ticket_stats.get('completed', 0),
                "by_priority": ticket_stats.get('by_priority', {}),
            },
            "health": {
            "overall_status": health_data.status,
            "database": "healthy" if health_data.database_ok else "unhealthy",
            "storage": "healthy" if health_data.files_writable else "unhealthy",
            },
            "timestamp": int(time.time()),
        }

    except Exception as e:
        log_event(
            "METRICS_SUMMARY_FAILED",
            f"Failed to get metrics summary: {e}",
            extra={"error": str(e)},
        )
        raise
