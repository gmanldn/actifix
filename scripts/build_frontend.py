#!/usr/bin/env python3
"""
Build script for Actifix frontend.
Automatically synchronizes version from pyproject.toml to frontend files.
"""

import re
import sys
from pathlib import Path


def get_version_from_pyproject():
    """Extract version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found")
        sys.exit(1)
    
    content = pyproject_path.read_text()
    
    # Match version = "x.x.x" pattern
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    version = match.group(1)
    print(f"Found version: {version}")
    return version


def update_index_html(version):
    """Update version in index.html"""
    index_path = Path(__file__).parent.parent / "actifix-frontend" / "index.html"
    
    if not index_path.exists():
        print(f"Warning: {index_path} not found, skipping index.html update")
        return
    
    content = index_path.read_text()
    
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
    
    index_path.write_text(content)
    print(f"Updated {index_path}")


def update_app_js(version):
    """Update version in app.js"""
    app_js_path = Path(__file__).parent.parent / "actifix-frontend" / "app.js"
    
    if not app_js_path.exists():
        print(f"Warning: {app_js_path} not found, skipping app.js update")
        return
    
    content = app_js_path.read_text()
    
    # Update UI_VERSION constant
    content = re.sub(
        r'const\s+UI_VERSION\s*=\s*"[^"]+"',
        f'const UI_VERSION = "{version}"',
        content
    )
    
    app_js_path.write_text(content)
    print(f"Updated {app_js_path}")


def build_frontend(project_root: Path = None):
    """Build frontend - main entry point for imports."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("Actifix Frontend Build - Version Synchronization")
    print("=" * 60)
    
    # Get current version from pyproject.toml
    version = get_version_from_pyproject()
    
    # Update frontend files
    update_index_html(version)
    update_app_js(version)
    
    print("=" * 60)
    print(f" Frontend version synchronized to {version}")
    print("=" * 60)


def main():
    """Main build function"""
    build_frontend()


if __name__ == "__main__":
    main()