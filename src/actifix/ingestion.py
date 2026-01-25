"""
Sentry-style error ingestion endpoint.

Accepts external error reports and maps them to Actifix tickets.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .raise_af import record_error, TicketPriority
from .log_utils import log_event


def _parse_sentry_level(level: str) -> TicketPriority:
    """
    Map Sentry-style error levels to Actifix priorities.

    Args:
        level: Sentry level (fatal, error, warning, info, debug).

    Returns:
        Corresponding TicketPriority.
    """
    level_lower = level.lower().strip()

    level_map = {
        "fatal": TicketPriority.P0,
        "error": TicketPriority.P1,
        "warning": TicketPriority.P2,
        "info": TicketPriority.P3,
        "debug": TicketPriority.P4,
    }

    return level_map.get(level_lower, TicketPriority.P2)


def _extract_source_location(event: Dict[str, Any]) -> str:
    """
    Extract source file location from Sentry event.

    Args:
        event: Sentry event data.

    Returns:
        Source location string (file:line or module).
    """
    # Try to get from exception stacktrace
    if "exception" in event and "values" in event["exception"]:
        exceptions = event["exception"]["values"]
        if exceptions and len(exceptions) > 0:
            exception = exceptions[-1]  # Get innermost exception

            if "stacktrace" in exception and "frames" in exception["stacktrace"]:
                frames = exception["stacktrace"]["frames"]
                if frames and len(frames) > 0:
                    frame = frames[-1]  # Get top frame
                    filename = frame.get("filename", "unknown")
                    lineno = frame.get("lineno", 0)
                    return f"{filename}:{lineno}"

    # Fallback to platform or culprit
    culprit = event.get("culprit", "")
    if culprit:
        return culprit

    platform = event.get("platform", "external")
    return f"{platform}:ingestion"


def _extract_error_message(event: Dict[str, Any]) -> str:
    """
    Extract error message from Sentry event.

    Args:
        event: Sentry event data.

    Returns:
        Error message string.
    """
    # Try message field first
    if "message" in event:
        message = event["message"]
        if isinstance(message, dict):
            return message.get("formatted", message.get("message", ""))
        return str(message)

    # Try exception value
    if "exception" in event and "values" in event["exception"]:
        exceptions = event["exception"]["values"]
        if exceptions and len(exceptions) > 0:
            exception = exceptions[-1]
            value = exception.get("value", "")
            error_type = exception.get("type", "")

            if error_type and value:
                return f"{error_type}: {value}"
            elif value:
                return value
            elif error_type:
                return error_type

    # Fallback to logentry
    if "logentry" in event:
        logentry = event["logentry"]
        if isinstance(logentry, dict):
            return logentry.get("formatted", logentry.get("message", "No message"))
        return str(logentry)

    return "No error message provided"


def _extract_error_type(event: Dict[str, Any]) -> str:
    """
    Extract error type from Sentry event.

    Args:
        event: Sentry event data.

    Returns:
        Error type string.
    """
    # Try exception type
    if "exception" in event and "values" in event["exception"]:
        exceptions = event["exception"]["values"]
        if exceptions and len(exceptions) > 0:
            exception = exceptions[-1]
            error_type = exception.get("type", "")
            if error_type:
                return error_type

    # Fallback to level or platform
    level = event.get("level", "error")
    platform = event.get("platform", "external")
    return f"{platform}.{level}"


def _extract_stack_trace(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract stack trace from Sentry event.

    Args:
        event: Sentry event data.

    Returns:
        Stack trace string or None.
    """
    if "exception" in event and "values" in event["exception"]:
        exceptions = event["exception"]["values"]
        if exceptions and len(exceptions) > 0:
            exception = exceptions[-1]

            if "stacktrace" in exception and "frames" in exception["stacktrace"]:
                frames = exception["stacktrace"]["frames"]
                lines = []

                for frame in frames:
                    filename = frame.get("filename", "unknown")
                    lineno = frame.get("lineno", "?")
                    function = frame.get("function", "<unknown>")
                    lines.append(f"  File \"{filename}\", line {lineno}, in {function}")

                    # Add context line if available
                    context_line = frame.get("context_line", "").strip()
                    if context_line:
                        lines.append(f"    {context_line}")

                return "\n".join(lines) if lines else None

    return None


def ingest_sentry_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Ingest a Sentry-style error event and create an Actifix ticket.

    Args:
        event: Sentry event data (JSON payload).

    Returns:
        Created ticket ID or None if ingestion failed.
    """
    try:
        # Extract fields from Sentry event
        level = event.get("level", "error")
        priority = _parse_sentry_level(level)

        message = _extract_error_message(event)
        source = _extract_source_location(event)
        error_type = _extract_error_type(event)
        stack_trace = _extract_stack_trace(event)

        # Extract environment and tags for run_label
        environment = event.get("environment", "production")
        tags = event.get("tags", {})
        server_name = event.get("server_name", "external")

        run_label = f"{environment}:{server_name}"

        # Record error via Raise_AF
        entry = record_error(
            message=message,
            source=source,
            run_label=run_label,
            error_type=error_type,
            priority=priority,
            stack_trace=stack_trace,
            capture_context=False,  # Already have context from Sentry
        )

        if entry:
            log_event(
                "SENTRY_INGESTION_SUCCESS",
                f"Ingested Sentry event as ticket {entry.ticket_id}",
                extra={
                    "ticket_id": entry.ticket_id,
                    "event_id": event.get("event_id", "unknown"),
                    "level": level,
                    "platform": event.get("platform", "unknown"),
                },
            )
            return entry.ticket_id
        else:
            log_event(
                "SENTRY_INGESTION_DUPLICATE",
                "Sentry event was duplicate, no ticket created",
                extra={
                    "event_id": event.get("event_id", "unknown"),
                },
            )
            return None

    except Exception as e:
        log_event(
            "SENTRY_INGESTION_ERROR",
            f"Failed to ingest Sentry event: {e}",
            extra={
                "error": str(e),
                "event_id": event.get("event_id", "unknown"),
            },
        )
        return None
