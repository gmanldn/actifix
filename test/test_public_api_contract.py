#!/usr/bin/env python3
"""Contract tests for the public Actifix API surface."""

from __future__ import annotations

import inspect

import actifix


EXPECTED_PUBLIC_EXPORTS = {
    "record_error": {"required": {"message", "source"}},
    "enable_actifix_capture": {"required": set()},
    "disable_actifix_capture": {"required": set()},
    "track_development_progress": {"required": {"milestone"}},
    "get_health": {"required": set()},
    "run_health_check": {"required": set()},
}


def _required_param_names(func) -> set[str]:
    signature = inspect.signature(func)
    required = set()
    for param in signature.parameters.values():
        if param.default is inspect._empty and param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            required.add(param.name)
    return required


def test_public_exports_present() -> None:
    for name in EXPECTED_PUBLIC_EXPORTS:
        assert name in actifix.__all__
        assert hasattr(actifix, name)


def test_public_export_signatures_stable() -> None:
    for name, expectations in EXPECTED_PUBLIC_EXPORTS.items():
        func = getattr(actifix, name)
        assert expectations["required"].issubset(_required_param_names(func))
