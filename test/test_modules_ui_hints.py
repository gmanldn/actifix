from pathlib import Path


def test_modules_view_includes_critical_warning():
    app_js = Path(__file__).parent.parent / "actifix-frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")
    assert 'Critical module' in content
    assert 'critical-chip' in content
