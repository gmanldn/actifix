from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_root_symlinks_point_to_expected_sources():
    """Ensure the helper scripts and API surface stay available at the project root."""
    mappings = [
        ("view_tickets.py", "scripts/view_tickets.py"),
        ("query_tickets.py", "scripts/query_open_tickets.py"),
        ("raise_af.py", "src/actifix/raise_af.py"),
    ]

    for link_name, expected_target in mappings:
        link_path = ROOT / link_name
        assert link_path.exists(), f"{link_name} should exist in the repository root"
        assert link_path.is_symlink(), f"{link_name} should be a symlink"

        resolved = link_path.resolve()
        expected = (ROOT / expected_target).resolve()
        assert resolved == expected, f"{link_name} must point to {expected_target}"
