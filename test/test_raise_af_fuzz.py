#!/usr/bin/env python3
"""Fuzz tests for Raise_AF inputs."""

from __future__ import annotations

import random
import string

from actifix.raise_af import generate_duplicate_guard


def _random_text(rng: random.Random, length: int) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation + " \n\t"
    return "".join(rng.choice(alphabet) for _ in range(length))


def test_duplicate_guard_fuzz_inputs() -> None:
    rng = random.Random(1337)
    for _ in range(100):
        message = _random_text(rng, rng.randint(1, 200))
        stack_trace = _random_text(rng, rng.randint(0, 400))
        guard = generate_duplicate_guard("test/source.py:1", message, "ValueError", stack_trace)
        assert guard
