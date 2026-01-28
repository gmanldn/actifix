from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"


def _read_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_index_links_to_framework_overview() -> None:
    """The docs index should reference the framework overview."""
    index_content = _read_doc(DOCS_DIR / "INDEX.md")
    assert "FRAMEWORK_OVERVIEW.md" in index_content, (
        "docs/INDEX.md must reference FRAMEWORK_OVERVIEW.md so cross links stay discoverable."
    )


def test_framework_overview_mentions_index() -> None:
    """The framework overview should mention the docs index so readers can jump back."""
    overview_content = _read_doc(DOCS_DIR / "FRAMEWORK_OVERVIEW.md")
    assert "docs/INDEX.md" in overview_content, (
        "docs/FRAMEWORK_OVERVIEW.md should reference docs/INDEX.md to close the cross-reference loop."
    )
