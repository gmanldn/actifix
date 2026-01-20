"""Baseline module tests using the module test harness."""

import pytest

from actifix.testing import create_module_test_client


def test_yhatzee_module_harness():
    pytest.importorskip("flask")

    client = create_module_test_client("yhatzee", url_prefix=None)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Yhatzee" in response.data

    health = client.get("/health")
    assert health.status_code == 200
    assert health.get_json() == {"status": "ok"}


def test_superquiz_module_harness():
    pytest.importorskip("flask")

    client = create_module_test_client("superquiz", url_prefix=None)
    response = client.get("/")
    assert response.status_code == 200
    assert b"SuperQuiz" in response.data

    health = client.get("/health")
    assert health.status_code == 200
    assert health.get_json() == {"status": "ok"}
