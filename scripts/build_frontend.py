"""Utility to materialize the Actifix frontend bundle."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


def _get_version_from_pyproject(project_root: Path) -> str:
    """Extract version from pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    
    content = pyproject_path.read_text(encoding="utf-8")
    # Match version = "X.Y.Z" or version = 'X.Y.Z'
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def _update_frontend_version(frontend_dir: Path, version: str) -> None:
    """Update UI_VERSION in app.js to match the project version."""
    app_js_path = frontend_dir / "app.js"
    if not app_js_path.exists():
        raise FileNotFoundError(f"app.js not found at {app_js_path}")
    
    content = app_js_path.read_text(encoding="utf-8")
    
    # Replace UI_VERSION = 'X.Y.Z' or UI_VERSION = "X.Y.Z"
    pattern = r"(UI_VERSION\s*=\s*['\"])[^'\"]+(['\"])"
    
    def replacer(match):
        return match.group(1) + version + match.group(2)
    
    updated_content = re.sub(pattern, replacer, content)
    
    if updated_content == content:
        raise ValueError(f"UI_VERSION not found in {app_js_path}")
    
    app_js_path.write_text(updated_content, encoding="utf-8")


def build_frontend(project_root: Path | str | None = None) -> Path:
    """Copy the frontend source into a dist bundle."""
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    frontend_dir = root / "actifix-frontend"
    dist_dir = frontend_dir / "dist"
    if not frontend_dir.exists():
        raise FileNotFoundError(f"Frontend directory missing: {frontend_dir}")

    # Get version from pyproject.toml and update frontend
    version = _get_version_from_pyproject(root)
    _update_frontend_version(frontend_dir, version)
    print(f" Synced frontend version to {version}")

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