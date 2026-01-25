#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Root launcher shim.

Keep this file tiny: it delegates to `scripts/start.py` so `python3 start.py`
works reliably (and doesn’t depend on symlink semantics).
"""

from __future__ import annotations

from pathlib import Path
import runpy


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    runpy.run_path(str(repo_root / "scripts" / "start.py"), run_name="__main__")


if __name__ == "__main__":
    main()
