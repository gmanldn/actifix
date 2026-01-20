"""Utility to materialize the Actifix frontend bundle."""

from __future__ import annotations

import shutil
from pathlib import Path


def build_frontend(project_root: Path | str | None = None) -> Path:
    """Copy the frontend source into a dist bundle."""
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    frontend_dir = root / "actifix-frontend"
    dist_dir = frontend_dir / "dist"
    if not frontend_dir.exists():
        raise FileNotFoundError(f"Frontend directory missing: {frontend_dir}")

    dist_dir.mkdir(parents=True, exist_ok=True)

    for entry in ("index.html", "app.js", "styles.css"):
        src_file = frontend_dir / entry
        if not src_file.exists():
            raise FileNotFoundError(f"Missing frontend source file: {src_file}")
        shutil.copy2(src_file, dist_dir / entry)

    assets_src = frontend_dir / "assets"
    assets_dest = dist_dir / "assets"
    if assets_dest.exists():
        shutil.rmtree(assets_dest)
    if assets_src.exists():
        shutil.copytree(assets_src, assets_dest)

    return dist_dir


if __name__ == "__main__":
    build_frontend()
