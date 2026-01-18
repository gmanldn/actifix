from __future__ import annotations

from datetime import datetime, timezone

from actifix.raise_af import (
    ActifixEntry,
    TicketPriority,
    CONTEXT_TRUNCATION_CHARS,
    _compact_queue_entry,
    _truncate_context_text,
    preview_ai_remediation_notes,
)


def test_truncate_context_preserves_headers() -> None:
    long_tail = "line-tail"
    long_text = "line-start\n" + ("x" * (CONTEXT_TRUNCATION_CHARS * 2)) + f"\n{long_tail}"
    truncated = _truncate_context_text(long_text, CONTEXT_TRUNCATION_CHARS)

    assert "line-start" in truncated
    assert long_tail in truncated
    assert len(truncated) <= CONTEXT_TRUNCATION_CHARS + len("\n... (truncated) ...\n")


def test_preview_ai_remediation_notes_measures_tokens() -> None:
    entry = ActifixEntry(
        message="Sample failure for token robustness",
        source="test_raise_af_notes_and_context.py:42",
        run_label="test-run",
        entry_id="ACT-TEST-000",
        created_at=datetime.now(timezone.utc),
        priority=TicketPriority.P1,
        error_type="TestError",
        stack_trace="\n".join(f"frame {i}" for i in range(500)),
        file_context={"src/app.py": "line1\nline2\nline3"},
        system_state={"context_control": {"requested": True}},
    )

    notes, stats = preview_ai_remediation_notes(entry, max_chars=1024)

    assert "Root Cause" in notes
    assert stats["ai_notes_char_count"] <= 1024
    assert "Action" in notes
    assert stats["ai_notes_overflow"] >= 0


def test_compact_queue_entry_drops_empty_fields() -> None:
    payload = {
        "message": "  keep-me  ",
        "stack_trace": "   ",
        "file_context": {"empty.txt": "   ", "good.txt": "code snippet"},
        "system_state": {},
        "extra": None,
    }

    compacted = _compact_queue_entry(payload)

    assert compacted["message"] == "keep-me"
    assert "stack_trace" not in compacted
    assert compacted["file_context"] == {"good.txt": "code snippet"}
