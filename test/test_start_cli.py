"""Lightweight CLI coverage for the launcher arguments."""

import pytest

import scripts.start as start_launcher


def test_run_duration_flag_defaults_to_none():
    args = start_launcher.parse_args([])
    assert args.run_duration is None


def test_run_duration_flag_parses_float():
    args = start_launcher.parse_args(["--run-duration", "2.5"])
    assert pytest.approx(args.run_duration) == 2.5
