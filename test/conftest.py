import os
import pytest


@pytest.fixture(autouse=True)
def enforce_raise_af_origin(monkeypatch):
    """
    Ensure tests run with Raise_AF gate satisfied.

    The enforcement policy requires ACTIFIX_CHANGE_ORIGIN=raise_af for any
    Actifix operations. Tests set it by default but can override per-case.
    """
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    yield
