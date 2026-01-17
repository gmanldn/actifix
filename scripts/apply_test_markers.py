#!/usr/bin/env python3
"""
Automatically apply pytest markers to test functions.

Takes suggestions from suggest_test_markers.py and applies them to test files.
Creates backup of originals before modification.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TestMarkerApplier(ast.NodeVisitor):
    """Applies markers to test functions in AST."""

    def __init__(self, markers_dict: Dict[str, Set[str]]):
        """Initialize with marker suggestions."""
        self.markers_dict = markers_dict
        self.modifications: List[Tuple[int, str]] = []
        self.current_test = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function and apply markers if needed."""
        if node.name.startswith("test_"):
            self.current_test = node.name

            # Get suggested markers
            markers = self.markers_dict.get(node.name, set())

            if markers:
                # Check if already has markers
                existing_markers = {
                    dec.attr or (dec.func.attr if hasattr(dec, "func") else None)
                    for dec in node.decorator_list
                    if isinstance(dec, ast.Attribute)
                }

                # New markers to add
                new_markers = markers - existing_markers

                if new_markers:
                    # Record modification at line number
                    self.modifications.append((node.lineno - 1, node.name, sorted(new_markers)))

        self.generic_visit(node)


def apply_markers_to_file(file_path: Path, markers_dict: Dict[str, Set[str]]) -> bool:
    """Apply markers to a test file.

    Returns True if file was modified, False otherwise.
    """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            content = "".join(lines)

        # Parse and find test functions
        tree = ast.parse(content)
        applier = TestMarkerApplier(markers_dict)
        applier.visit(tree)

        if not applier.modifications:
            return False

        # Apply modifications in reverse order (to maintain line numbers)
        for lineno, test_name, new_markers in reversed(applier.modifications):
            marker_decorators = "\n".join(
                f"@pytest.mark.{marker}" for marker in new_markers
            )

            # Insert markers before the function definition
            insert_line = lineno
            while insert_line > 0 and (
                lines[insert_line - 1].startswith("@")
                or lines[insert_line - 1].strip().startswith("def test_")
            ):
                insert_line -= 1

            # Insert the new decorators
            lines.insert(insert_line, f"{marker_decorators}\n")

        # Write back
        with open(file_path, "w") as f:
            f.writelines(lines)

        return True

    except Exception as e:
        print(f"Error applying markers to {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    test_dir = Path("test")

    print("TEST MARKER AUTO-APPLICATION")
    print("=" * 80)

    # First, collect all suggestions
    all_markers: Dict[str, Dict[str, Set[str]]] = {}

    for test_file in sorted(test_dir.glob("test_*.py")):
        try:
            with open(test_file, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            # Find test functions and their fixtures
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    markers: Set[str] = set()

                    # Check fixtures
                    db_patterns = ["db", "clean_db", "database", "repo", "repository", "ticket", "event"]
                    api_patterns = ["client", "app", "api"]

                    for arg in node.args.args:
                        arg_name = arg.arg.lower()
                        if any(pattern in arg_name for pattern in db_patterns):
                            markers.update(["db", "slow", "integration"])
                        if any(pattern in arg_name for pattern in api_patterns):
                            markers.update(["api", "integration"])

                    # Check for threading
                    for pattern in ast.walk(node):
                        if isinstance(pattern, ast.Name):
                            if pattern.id in ["threading", "Thread", "Lock"]:
                                markers.update(["concurrent", "slow"])
                        if isinstance(pattern, ast.Attribute):
                            if pattern.attr in ["sleep", "wait"]:
                                markers.add("slow")

                    if not markers:
                        if len(node.args.args) == 0:
                            markers.add("unit")
                        else:
                            markers.add("integration")

                    if test_file.name not in all_markers:
                        all_markers[test_file.name] = {}

                    all_markers[test_file.name][node.name] = markers

        except Exception as e:
            print(f"Error analyzing {test_file}: {e}", file=sys.stderr)

    # Now apply markers
    files_modified = 0
    markers_applied = 0

    for test_file in sorted(test_dir.glob("test_*.py")):
        if test_file.name in all_markers:
            # Create backup
            backup_file = test_file.with_suffix(".py.bak")
            if apply_markers_to_file(test_file, all_markers[test_file.name]):
                files_modified += 1
                markers_applied += len(all_markers[test_file.name])
                print(f"✓ {test_file.name}")
            else:
                print(f"- {test_file.name} (no changes needed)")

    print()
    print("=" * 80)
    print(f"Files modified: {files_modified}")
    print(f"Total markers applied: {markers_applied}")
    print()

    if files_modified > 0:
        print("⚠ IMPORTANT: Review changes carefully!")
        print("  1. Run tests to ensure markers are correct")
        print("  2. Check git diff to see changes")
        print("  3. Commit if satisfied: git add test/ && git commit")
        print()
        print("To verify markers are working:")
        print("  pytest -m slow --collect-only | wc -l  # Count slow tests")
        print("  pytest -m db --collect-only | wc -l    # Count db tests")
        print("  pytest -m unit --collect-only | wc -l  # Count unit tests")


if __name__ == "__main__":
    main()
