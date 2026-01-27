"""Baseline module tests using the module test harness."""

import os
import pytest

from actifix.testing import create_module_test_client


def test_yahtzee_module_harness():
    pytest.importorskip("flask")

    # Set minimal health response for testing
    os.environ["ACTIFIX_MODULE_HEALTH_MINIMAL"] = "1"
    try:
        client = create_module_test_client("yahtzee", url_prefix=None)
        response = client.get("/")
        assert response.status_code == 200
        assert b"Yahtzee" in response.data

        health = client.get("/health")
        assert health.status_code == 200
        assert health.get_json() == {"status": "ok"}
    finally:
        os.environ.pop("ACTIFIX_MODULE_HEALTH_MINIMAL", None)


def test_superquiz_module_harness():
    pytest.importorskip("flask")

    # Set minimal health response for testing
    os.environ["ACTIFIX_MODULE_HEALTH_MINIMAL"] = "1"
    try:
        client = create_module_test_client("superquiz", url_prefix=None)
        response = client.get("/")
        assert response.status_code == 200
        assert b"SuperQuiz" in response.data

        health = client.get("/health")
        assert health.status_code == 200
        assert health.get_json() == {"status": "ok"}
    finally:
        os.environ.pop("ACTIFIX_MODULE_HEALTH_MINIMAL", None)