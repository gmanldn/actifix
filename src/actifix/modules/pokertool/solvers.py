"""Solver helpers for the PokerTool module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


from .core import evaluate_hand


class PokerToolSolverError(ValueError):
    """Raised when provided solver inputs are invalid."""


@dataclass(frozen=True)
class SolverRecommendation:
    equity: float
    action: str
    message: str
    narrative: str


def _describe_texture(score: float, board_count: int) -> str:
    if score >= 70:
        return "Very strong range; board is forgiving."
    if board_count >= 4:
        return "Board is connected; expect dynamic solutions."
    if score >= 50:
        return "Solid equity; favour size with aggression."
    return "Defer to checks/folds until texture clarifies."


def compute_nash_equilibrium(hand: Iterable[str], board: Iterable[str] | None = None) -> SolverRecommendation:
    """Return an enriched Nash-equilibrium recommendation."""
    hand_cards = list(hand)
    if len(hand_cards) < 2:
        raise PokerToolSolverError("Hand information is required for Nash computation.")
    board_cards = list(board or [])
    evaluation = evaluate_hand(hand_cards, board_cards)

    raw_score = evaluation["strength_score"]
    board_count = len(board_cards)
    suited = evaluation["suited"]
    connectors = evaluation["connected_run"] >= 3

    equity = min(99.0, raw_score + (5 if suited else 0) + (3 if connectors else 0))
    action = "fold"
    if equity >= 70:
        action = "raise"
    elif equity >= 45:
        action = "call"

    message = {
        "raise": "Commit chips; strong equity and favourable texture.",
        "call": "Continue but stay alert for reverse implied odds.",
        "fold": "Caution: preserve stack, let the hand go."
    }[action]

    return SolverRecommendation(
        equity=round(equity, 2),
        action=action,
        message=message,
        narrative=_describe_texture(raw_score, board_count),
    )


def estimate_icm_value(stack_sizes: Iterable[float], payout_structure: Iterable[float]) -> dict[str, object]:
    """Estimate ICM share with a deck-leveraging heuristic."""
    stacks = list(stack_sizes)
    payouts = list(payout_structure)
    if not stacks or not payouts:
        raise PokerToolSolverError("Stacks and payout structure are required for ICM.")
    total_stack = sum(stacks)
    if total_stack <= 0:
        raise PokerToolSolverError("Total stack must be positive.")
    normalized = [stack / total_stack for stack in stacks]
    spread = max(normalized) - min(normalized)
    value = sum(payout * share for payout, share in zip(payouts, normalized))
    return {
        "icm_value": round(value, 2),
        "spread": round(spread, 3),
        "stack_share": normalized,
        "confidence": round(min(1.0, 0.3 + len(stacks) * 0.05), 2),
    }
