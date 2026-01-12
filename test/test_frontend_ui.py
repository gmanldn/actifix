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
