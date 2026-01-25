"""Simplified PokerTool analysis helpers for hole-card evaluation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}

SUIT_VALUES = {"S", "H", "D", "C"}
MAX_TOTAL_CARDS = 7


class PokerToolAnalysisError(ValueError):
    """Domain error raised when inputs cannot be analysed."""


@dataclass(frozen=True)
class NormalizedCard:
    rank: str
    suit: str
    value: int

    def to_dict(self) -> dict[str, object]:
        return {"rank": self.rank, "suit": self.suit, "value": self.value}


def _normalize_card(token: str) -> NormalizedCard:
    if not isinstance(token, str):
        raise PokerToolAnalysisError("Card token must be a string.")
    normalized = token.strip().upper()
    if len(normalized) < 2:
        raise PokerToolAnalysisError(f"Card '{token}' is too short.")
    suit = normalized[-1]
    rank_token = normalized[:-1]
    if rank_token == "10":
        rank_token = "T"
    if suit not in SUIT_VALUES or rank_token not in RANK_VALUES:
        raise PokerToolAnalysisError(f"Invalid card representation: '{token}'.")
    return NormalizedCard(rank=rank_token, suit=suit, value=RANK_VALUES[rank_token])


def _normalize_cards(cards: Iterable[object]) -> list[NormalizedCard]:
    parsed: list[NormalizedCard] = []
    for idx, token in enumerate(cards):
        if token is None:
            raise PokerToolAnalysisError(f"Card at position {idx} is None.")
        parsed.append(_normalize_card(str(token)))
    return parsed


def _longest_consecutive_run(values: Sequence[int]) -> int:
    if not values:
        return 0
    unique_sorted = sorted(set(values))
    longest = 1
    current = 1
    for previous, current_value in zip(unique_sorted, unique_sorted[1:]):
        if current_value - previous == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _build_notes(
    normalized_hand: Sequence[NormalizedCard],
    normalized_board: Sequence[NormalizedCard],
    score: float,
    label: str,
) -> list[str]:
    notes: list[str] = []
    ranks = ", ".join(card.rank for card in normalized_hand)
    notes.append(f"Hole cards: {ranks}")
    if normalized_board:
        board_ranks = ", ".join(card.rank for card in normalized_board)
        notes.append(f"Board: {board_ranks}")
    notes.append(f"Strength label: {label} (score {score:.1f})")
    suits = {card.suit for card in normalized_hand}
    if len(suits) < len(normalized_hand):
        notes.append("Hole cards are suited.")
    return notes


def _recommendation(label: str) -> str:
    mapping = {
        "Premium": "Lean-in: raise or reraise with confidence.",
        "Strong": "Continue: build the pot or defend aggressively.",
        "Playable": "Proceed with caution; look for favourable spots.",
        "Marginal": "Sit tight or fold unless you get favourable odds.",
        "Fold": "Release the hand and wait for a stronger holding.",
    }
    return mapping.get(label, "Assess the opportunity with caution.")


def _determine_strength_label(score: float) -> str:
    if score >= 80:
        return "Premium"
    if score >= 60:
        return "Strong"
    if score >= 40:
        return "Playable"
    if score >= 25:
        return "Marginal"
    return "Fold"


def evaluate_hand(
    hand: Sequence[object],
    board: Sequence[object] | None = None,
) -> dict[str, object]:
    """
    Evaluate the provided hand and optional board cards for simple strength metrics.

    Args:
        hand: Iterable of at least two card strings (e.g., "Ah", "Ks").
        board: Optional board cards (up to five entries) to include in the analysis.

    Returns:
        Structured dictionary detailing hand strength heuristics.
    """
    if not hand:
        raise PokerToolAnalysisError("At least one hole card is required.")
    normalized_hand = _normalize_cards(hand)
    if len(normalized_hand) < 2:
        raise PokerToolAnalysisError("Provide at least two hole cards.")
    normalized_board = _normalize_cards(board) if board else []
    total_cards = normalized_hand + normalized_board
    if len(total_cards) > MAX_TOTAL_CARDS:
        raise PokerToolAnalysisError("Too many cards provided (maximum of 7).")

    values = [card.value for card in total_cards]
    rank_counts = Counter(card.rank for card in total_cards)
    suit_counts = Counter(card.suit for card in total_cards)

    high_card_value = max(values)
    max_duplicates = max(rank_counts.values(), default=0)
    pair_bonus = sum((count - 1) * 8 for count in rank_counts.values() if count > 1)
    suited_bonus = max(suit_counts.values(), default=0) >= 2
    connected_run = _longest_consecutive_run(values)

    score = float(high_card_value)
    score += 12 * max_duplicates
    score += pair_bonus
    score += 5 if suited_bonus else 0
    score += 4 if connected_run >= 3 else 0
    score += 3 if normalized_board else 0
    score = min(score, 100.0)

    label = _determine_strength_label(score)
    notes = _build_notes(normalized_hand, normalized_board, score, label)
    recommendation = _recommendation(label)

    high_card_rank = max(normalized_hand, key=lambda card: card.value).rank
    return {
        "hand": [card.to_dict() for card in normalized_hand],
        "board": [card.to_dict() for card in normalized_board],
        "strength_score": round(score, 2),
        "strength_label": label,
        "high_card": high_card_rank,
        "pair_count": sum(1 for count in rank_counts.values() if count >= 2),
        "suited": suited_bonus,
        "connected_run": connected_run,
        "has_board": bool(normalized_board),
        "notes": notes,
        "recommendation": recommendation,
    }
