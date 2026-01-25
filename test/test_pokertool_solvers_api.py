from __future__ import annotations

import pytest

from flask import Flask

from actifix.modules.pokertool import create_blueprint


@pytest.fixture
def pokertool_client() -> Flask.test_client:
    app = Flask(__name__)
    app.register_blueprint(create_blueprint(url_prefix="/modules/pokertool"))
    return app.test_client()


def test_solvers_nash_endpoint_returns_recommendation(pokertool_client: Flask.test_client) -> None:
    response = pokertool_client.post(
        "/modules/pokertool/api/solvers/nash",
        json={"hand": ["Ah", "Kd"], "board": ["Qs", "Jh", "10c"]},
    )
    assert response.status_code == 200
    payload = response.get_json() or {}
    assert payload.get("message") == "Nash computation completed."


def test_solvers_icm_endpoint_rejects_missing_payload(pokertool_client: Flask.test_client) -> None:
    response = pokertool_client.post("/modules/pokertool/api/solvers/icm")
    assert response.status_code == 400
