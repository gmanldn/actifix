"""
Comprehensive validation of Actifix 100-ticket suite.

Ensures that:
- All 100 comprehensive-test-suite tickets exist
- Tickets are in the Completed Items section
- Completion summary is recorded for processed tickets
"""

import re
from pathlib import Path


def test_comprehensive_tickets_exist():
    """All 100 comprehensive test tickets should exist in ACTIFIX-LIST.md."""
    project_root = Path(__file__).parent.parent
    list_file = project_root / "actifix" / "ACTIFIX-LIST.md"
    content = list_file.read_text()
    
    # Count T001-T100 tickets
    t_tickets = []
    for i in range(1, 101):
        pattern = f"T{i:03d}:"
        if pattern in content:
            t_tickets.append(pattern)
    
    assert len(t_tickets) == 100, f"Expected 100 T0xx tickets, found {len(t_tickets)}"


def test_comprehensive_tickets_in_completed_section():
    """Comprehensive test tickets should be in the Completed Items section."""
    project_root = Path(__file__).parent.parent
    list_file = project_root / "actifix" / "ACTIFIX-LIST.md"
    content = list_file.read_text()
    
    # Split by sections
    if "## Completed Items" not in content:
        assert False, "No Completed Items section found"
    
    completed_section = content.split("## Completed Items")[1] if len(content.split("## Completed Items")) > 1 else ""
    
    # Count T001-T100 tickets in Completed section
    completed_t_tickets = 0
    for i in range(1, 101):
        pattern = f"T{i:03d}:"
        if pattern in completed_section:
            completed_t_tickets += 1
    
    # At least 90% should be in Completed section (allows for some still processing)
    assert completed_t_tickets >= 90, f"Expected at least 90 tickets in Completed section, found {completed_t_tickets}"


def test_completion_summary_present():
    """Processed tickets should include a completion summary marker in ACTIFIX-LIST.md."""
    project_root = Path(__file__).parent.parent
    list_file = project_root / "actifix" / "ACTIFIX-LIST.md"
    content = list_file.read_text()
    assert "Summary: Processed comprehensive test ticket" in content, "Completion summary not found in ACTIFIX-LIST.md"
