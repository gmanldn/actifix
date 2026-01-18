"""Tests for the Yhatzee module GUI."""

import pytest


def test_yhatzee_gui_serves_html():
    pytest.importorskip("flask")

    from actifix.modules.yhatzee import create_app

    app = create_app()
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"Yhatzee" in response.data
    assert b"Roll Dice" in response.data


def test_yhatzee_health_route():
    pytest.importorskip("flask")

    from actifix.modules.yhatzee import create_app

    app = create_app()
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
