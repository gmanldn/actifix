#!/usr/bin/env python3
"""
Suggest pytest markers for tests based on code analysis.

Analyzes test files to identify:
- Tests using database fixtures (@pytest.fixture with db in name)
- Tests using API fixtures
- Tests using threading/concurrency
- Test execution time patterns
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TestMarkerAnalyzer(ast.NodeVisitor):
    """Analyzes test files for marker suggestions."""

    def __init__(self, file_path: Path):
        """Initialize analyzer."""
        self.file_path = file_path
        self.tests: Dict[str, Set[str]] = {}
        self.current_test = None
        self.in_test_class = False

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit test class."""
        if node.name.startswith("Test"):
            self.in_test_class = True
            self.generic_visit(node)
            self.in_test_class = False
        else:
            self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if node.name.startswith("test_"):
            self.current_test = node.name
            self.tests[node.name] = set()

            # Analyze function
            self._analyze_function(node)

            self.current_test = None

        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef):
        """Analyze a test function for patterns."""
        if not self.current_test:
            return

        # Check for database-related fixtures
        db_patterns = ["db", "clean_db", "database", "repo", "repository", "ticket", "event"]
        for arg in node.args.args:
            arg_name = arg.arg.lower()
            if any(pattern in arg_name for pattern in db_patterns):
                self.tests[self.current_test].add("db")
                self.tests[self.current_test].add("slow")
                self.tests[self.current_test].add("integration")

        # Check for API-related fixtures
        api_patterns = ["client", "app", "api"]
        for arg in node.args.args:
            arg_name = arg.arg.lower()
            if any(pattern in arg_name for pattern in api_patterns):
                self.tests[self.current_test].add("api")
                self.tests[self.current_test].add("integration")

        # Check for threading/concurrency
        for pattern in ast.walk(node):
            if isinstance(pattern, ast.Name):
                if pattern.id in ["threading", "Thread", "Lock", "concurrent"]:
                    self.tests[self.current_test].add("concurrent")
                    self.tests[self.current_test].add("slow")

            if isinstance(pattern, ast.Attribute):
                if pattern.attr in ["sleep", "wait"]:
                    self.tests[self.current_test].add("slow")

        # Check for existing markers
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if decorator.attr == "mark":
                    # Already has marker, could be optimized
                    pass

        # If no markers suggested but has fixtures, suggest unit
        if not self.tests[self.current_test]:
            # Check if simple (no arguments)
            if len(node.args.args) == 0:
                self.tests[self.current_test].add("unit")
            else:
                self.tests[self.current_test].add("integration")


def analyze_test_file(file_path: Path) -> Dict[str, Set[str]]:
    """Analyze a test file and return suggested markers."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = TestMarkerAnalyzer(file_path)
        analyzer.visit(tree)

        return analyzer.tests
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {}


def main():
    """Main entry point."""
    test_dir = Path("test")
    results = {}

    # Analyze all test files
    for test_file in sorted(test_dir.glob("test_*.py")):
        print(f"Analyzing {test_file.name}...", end=" ")

        markers = analyze_test_file(test_file)

        if markers:
            results[test_file.name] = markers
            print(f"✓ ({len(markers)} tests)")
        else:
            print("(no suggestions)")

    # Generate report
    print("\n" + "=" * 80)
    print("MARKER SUGGESTIONS")
    print("=" * 80)

    total_suggestions = 0
    by_marker = {}

    for file_name, tests in sorted(results.items()):
        for test_name, markers in sorted(tests.items()):
            if markers:
                total_suggestions += 1
                marker_str = ", ".join(sorted(markers))

                # Track by marker
                for marker in markers:
                    if marker not in by_marker:
                        by_marker[marker] = 0
                    by_marker[marker] += 1

                print(f"{file_name:40s} | {test_name:40s}")
                print(f"{'':40s} | @pytest.mark.{marker_str}")
                print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total suggestion markers: {total_suggestions}")
    print()

    print("Marker distribution:")
    for marker, count in sorted(by_marker.items(), key=lambda x: x[1], reverse=True):
        print(f"  @pytest.mark.{marker:15s}: {count:3d} tests")

    print()
    print("RECOMMENDATIONS:")
    print("-" * 80)

    if by_marker.get("slow", 0) > 50:
        print(f"✓ {by_marker['slow']} tests marked as slow - consider splitting test suite")
        print("  Strategy: Run 'pytest -m \"not slow\"' during development")
        print("  Strategy: Run slow tests in separate CI step")

    if by_marker.get("db", 0) > 0:
        print(f"✓ {by_marker['db']} database tests identified - may benefit from optimization")
        print("  Strategy: Use in-memory databases for tests")
        print("  Strategy: Batch database operations")
        print("  Strategy: Reduce fixture setup overhead")

    if by_marker.get("concurrent", 0) > 0:
        print(f"✓ {by_marker['concurrent']} concurrent tests - monitor for flakiness")
        print("  Strategy: Increase timeout tolerance")
        print("  Strategy: Use proper synchronization primitives")


if __name__ == "__main__":
    main()
