from __future__ import annotations

import pytest

from flask import Flask

from actifix.modules.pokertool import create_blueprint


@pytest.fixture
def pokertool_client() -> Flask.test_client:
    app = Flask(__name__)
    app.register_blueprint(create_blueprint(url_prefix="/modules/pokertool"))
    return app.test_client()


def test_ml_opponent_endpoint_returns_profile(pokertool_client: Flask.test_client) -> None:
    response = pokertool_client.post(
        "/modules/pokertool/api/ml/opponent",
        json={"history": [{"action": "raise", "aggression": 0.9}]},
    )
    assert response.status_code == 200
    assert response.get_json().get("message") == "Opponent model ready."


def test_ml_learn_endpoint_requires_scores(pokertool_client: Flask.test_client) -> None:
    response = pokertool_client.post("/modules/pokertool/api/ml/learn", json={"scores": [0.1, 0.5]})
    assert response.status_code == 200


def test_ml_endpoints_reject_missing_payload(pokertool_client: Flask.test_client) -> None:
    response = pokertool_client.post("/modules/pokertool/api/ml/opponent")
    assert response.status_code == 400
