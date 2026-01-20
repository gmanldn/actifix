from __future__ import annotations

import pytest

from actifix.modules.pokertool.ml import (
    PokerToolMLError,
    OpponentProfile,
    active_learning_hint,
    build_opponent_model,
)


def test_build_opponent_model_constructs_profile() -> None:
    history = [
        {"action": "raise", "aggression": 0.8},
        {"action": "call", "aggression": 0.4},
        {"action": "raise", "aggression": 0.6},
    ]
    profile = build_opponent_model(history)
    assert isinstance(profile, OpponentProfile)
    assert profile.confidence >= 0.5


def test_build_opponent_model_requires_history() -> None:
    with pytest.raises(PokerToolMLError):
        build_opponent_model([])


def test_active_learning_hint_requires_scores() -> None:
    with pytest.raises(PokerToolMLError):
        active_learning_hint([])


def test_active_learning_hint_returns_spread() -> None:
    scores = [0.2, 0.5, 0.8]
    hint = active_learning_hint(scores)
    assert hint["spread"] == pytest.approx(0.6, rel=1e-3)
