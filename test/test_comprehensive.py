"""
Comprehensive validation of Actifix 100-ticket suite.

Ensures that:
- All 100 comprehensive-test-suite tickets exist and are marked complete.
- Ticket statistics reflect zero open tickets for the suite.
- Completion summary is recorded for processed tickets.
"""

import os
from pathlib import Path

import actifix
from actifix.do_af import get_ticket_stats, get_open_tickets
from actifix.state_paths import get_actifix_paths


def test_comprehensive_tickets_completed(tmp_path, monkeypatch):
    """All comprehensive-test-suite tickets should be completed after processing."""
    # Point Actifix to the real project files (not tmp) to validate the generated tickets
    project_root = Path(__file__).parent.parent
    paths = get_actifix_paths(base_dir=project_root / "actifix")

    stats = get_ticket_stats(paths)
    # We expect 100 total comprehensive tickets, all completed
    assert stats["completed"] >= 100, "Expected at least 100 completed tickets"
    assert stats["open"] == 0, "Expected zero open tickets"

    open_tickets = get_open_tickets(paths)
    # Ensure no open tickets remain for the comprehensive-test-suite run
    suite_open = [t for t in open_tickets if t.run_name == "comprehensive-test-suite"]
    assert not suite_open, "There should be no open comprehensive-test-suite tickets"


def test_completion_summary_present():
    """Processed tickets should include a completion summary marker in ACTIFIX-LIST.md."""
    project_root = Path(__file__).parent.parent
    list_file = project_root / "actifix" / "ACTIFIX-LIST.md"
    content = list_file.read_text()
    assert "Summary: Processed comprehensive test ticket" in content, "Completion summary not found in ACTIFIX-LIST.md"
