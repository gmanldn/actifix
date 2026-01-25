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


def test_header_and_nav_use_shared_tokens():
    """Dashboard header and nav elements must reference the shared spacing/family tokens."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    assert "dashboard-header" in content
    assert "gap: var(--spacing-lg)" in content
    assert "padding: 0 var(--spacing-xl)" in content
    assert "--nav-icon-size" in content
    assert "height: var(--nav-item-height)" in content


def test_metric_tiles_use_updated_layout():
    """Metric tiles should use the shared gaps and expose the new tag class."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    assert "metric-tile" in content
    assert "gap: var(--spacing-sm)" in content
    assert "min-height: 160px" in content
    assert "metric-tile-tag" in content


def test_ticket_filters_have_compact_styles():
    """Ticket filter bar styles should reference the shared chips and search field."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    assert "tickets-filter-bar" in content
    assert ".filter-chip" in content
    assert "filter-search" in content


def test_logs_view_additional_controls_present():
    """Logs view should expose the new summary grid, chip filters, and helper tokens."""
    content = BASE_CSS_PATH.read_text(encoding="utf-8")
    assert ".log-summary-grid" in content
    assert ".log-summary-card" in content
    assert ".log-chips" in content
    assert ".log-chip" in content
    assert "log-controls-actions" in content
    assert "log-updated-label" in content
