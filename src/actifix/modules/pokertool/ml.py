"""Machine-learning helpers for PokerTool opponent modelling."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable


class PokerToolMLError(ValueError):
    """Raised when ML inputs are invalid."""


@dataclass(frozen=True)
class OpponentProfile:
    tendencies: dict[str, float]
    aggression_score: float
    confidence: float


def build_opponent_model(history: Iterable[dict[str, object]]) -> OpponentProfile:
    entries = list(history)
    if not entries:
        raise PokerToolMLError("History is required to build an opponent model.")
    action_counts: dict[str, int] = {}
    aggression_values: list[float] = []
    for entry in entries:
        action = str(entry.get("action") or "unknown").lower()
        aggression = float(entry.get("aggression", 0.5))
        action_counts[action] = action_counts.get(action, 0) + 1
        aggression_values.append(aggression)
    total = sum(action_counts.values())
    tendencies = {action: count / total for action, count in action_counts.items()}
    aggression_score = min(max(mean(aggression_values), 0.0), 1.0)
    confidence = min(0.9, 0.5 + len(entries) * 0.05)
    return OpponentProfile(
        tendencies=tendencies,
        aggression_score=round(aggression_score, 2),
        confidence=round(confidence, 2),
    )


def active_learning_hint(scores: Iterable[float]) -> dict[str, object]:
    values = list(scores)
    if not values:
        raise PokerToolMLError("At least one score is required for active learning.")
    target_index = int(len(values) * 0.6) % len(values)
    return {
        "suggested_index": target_index,
        "value": round(values[target_index], 3),
        "spread": round(max(values) - min(values), 3),
    }
