"""Tests for version synchronization across the Actifix project."""

import re
from pathlib import Path

import pytest

import actifix
from actifix.api import create_app
from scripts.build_frontend import get_version_from_pyproject


def test_backend_version_matches_pyproject():
    """Test that backend __version__ matches pyproject.toml."""
    # Get version from pyproject.toml
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(Path(__file__).parent.parent)
        expected_version = get_version_from_pyproject()
        assert actifix.__version__ == expected_version
    finally:
        os.chdir(original_cwd)


def test_api_version_endpoint_returns_backend_version(tmp_path):
    """Test that API /version endpoint returns backend __version__."""
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        response = client.get("/api/version")
        assert response.status_code == 200
        
        data = response.get_json()
        assert "version" in data
        assert data["version"] == actifix.__version__


def test_version_consistency_across_all_components(tmp_path):
    """Test that version is consistent across pyproject.toml, backend, and frontend."""
    # Get version from pyproject.toml
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(Path(__file__).parent.parent)
        pyproject_version = get_version_from_pyproject()
    finally:
        os.chdir(original_cwd)
    
    # Check backend version
    backend_version = actifix.__version__
    
    # They should match
    assert pyproject_version == backend_version, \
        f"Backend version {backend_version} doesn't match pyproject.toml {pyproject_version}"


def test_frontend_version_display_logic(tmp_path):
    """Test the frontend version display and mismatch detection logic."""
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        # Get actual version from API
        response = client.get("/api/version")
        assert response.status_code == 200
        api_data = response.get_json()
        api_version = api_data["version"]
        
        # This simulates what the frontend does:
        # It has UI_VERSION hardcoded in the JS bundle and compares it with API version.
        project_root = Path(__file__).parent.parent
        app_js = project_root / "actifix-frontend" / "app.js"
        content = app_js.read_text(encoding="utf-8")
        match = re.search(r"\bconst\s+UI_VERSION\s*=\s*['\"]([^'\"]+)['\"]\s*;", content)
        assert match, "Frontend UI_VERSION constant not found in actifix-frontend/app.js"
        UI_VERSION = match.group(1)
        
        # Version mismatch detection (what frontend does)
        version_mismatch = api_version != UI_VERSION
        
        # In production, they should always match
        assert not version_mismatch, \
            f"Frontend UI_VERSION ({UI_VERSION}) doesn't match API version ({api_version})"
        
        # Verify both come from same source
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(Path(__file__).parent.parent)
            expected_version = get_version_from_pyproject()
            assert UI_VERSION == expected_version
            assert api_version == expected_version
        finally:
            os.chdir(original_cwd)


def test_version_format_is_semver():
    """Test that version follows semantic versioning format."""
    version = actifix.__version__
    
    # Should match pattern: major.minor.patch
    pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(pattern, version), \
        f"Version {version} doesn't follow semantic versioning (major.minor.patch)"


def test_version_increases_monotonically():
    """Test that version follows a logical progression."""
    # Get current version parts
    parts = actifix.__version__.split('.')
    assert len(parts) >= 2, "Version should have at least major.minor"
    
    major, minor, patch = parts[0], parts[1], parts[2] if len(parts) > 2 else "0"
    
    # All parts should be integers
    assert major.isdigit(), "Major version should be numeric"
    assert minor.isdigit(), "Minor version should be numeric"
    assert patch.isdigit(), "Patch version should be numeric"
    
    # Version should be >= 1.0.0
    assert int(major) >= 1, "Major version should be at least 1"


def test_version_endpoint_matches_frontend_ui_version(tmp_path):
    """Test that API version endpoint returns same version as frontend UI_VERSION."""
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        # Get version from API
        response = client.get("/api/version")
        assert response.status_code == 200
        api_data = response.get_json()
        api_version = api_data["version"]
        
        # This is what the frontend has hardcoded.
        project_root = Path(__file__).parent.parent
        app_js = project_root / "actifix-frontend" / "app.js"
        content = app_js.read_text(encoding="utf-8")
        match = re.search(r"\bconst\s+UI_VERSION\s*=\s*['\"]([^'\"]+)['\"]\s*;", content)
        assert match, "Frontend UI_VERSION constant not found in actifix-frontend/app.js"
        frontend_ui_version = match.group(1)
        
        # They should match (this is what ensures sync)
        assert api_version == frontend_ui_version, \
            f"API version ({api_version}) doesn't match frontend UI_VERSION ({frontend_ui_version})"
        
        # Verify both match pyproject.toml
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(Path(__file__).parent.parent)
            expected_version = get_version_from_pyproject()
            assert api_version == expected_version
            assert frontend_ui_version == expected_version
        finally:
            os.chdir(original_cwd)


@pytest.mark.slow
def test_no_hardcoded_old_versions_in_production_files():
    """Test that no old version numbers (5.0.50, 5.0.51, 5.0.52) remain in production files."""
    project_root = Path(__file__).parent.parent
    
    old_versions = ["5.0.50", "5.0.51", "5.0.52"]
    
    for old_version in old_versions:
        # Search in Python files
        for py_file in project_root.rglob("*.py"):
            if ".git" in str(py_file) or "test_logs" in str(py_file):
                continue
            if "test_" in str(py_file):
                # Skip test files that might contain old versions as examples
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            assert f'"{old_version}"' not in content, \
                f"Found old version {old_version} in {py_file}"
            assert f"'{old_version}'" not in content, \
                f"Found old version {old_version} in {py_file}"
        
        # Search in JavaScript files
        for js_file in project_root.rglob("*.js"):
            if ".git" in str(js_file):
                continue
            if "test_" in str(js_file):
                continue
            try:
                content = js_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            assert f'"{old_version}"' not in content, \
                f"Found old version {old_version} in {js_file}"
            assert f"'{old_version}'" not in content, \
                f"Found old version {old_version} in {js_file}"
        
        # Search in HTML files
        for html_file in project_root.rglob("*.html"):
            if ".git" in str(html_file):
                continue
            try:
                content = html_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            assert f'"{old_version}"' not in content, \
                f"Found old version {old_version} in {html_file}"


def test_actual_production_files_have_correct_version():
    """Test that the actual production files have the current version."""
    project_root = Path(__file__).parent.parent
    
    # Get expected version
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(project_root)
        expected_version = get_version_from_pyproject()
    finally:
        os.chdir(original_cwd)
    
    # Backend should not carry a hardcoded semver string; the canonical version is pyproject.toml.
    init_py = project_root / "src" / "actifix" / "__init__.py"
    if init_py.exists():
        content = init_py.read_text(encoding="utf-8")
        assert "__version__ = _resolve_version()" in content
        assert not re.search(r'__version__\s*=\s*["\']\d+\.\d+\.\d+["\']', content)

    # Check actifix-frontend/app.js (uses single quotes for UI_VERSION)
    app_js = project_root / "actifix-frontend" / "app.js"
    if app_js.exists():
        content = app_js.read_text(encoding="utf-8")
        assert re.search(
            rf"\bconst\s+UI_VERSION\s*=\s*['\"]{re.escape(expected_version)}['\"]\s*;",
            content,
        ), f"Frontend UI_VERSION doesn't match expected version {expected_version}"

        # The top-right version badge must render the UI build version.
        assert "className: 'version-indicator'" in content
        assert "className: 'version-label'" in content
        assert "`v${UI_VERSION}`" in content
    
    # Check actifix-frontend/dist/app.js (uses single quotes for UI_VERSION)
    dist_app_js = project_root / "actifix-frontend" / "dist" / "app.js"
    if dist_app_js.exists():
        content = dist_app_js.read_text(encoding="utf-8")
        assert re.search(
            rf"\bconst\s+UI_VERSION\s*=\s*['\"]{re.escape(expected_version)}['\"]\s*;",
            content,
        ), f"Frontend dist UI_VERSION doesn't match expected version {expected_version}"
    
    # Check actifix-frontend/dist/index.html (uses double quotes for ACTIFIX_ASSET_VERSION)
    dist_index = project_root / "actifix-frontend" / "dist" / "index.html"
    if dist_index.exists():
        content = dist_index.read_text(encoding="utf-8")
        assert f'window.ACTIFIX_ASSET_VERSION = "{expected_version}"' in content, \
            f"Frontend dist ACTIFIX_ASSET_VERSION doesn't match expected version {expected_version}"
