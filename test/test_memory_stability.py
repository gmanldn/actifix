#!/usr/bin/env python3
"""Stability test for detecting unexpected memory growth."""

from __future__ import annotations

import gc
import os
import tracemalloc

import pytest

pytestmark = [pytest.mark.very_slow, pytest.mark.performance]


def _allocation_workload() -> None:
    data = [bytearray(1024) for _ in range(1000)]
    del data


def test_memory_stability_guardrail() -> None:
    if not os.getenv("ACTIFIX_ENABLE_STABILITY_TESTS"):
        pytest.skip("Stability tests are disabled; set ACTIFIX_ENABLE_STABILITY_TESTS=1 to run.")

    tracemalloc.start()
    baseline = tracemalloc.take_snapshot()

    for _ in range(50):
        _allocation_workload()
        gc.collect()

    followup = tracemalloc.take_snapshot()
    tracemalloc.stop()

    growth_bytes = sum(
        stat.size_diff for stat in followup.compare_to(baseline, "lineno")
    )

    assert growth_bytes < 10 * 1024 * 1024, f"Unexpected growth detected: {growth_bytes} bytes"
