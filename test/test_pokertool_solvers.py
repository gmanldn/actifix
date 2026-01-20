from __future__ import annotations

import pytest

from actifix.modules.pokertool.solvers import (
    PokerToolSolverError,
    compute_nash_equilibrium,
    estimate_icm_value,
)


def test_compute_nash_equilibrium_returns_recommendation() -> None:
    recommendation = compute_nash_equilibrium(["Ah", "Kd"], ["9h", "Ts"])
    assert recommendation.equity >= 40.0
    assert recommendation.action in {"raise", "call", "fold"}


def test_compute_nash_equilibrium_requires_hand() -> None:
    with pytest.raises(PokerToolSolverError):
        compute_nash_equilibrium([])


def test_estimate_icm_value_requires_inputs() -> None:
    with pytest.raises(PokerToolSolverError):
        estimate_icm_value([], [])


def test_estimate_icm_value_computes_share() -> None:
    result = estimate_icm_value([100.0, 50.0], [5.0, 2.5])
    assert "icm_value" in result
    assert result["stack_share"][0] > result["stack_share"][1]
