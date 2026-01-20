from __future__ import annotations

import pytest

from actifix.modules.pokertool.core import evaluate_hand, PokerToolAnalysisError


def test_evaluate_hand_computes_strength_for_two_cards() -> None:
    result = evaluate_hand(["Ah", "Kd"])
    assert result["strength_label"] in {"Premium", "Strong", "Playable", "Marginal", "Fold"}
    assert result["hand"][0]["rank"] == "A"
    assert result["hand"][1]["rank"] == "K"
    assert result["board"] == []
    assert isinstance(result["strength_score"], float)
    assert result["high_card"] == "A"


def test_evaluate_hand_includes_board_context() -> None:
    result = evaluate_hand(["7h", "7d"], ["9h", "Th", "Jh"])
    assert result["pair_count"] >= 1
    assert result["has_board"] is True
    assert result["connected_run"] >= 3
    assert "board" in result
    assert len(result["board"]) == 3


def test_evaluate_hand_invalid_payload_raises() -> None:
    with pytest.raises(PokerToolAnalysisError):
        evaluate_hand(["Ah"])  # not enough hole cards


def test_evaluate_hand_rejects_too_many_cards() -> None:
    hand = ["Ah", "Kd"]
    board = ["2c", "3c", "4c", "5c", "6c", "7c"]
    with pytest.raises(PokerToolAnalysisError):
        evaluate_hand(hand, board)
