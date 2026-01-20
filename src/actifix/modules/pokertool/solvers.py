"""Solver helpers for the PokerTool module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class PokerToolSolverError(ValueError):
    """Raised when provided solver inputs are invalid."""


@dataclass(frozen=True)
class SolverRecommendation:
    equity: float
    action: str
    message: str


def compute_nash_equilibrium(hand: Iterable[str], board: Iterable[str] | None = None) -> SolverRecommendation:
    """Return a placeholder Nash-equilibrium recommendation."""
    if not hand:
        raise PokerToolSolverError("Hand information is required for Nash computation.")
    board_cards = list(board or [])
    equity = 40.0 + min(len(hand), 3) * 6.0 + min(len(board_cards), 5) * 3.0
    equity = min(equity, 95.0)
    if equity >= 60:
        action = "raise"
        message = "Equity profile supports an aggressive action."
    elif equity >= 40:
        action = "call"
        message = "Continue with a controlled call."
    else:
        action = "fold"
        message = "Equity too low; protect your stack."
    return SolverRecommendation(equity=equity, action=action, message=message)


def estimate_icm_value(stack_sizes: Iterable[float], payout_structure: Iterable[float]) -> dict[str, object]:
    """Compute a simplified ICM value spread based on stacks and payouts."""
    stacks = list(stack_sizes)
    payouts = list(payout_structure)
    if not stacks or not payouts:
        raise PokerToolSolverError("Stacks and payout structure are required for ICM.")
    total_stack = sum(stacks)
    if total_stack <= 0:
        raise PokerToolSolverError("Total stack must be positive.")
    normalized = [stack / total_stack for stack in stacks]
    icm_value = sum(payout * share for payout, share in zip(payouts, normalized))
    return {"icm_value": round(icm_value, 2), "stack_share": normalized}
