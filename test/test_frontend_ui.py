import pytest
from pathlib import Path

def test_index_html_contains_required_tags():
    index_path = Path("actifix-frontend") / "index.html"
    content = index_path.read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="./styles.css?v=2.7.8">' in content, "styles.css link missing"
    assert '<script src="./app.js"></script>' in content, "app.js script tag missing"
    assert '<link rel="icon" href="./assets/pangolin.svg"' in content, "favicon link missing"

def test_styles_css_contains_corporate_palette():
    css_path = Path("actifix-frontend") / "styles.css"
    content = css_path.read_text(encoding="utf-8")
    assert "--accent: #3b82f6;" in content, "Corporate accent color missing"
    assert "--bg-primary: #111827;" in content, "Corporate background color missing"


def test_app_js_system_view_enhancements():
    """Test SystemView enhancements and no regressions."""
    app_path = Path("actifix-frontend") / "app.js"
    content = app_path.read_text(encoding="utf-8")
    
    # Regression: core components present
    assert 'SystemView' in content
    assert 'stats-grid' in content
    assert 'MetricTile' in content
    assert 'navItems' in content
    assert "{ id: 'system', icon: '™'" in content, "System nav cog icon missing"
    
    # New features
    assert 'HEALTH' in content
    assert 'DISK' in content
    assert 'GIT' in content
    assert 'getDiskColor' in content
    assert 'paths-table' in content
    assert 'git-table' in content
    assert 'recent_events' in content
    assert 'PATHS' in content
    assert 'GIT STATUS' in content
    assert 'RECENT EVENTS' in content


def test_app_js_nav_rail_cog():
    """Ensure clear cog icon for System panel."""
    app_path = Path("actifix-frontend") / "app.js"
    content = app_path.read_text(encoding="utf-8")
    assert "{ id: 'system', icon: '™', label: 'System' }" in content, "System cog icon regression"
    assert 'nav-rail-logo' in content, "AF pangolin.svg logo present"