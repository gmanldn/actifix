"""
Tests for webhook integration.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import List, Dict, Any
import pytest

from actifix.webhooks import (
    send_webhook_notification,
    send_ticket_created_webhook,
    send_ticket_completed_webhook,
    send_ticket_alert_webhook,
    _sanitize_ticket_for_webhook,
)
from actifix.config import reset_config


class WebhookTestHandler(BaseHTTPRequestHandler):
    """Test HTTP handler to receive webhook notifications."""

    received_webhooks: List[Dict[str, Any]] = []

    def do_POST(self):
        """Handle POST requests (webhooks)."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        webhook_data = json.loads(body.decode('utf-8'))

        # Store received webhook
        WebhookTestHandler.received_webhooks.append(webhook_data)

        # Send success response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        """Suppress log messages during tests."""
        pass


@pytest.fixture
def webhook_server():
    """Start a test webhook server."""
    WebhookTestHandler.received_webhooks = []

    server = HTTPServer(('127.0.0.1', 0), WebhookTestHandler)
    port = server.server_port

    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()


def test_sanitize_ticket_for_webhook():
    """Test ticket data sanitization."""
    ticket = {
        "id": "ACT-123",
        "priority": "P1",
        "message": "Test error",
        "source": "test.py:42",
        "stack_trace": "Traceback...",  # Should be excluded
        "file_context": {"test.py": "..."},  # Should be excluded
    }

    sanitized = _sanitize_ticket_for_webhook(ticket)

    assert "id" in sanitized
    assert "priority" in sanitized
    assert "message" in sanitized
    assert "source" in sanitized
    assert "stack_trace" not in sanitized
    assert "file_context" not in sanitized


def test_sanitize_long_message():
    """Test message truncation for webhook payload."""
    long_message = "x" * 2000
    ticket = {
        "id": "ACT-123",
        "message": long_message,
    }

    sanitized = _sanitize_ticket_for_webhook(ticket)

    assert len(sanitized["message"]) == 1000
    assert sanitized["message"].endswith("...")


def test_send_webhook_notification(webhook_server):
    """Test sending webhook notification."""
    ticket = {
        "id": "ACT-123",
        "priority": "P1",
        "error_type": "ValueError",
        "message": "Test error",
        "source": "test.py:42",
        "created_at": "2026-01-25T12:00:00",
        "status": "Open",
    }

    success_count = send_webhook_notification(
        "ticket.created",
        ticket,
        webhook_urls=[webhook_server],
    )

    assert success_count == 1
    assert len(WebhookTestHandler.received_webhooks) == 1

    received = WebhookTestHandler.received_webhooks[0]
    assert received["event"] == "ticket.created"
    assert received["ticket"]["id"] == "ACT-123"
    assert received["ticket"]["priority"] == "P1"
    assert "timestamp" in received


def test_send_multiple_webhooks(webhook_server):
    """Test sending to multiple webhook URLs."""
    ticket = {
        "id": "ACT-456",
        "priority": "P2",
        "message": "Another test",
    }

    # Send to same webhook twice (simulating multiple URLs)
    success_count = send_webhook_notification(
        "ticket.completed",
        ticket,
        webhook_urls=[webhook_server, webhook_server],
    )

    assert success_count == 2
    assert len(WebhookTestHandler.received_webhooks) == 2


def test_send_webhook_invalid_url():
    """Test webhook failure handling for invalid URL."""
    ticket = {"id": "ACT-789", "message": "Test"}

    success_count = send_webhook_notification(
        "ticket.created",
        ticket,
        webhook_urls=["http://invalid-host-that-does-not-exist:9999"],
    )

    assert success_count == 0


def test_send_webhook_no_urls():
    """Test sending webhook with no URLs configured."""
    ticket = {"id": "ACT-999", "message": "Test"}

    success_count = send_webhook_notification(
        "ticket.created",
        ticket,
        webhook_urls=[],
    )

    assert success_count == 0


def test_send_ticket_created_webhook(webhook_server):
    """Test ticket creation webhook helper."""
    ticket = {
        "id": "ACT-111",
        "priority": "P0",
        "message": "Critical error",
    }

    success_count = send_ticket_created_webhook(ticket)
    # No URLs in config, should return 0
    assert success_count == 0

    # With explicit URLs
    success_count = send_webhook_notification(
        "ticket.created",
        ticket,
        webhook_urls=[webhook_server],
    )
    assert success_count == 1


def test_send_ticket_completed_webhook(webhook_server):
    """Test ticket completion webhook helper."""
    ticket = {
        "id": "ACT-222",
        "priority": "P1",
        "message": "Fixed issue",
        "status": "Completed",
    }

    success_count = send_ticket_completed_webhook(ticket)
    # No URLs in config, should return 0
    assert success_count == 0

    # With explicit URLs
    success_count = send_webhook_notification(
        "ticket.completed",
        ticket,
        webhook_urls=[webhook_server],
    )
    assert success_count == 1

    received = WebhookTestHandler.received_webhooks[-1]
    assert received["event"] == "ticket.completed"
    assert received["ticket"]["status"] == "Completed"


def test_send_ticket_alert_webhook(webhook_server, monkeypatch):
    """Test Slack/Discord alert webhook helper."""
    monkeypatch.setenv("ACTIFIX_ALERT_WEBHOOK_URLS", webhook_server)
    monkeypatch.setenv("ACTIFIX_ALERT_WEBHOOK_ENABLED", "1")
    monkeypatch.setenv("ACTIFIX_ALERT_WEBHOOK_PRIORITIES", "P0,P1")
    reset_config()

    ticket = {
        "id": "ACT-333",
        "priority": "P0",
        "message": "Critical outage",
        "source": "api.py:42",
    }

    success_count = send_ticket_alert_webhook(ticket)
    assert success_count == 1
    received = WebhookTestHandler.received_webhooks[-1]
    assert received["event"] == "ticket.alert"
    assert "text" in received
    assert "content" in received

    ticket["priority"] = "P2"
    success_count = send_ticket_alert_webhook(ticket)
    assert success_count == 0
