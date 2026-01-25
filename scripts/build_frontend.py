#!/usr/bin/env python3
"""
Build script for Actifix frontend.
Automatically synchronizes version from pyproject.toml to frontend files.
"""

import re
import shutil
import sys
from pathlib import Path


def get_version_from_pyproject(project_root: Path | None = None) -> str:
    """Extract version from pyproject.toml"""
    root = project_root or (Path(__file__).parent.parent)
    pyproject_path = root / "pyproject.toml"
    
    if not pyproject_path.exists():
        # Test harnesses may invoke build_frontend with a tmp_path that doesn't include
        # a pyproject. In that case, keep the build runnable and just skip version sync.
        print(f"Warning: {pyproject_path} not found; using version 0.0.0")
        return "0.0.0"
    
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Match version = "x.x.x" pattern
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print("Warning: Could not find version in pyproject.toml; using version 0.0.0")
        return "0.0.0"
    
    version = match.group(1)
    print(f"Found version: {version}")
    return version


def update_index_html(project_root: Path, version: str) -> None:
    """Update version in index.html"""
    index_path = project_root / "actifix-frontend" / "index.html"
    
    if not index_path.exists():
        print(f"Warning: {index_path} not found, skipping index.html update")
        return
    
    content = index_path.read_text(encoding='utf-8')
    
    # Update ACTIFIX_ASSET_VERSION
    content = re.sub(
        r'window\.ACTIFIX_ASSET_VERSION\s*=\s*"[^"]+"',
        f'window.ACTIFIX_ASSET_VERSION = "{version}"',
        content
    )
    
    # Update stylesheet version query parameter
    content = re.sub(
        r'href="\.\/styles\.css\?v=[^"]+"',
        f'href="./styles.css?v={version}"',
        content
    )
    
    # Update app.js version query parameter
    content = re.sub(
        r'src="\.\/app\.js\?v=[^"]+"',
        f'src="./app.js?v={version}"',
        content
    )
    
    index_path.write_text(content, encoding="utf-8")
    print(f"Updated {index_path}")


def update_app_js(project_root: Path, version: str) -> None:
    """Update version in app.js"""
    app_js_path = project_root / "actifix-frontend" / "app.js"
    
    if not app_js_path.exists():
        print(f"Warning: {app_js_path} not found, skipping app.js update")
        return
    
    content = app_js_path.read_text(encoding='utf-8')
    
    # Update UI_VERSION constant (supports both single and double quotes).
    def replace_ui_version(match: re.Match[str]) -> str:
        prefix = match.group(1)
        quote = match.group(2)
        return f"{prefix}{quote}{version}{quote}"

    content = re.sub(
        r"(const\s+UI_VERSION\s*=\s*)(['\"])[^'\"]*(['\"]);",
        lambda m: f"{m.group(1)}{m.group(2)}{version}{m.group(2)};",
        content,
    )
    # Backward compatibility for files missing the trailing semicolon pattern.
    content = re.sub(
        r"(const\s+UI_VERSION\s*=\s*)(['\"])[^'\"]*(['\"])",
        replace_ui_version,
        content,
    )
    
    app_js_path.write_text(content, encoding="utf-8")
    print(f"Updated {app_js_path}")

def _sync_dist(project_root: Path) -> Path:
    """Copy `actifix-frontend/` into `actifix-frontend/dist/` and return the dist path."""
    frontend_dir = project_root / "actifix-frontend"
    dist_dir = frontend_dir / "dist"
    dist_tmp = frontend_dir / ".dist.tmp"

    if not frontend_dir.exists():
        raise FileNotFoundError(frontend_dir)

    if dist_tmp.exists():
        shutil.rmtree(dist_tmp)
    dist_tmp.mkdir(parents=True, exist_ok=True)

    # Copy top-level files
    for name in ("index.html", "app.js", "styles.css"):
        src = frontend_dir / name
        if src.exists():
            shutil.copy2(src, dist_tmp / name)

    # Copy assets directory (if present)
    assets_src = frontend_dir / "assets"
    if assets_src.exists() and assets_src.is_dir():
        shutil.copytree(assets_src, dist_tmp / "assets", dirs_exist_ok=True)

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_tmp.replace(dist_dir)
    return dist_dir


def build_frontend(project_root: Path = None):
    """Build frontend - main entry point for imports."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("Actifix Frontend Build - Version Synchronization")
    print("=" * 60)
    
    # Get current version from pyproject.toml
    version = get_version_from_pyproject(project_root)
    
    # Update frontend files
    update_index_html(project_root, version)
    update_app_js(project_root, version)
    dist_dir = _sync_dist(project_root)
    
    print("=" * 60)
    print(f" Frontend version synchronized to {version}")
    print("=" * 60)
    return dist_dir


def main():
    """Main build function"""
    build_frontend()


if __name__ == "__main__":
    main()
