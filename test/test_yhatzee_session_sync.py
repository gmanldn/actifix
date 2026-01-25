"""Yhatzee session-sync UI smoke tests.

These tests intentionally treat the GUI as an embedded HTML/JS blob and only
assert that the key session-sync primitives are present. Browser-level behavior
is covered by manual verification.
"""


def test_yhatzee_metadata_declares_external_requests():
    from actifix.modules import yhatzee

    assert yhatzee.MODULE_METADATA["network"]["external_requests"] is True
    assert yhatzee.ACCESS_RULE == "local-only"


def test_yhatzee_html_includes_session_sync_primitives():
    from actifix.modules import yhatzee

    html = yhatzee._HTML_PAGE

    # Basic UI + key JS helpers. Keep these checks coarse to avoid brittle tests.
    assert "Session Sync" in html
    assert "normalizeSessionCode" in html
    assert 'baseUrl: "https://paste.rs"' in html
    assert 'method: "PUT"' in html
    assert 'method: "GET"' in html

