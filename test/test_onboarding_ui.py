from pathlib import Path


def test_onboarding_walkthrough_present():
    app_js = Path(__file__).parent.parent / "actifix-frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")
    assert "actifix_onboarding_v1" in content
    assert "OnboardingModal" in content
    assert "Welcome to Actifix" in content
