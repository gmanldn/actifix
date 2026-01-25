from pathlib import Path


BASE_CSS_PATH = Path(__file__).parent.parent / "actifix-frontend" / "styles.css"


def test_typography_tokens_defined():
    """Ensure the CSS defines the shared typography and spacing tokens."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    assert "--font-family-sans" in content
    assert "--font-family-mono" in content
    assert "--text-base" in content
    assert "--spacing-md" in content


def test_ticket_card_uses_fluid_spacing():
    """Ticket cards should use the new spacing tokens and sans family."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    ticket_card_block = "ticket-card"
    assert "ticket-card" in content
    assert "padding: var(--spacing-md)" in content
    assert "font-family: var(--font-family-sans)" in content
