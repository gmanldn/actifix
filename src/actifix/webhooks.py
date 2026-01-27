"""
Webhook integration for ticket events.

Sends HTTP POST notifications when tickets are created or completed.
Supports multiple webhook URLs with retry logic and timeout handling.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib import request
from urllib.error import URLError, HTTPError

from .log_utils import log_event
from .config import get_config


def _agent_voice_best_effort(thought: str, *, level: str = "INFO", extra: dict | None = None) -> None:
    # Best-effort AgentVoice logging for webhook activity; failures are captured via Raise_AF.
    try:
        from actifix.agent_voice import record_agent_voice

        record_agent_voice(
            thought,
            agent_id="core.webhooks",
            run_label="webhooks",
            level=level,
            extra=extra,
        )
    except Exception:
        pass


def _sanitize_ticket_for_webhook(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize ticket data for webhook payload.

    Removes sensitive fields and limits payload size.

    Args:
        ticket: Raw ticket data.

    Returns:
        Sanitized ticket data safe for external transmission.
    """
    # Fields to include in webhook payload
    safe_fields = {
        "id",
        "ticket_id",
        "entry_id",
        "priority",
        "error_type",
        "message",
        "source",
        "run_label",
        "created_at",
        "updated_at",
        "status",
        "correlation_id",
    }

    sanitized = {}
    for key, value in ticket.items():
        if key in safe_fields:
            # Truncate message if too long (max 1000 chars for webhook)
            if key == "message" and isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:997] + "..."
            else:
                sanitized[key] = value

    return sanitized


def _send_payload_webhook(
    url: str,
    payload: Dict[str, Any],
    *,
    event_type: str,
    ticket_id: str,
    timeout_seconds: int = 5,
    max_retries: int = 2,
) -> bool:
    payload_bytes = json.dumps(payload).encode("utf-8")

    for attempt in range(max_retries + 1):
        try:
            req = request.Request(
                url,
                data=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Actifix-Webhook/1.0",
                },
                method="POST",
            )

            with request.urlopen(req, timeout=timeout_seconds) as response:
                status_code = response.getcode()
                if 200 <= status_code < 300:
                    log_event(
                        "WEBHOOK_SUCCESS",
                        f"Webhook sent successfully: {event_type}",
                        extra={
                            "url": url,
                            "event": event_type,
                            "ticket_id": ticket_id,
                            "status_code": status_code,
                            "attempt": attempt + 1,
                        },
                    )
                    _agent_voice_best_effort(
                        f"Webhook sent successfully: {event_type}",
                        extra={"url": url, "event": event_type, "ticket_id": ticket_id},
                    )
                    return True
                else:
                    log_event(
                        "WEBHOOK_HTTP_ERROR",
                        f"Webhook returned non-2xx status: {status_code}",
                        extra={
                            "url": url,
                            "event": event_type,
                            "status_code": status_code,
                            "attempt": attempt + 1,
                        },
                    )
        except HTTPError as e:
            log_event(
                "WEBHOOK_HTTP_ERROR",
                f"Webhook HTTP error: {e.code} {e.reason}",
                extra={
                    "url": url,
                    "event": event_type,
                    "error_code": e.code,
                    "error_reason": str(e.reason),
                    "attempt": attempt + 1,
                },
            )
            _record_webhook_error(
                f"Webhook HTTP error: {e.code} {e.reason}",
                url=url,
                event_type=event_type,
                ticket_id=ticket_id,
                error_type=type(e).__name__,
            )
        except URLError as e:
            log_event(
                "WEBHOOK_URL_ERROR",
                f"Webhook URL error: {e.reason}",
                extra={
                    "url": url,
                    "event": event_type,
                    "error_reason": str(e.reason),
                    "attempt": attempt + 1,
                },
            )
            _record_webhook_error(
                f"Webhook URL error: {e.reason}",
                url=url,
                event_type=event_type,
                ticket_id=ticket_id,
                error_type=type(e).__name__,
            )
        except Exception as e:
            log_event(
                "WEBHOOK_ERROR",
                f"Webhook unexpected error: {type(e).__name__}: {e}",
                extra={
                    "url": url,
                    "event": event_type,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "attempt": attempt + 1,
                },
            )
            _record_webhook_error(
                f"Webhook unexpected error: {type(e).__name__}: {e}",
                url=url,
                event_type=event_type,
                ticket_id=ticket_id,
                error_type=type(e).__name__,
            )

        # Exponential backoff before retry
        if attempt < max_retries:
            time.sleep(0.5 * (2 ** attempt))

    return False


def _record_webhook_error(
    message: str,
    *,
    url: str,
    event_type: str,
    ticket_id: str,
    error_type: str,
) -> None:
    _agent_voice_best_effort(
        f"{message}",
        level="ERROR",
        extra={"url": url, "event": event_type, "ticket_id": ticket_id, "error_type": error_type},
    )
    try:
        from .raise_af import record_error, TicketPriority

        record_error(
            message=message,
            source="webhooks.py:_send_payload_webhook",
            error_type=error_type,
            priority=TicketPriority.P3,
        )
    except Exception:
        pass


def _send_single_webhook(
    url: str,
    event_type: str,
    ticket_data: Dict[str, Any],
    timeout_seconds: int = 5,
    max_retries: int = 2,
) -> bool:
    """
    Send a single webhook notification.

    Args:
        url: Webhook URL to POST to.
        event_type: Event type ("ticket.created" or "ticket.completed").
        ticket_data: Sanitized ticket data.
        timeout_seconds: Request timeout in seconds.
        max_retries: Maximum retry attempts on failure.

    Returns:
        True if webhook sent successfully, False otherwise.
    """
    payload = {
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        "ticket": ticket_data,
    }
    ticket_id = ticket_data.get("id", "unknown")
    return _send_payload_webhook(
        url,
        payload,
        event_type=event_type,
        ticket_id=ticket_id,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


def send_webhook_notification(
    event_type: str,
    ticket: Dict[str, Any],
    webhook_urls: Optional[List[str]] = None,
) -> int:
    """
    Send webhook notifications for a ticket event.

    Args:
        event_type: Event type ("ticket.created" or "ticket.completed").
        ticket: Ticket data to include in webhook.
        webhook_urls: Optional list of webhook URLs (uses config if not provided).

    Returns:
        Number of successfully sent webhooks.
    """
    # Get webhook URLs from config if not provided
    if webhook_urls is None:
        config = get_config()
        webhook_urls_str = config.webhook_urls.strip()
        if not webhook_urls_str:
            # No webhooks configured
            return 0

        # Parse comma-separated URLs
        webhook_urls = [
            url.strip()
            for url in webhook_urls_str.split(",")
            if url.strip()
        ]

    if not webhook_urls:
        return 0

    # Sanitize ticket data
    sanitized_ticket = _sanitize_ticket_for_webhook(ticket)

    # Send to all configured webhooks
    success_count = 0
    for url in webhook_urls:
        if _send_single_webhook(url, event_type, sanitized_ticket):
            success_count += 1

    return success_count


def send_ticket_created_webhook(ticket: Dict[str, Any]) -> int:
    """
    Send webhook notification for ticket creation.

    Args:
        ticket: Newly created ticket data.

    Returns:
        Number of successfully sent webhooks.
    """
    return send_webhook_notification("ticket.created", ticket)


def send_ticket_completed_webhook(ticket: Dict[str, Any]) -> int:
    """
    Send webhook notification for ticket completion.

    Args:
        ticket: Completed ticket data.

    Returns:
        Number of successfully sent webhooks.
    """
    return send_webhook_notification("ticket.completed", ticket)


def _normalize_alert_priorities(raw: str) -> set[str]:
    priorities = set()
    for token in (raw or "").split(","):
        normalized = token.strip().upper()
        if normalized:
            priorities.add(normalized)
    return priorities or {"P0", "P1"}


def _format_alert_payload(event_type: str, ticket: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = _sanitize_ticket_for_webhook(ticket)
    ticket_id = sanitized.get("id") or sanitized.get("ticket_id") or "unknown"
    priority = sanitized.get("priority") or "P?"
    message = sanitized.get("message") or ""
    source = sanitized.get("source") or "unknown"
    error_type = sanitized.get("error_type") or "unknown"
    created_at = sanitized.get("created_at") or ""

    title = f"Actifix {priority} alert"
    summary = f"{ticket_id} • {error_type} • {source}"
    text = "\n".join(
        [
            f"{title} ({event_type})",
            summary,
            message[:500],
            f"Created: {created_at}" if created_at else "",
        ]
    ).strip()

    return {
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        "ticket": sanitized,
        # Slack uses "text"; Discord uses "content". Provide both.
        "text": text,
        "content": text,
    }


def send_ticket_alert_webhook(ticket: Dict[str, Any]) -> int:
    """
    Send Slack/Discord alert notifications for high-priority tickets.

    Uses ACTIFIX_ALERT_WEBHOOK_URLS and ACTIFIX_ALERT_WEBHOOK_PRIORITIES.
    """
    config = get_config()
    if not config.alert_webhook_enabled:
        return 0

    urls = [u.strip() for u in (config.alert_webhook_urls or "").split(",") if u.strip()]
    if not urls:
        return 0

    priorities = _normalize_alert_priorities(config.alert_webhook_priorities)
    ticket_priority = (ticket.get("priority") or "").strip().upper()
    if ticket_priority and ticket_priority not in priorities:
        return 0

    payload = _format_alert_payload("ticket.alert", ticket)
    ticket_id = ticket.get("id") or ticket.get("ticket_id") or "unknown"

    success_count = 0
    for url in urls:
        if _send_payload_webhook(
            url,
            payload,
            event_type="ticket.alert",
            ticket_id=str(ticket_id),
        ):
            success_count += 1

    return success_count
