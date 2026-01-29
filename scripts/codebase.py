#!/usr/bin/env python3
"""
Codebase Explorer for AI Agents

This script provides AI agents with comprehensive codebase navigation and file inspection
capabilities. It is designed to be the primary tool for AI agents to understand the Actifix
codebase structure, locate files, and read their contents.

USAGE FOR AI AGENTS:
===================

1. List all files with sizes and modification dates:
   python3 codebase.py --list

2. Show files matching a pattern:
   python3 codebase.py --list --pattern "*.py"

3. Show files in a specific directory:
   python3 codebase.py --list --path src/actifix/modules

4. Read a specific file:
   python3 codebase.py --read src/actifix/raise_af.py

5. Search for files containing text:
   python3 codebase.py --search "record_error"

6. Show codebase statistics:
   python3 codebase.py --stats

WHY AI AGENTS SHOULD USE THIS:
==============================

- Get a complete view of the codebase structure
- Find files by name, path, or content
- See file sizes and modification dates to identify recently changed files
- Read file contents without needing to know exact paths
- Understand which areas of the codebase are most active

IMPORTANT PATTERNS:
==================

Before making changes:
  1. Use --list to see all relevant files
  2. Use --read to examine specific files
  3. Check --stats to understand codebase size and composition

When investigating issues:
  1. Use --search to find relevant code
  2. Use --list --pattern to find related files
  3. Use --read to examine implementation details

EXAMPLES:
========

# Find all test files
python3 codebase.py --list --pattern "test_*.py"

# Find persistence modules
python3 codebase.py --list --path src/actifix/persistence

# Read the main API file
python3 codebase.py --read src/actifix/api.py

# Search for ticket-related code
python3 codebase.py --search "mark_ticket_complete"

# Get overview statistics
python3 codebase.py --stats
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class CodebaseExplorer:
    """Explore and inspect the Actifix codebase."""

    def __init__(self, root: Path | None = None):
        """Initialize explorer.

        Args:
            root: Project root directory (auto-detected if None)
        """
        if root is None:
            root = Path(__file__).resolve().parent.parent
        self.root = root

        # Directories to exclude from exploration
        self.exclude_dirs = {
            '__pycache__',
            '.git',
            '.pytest_cache',
            '.actifix',
            'node_modules',
            '.venv',
            'venv',
            'dist',
            'build',
            '*.egg-info',
            '.DS_Store',
        }

        # File patterns to exclude
        self.exclude_files = {
            '*.pyc',
            '*.pyo',
            '*.db',
            '*.db-journal',
            '*.log',
            '.DS_Store',
        }

    def should_include_path(self, path: Path) -> bool:
        """Check if path should be included in exploration.

        Args:
            path: Path to check

        Returns:
            True if path should be included
        """
        # Check directory exclusions
        for part in path.parts:
            if part in self.exclude_dirs or part.startswith('.'):
                return False

        # Check file pattern exclusions
        for pattern in self.exclude_files:
            if fnmatch.fnmatch(path.name, pattern):
                return False

        return True

    def list_files(
        self,
        pattern: str | None = None,
        relative_path: str | None = None,
        include_hidden: bool = False,
    ) -> List[Dict[str, Any]]:
        """List all files in the codebase with metadata.

        Args:
            pattern: Optional glob pattern to filter files (e.g., "*.py")
            relative_path: Optional path relative to root to search within
            include_hidden: Include hidden files/directories

        Returns:
            List of file metadata dictionaries
        """
        search_root = self.root / relative_path if relative_path else self.root
        files = []

        for path in search_root.rglob('*'):
            if not path.is_file():
                continue

            # Skip hidden files unless explicitly included
            if not include_hidden and not self.should_include_path(path):
                continue

            # Apply pattern filter if specified
            if pattern and not fnmatch.fnmatch(path.name, pattern):
                continue

            try:
                stat = path.stat()
                relative = path.relative_to(self.root)

                files.append({
                    'path': str(relative),
                    'name': path.name,
                    'size': stat.st_size,
                    'size_human': self._format_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'modified_human': self._format_time_ago(stat.st_mtime),
                    'extension': path.suffix,
                })
            except (OSError, ValueError) as e:
                # Skip files that can't be accessed
                continue

        # Sort by path
        files.sort(key=lambda f: f['path'])
        return files

    def read_file(self, relative_path: str, max_lines: int | None = None) -> Dict[str, Any]:
        """Read file contents.

        Args:
            relative_path: Path relative to project root
            max_lines: Optional maximum number of lines to read

        Returns:
            Dictionary with file metadata and contents
        """
        path = self.root / relative_path

        if not path.exists():
            return {
                'error': 'File not found',
                'path': relative_path,
                'exists': False,
            }

        if not path.is_file():
            return {
                'error': 'Path is not a file',
                'path': relative_path,
                'is_file': False,
            }

        try:
            stat = path.stat()

            # Try to read as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    if max_lines:
                        lines = [f.readline() for _ in range(max_lines)]
                        content = ''.join(lines)
                        truncated = True
                    else:
                        content = f.read()
                        truncated = False

                return {
                    'path': relative_path,
                    'size': stat.st_size,
                    'size_human': self._format_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'lines': content.count('\n') + 1 if not truncated else max_lines,
                    'content': content,
                    'truncated': truncated,
                    'encoding': 'utf-8',
                }
            except UnicodeDecodeError:
                return {
                    'error': 'Binary file (cannot display as text)',
                    'path': relative_path,
                    'size': stat.st_size,
                    'size_human': self._format_size(stat.st_size),
                    'is_binary': True,
                }

        except Exception as e:
            return {
                'error': f'Error reading file: {e}',
                'path': relative_path,
            }

    def search_content(self, query: str, file_pattern: str | None = None) -> List[Dict[str, Any]]:
        """Search for text in files.

        Args:
            query: Text to search for
            file_pattern: Optional pattern to filter files (e.g., "*.py")

        Returns:
            List of matches with file path, line number, and context
        """
        matches = []
        files = self.list_files(pattern=file_pattern)

        for file_info in files:
            path = self.root / file_info['path']

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query in line:
                            matches.append({
                                'path': file_info['path'],
                                'line': line_num,
                                'content': line.rstrip(),
                            })
            except (UnicodeDecodeError, OSError):
                # Skip binary files or files that can't be read
                continue

        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Get codebase statistics.

        Returns:
            Dictionary with codebase statistics
        """
        files = self.list_files()

        stats = {
            'total_files': len(files),
            'total_size': sum(f['size'] for f in files),
            'total_size_human': self._format_size(sum(f['size'] for f in files)),
            'by_extension': {},
            'largest_files': sorted(files, key=lambda f: f['size'], reverse=True)[:10],
            'recently_modified': sorted(files, key=lambda f: f['modified'], reverse=True)[:10],
        }

        # Count by extension
        for file_info in files:
            ext = file_info['extension'] or '(no extension)'
            if ext not in stats['by_extension']:
                stats['by_extension'][ext] = {'count': 0, 'size': 0}
            stats['by_extension'][ext]['count'] += 1
            stats['by_extension'][ext]['size'] += file_info['size']

        # Format extension stats
        for ext, data in stats['by_extension'].items():
            data['size_human'] = self._format_size(data['size'])

        return stats

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _format_time_ago(self, timestamp: float) -> str:
        """Format timestamp as relative time.

        Args:
            timestamp: Unix timestamp

        Returns:
            Human-readable relative time
        """
        now = datetime.now().timestamp()
        diff = now - timestamp

        if diff < 60:
            return "just now"
        elif diff < 3600:
            mins = int(diff / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(diff / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Codebase explorer for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all files with metadata',
    )
    parser.add_argument(
        '--read',
        metavar='PATH',
        help='Read a specific file',
    )
    parser.add_argument(
        '--search',
        metavar='QUERY',
        help='Search for text in files',
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show codebase statistics',
    )
    parser.add_argument(
        '--pattern',
        metavar='PATTERN',
        help='Filter files by pattern (e.g., "*.py")',
    )
    parser.add_argument(
        '--path',
        metavar='PATH',
        help='Search within specific path',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format',
    )
    parser.add_argument(
        '--max-lines',
        type=int,
        metavar='N',
        help='Maximum lines to read from file',
    )

    args = parser.parse_args()

    # Require at least one action
    if not any([args.list, args.read, args.search, args.stats]):
        parser.print_help()
        return 1

    explorer = CodebaseExplorer()

    if args.list:
        files = explorer.list_files(pattern=args.pattern, relative_path=args.path)
        if args.json:
            print(json.dumps(files, indent=2))
        else:
            print(f"Found {len(files)} file(s):\n")
            for f in files:
                print(f"{f['path']:60} {f['size_human']:>10}  {f['modified_human']:>20}")

    elif args.read:
        result = explorer.read_file(args.read, max_lines=args.max_lines)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                return 1
            print(f"File: {result['path']}")
            print(f"Size: {result['size_human']}")
            print(f"Modified: {result['modified']}")
            print(f"Lines: {result.get('lines', 'N/A')}")
            if result.get('truncated'):
                print(f"(Showing first {args.max_lines} lines)")
            print("\nContent:\n" + "=" * 80)
            print(result.get('content', ''))

    elif args.search:
        matches = explorer.search_content(args.search, file_pattern=args.pattern)
        if args.json:
            print(json.dumps(matches, indent=2))
        else:
            print(f"Found {len(matches)} match(es) for '{args.search}':\n")
            for m in matches[:50]:  # Limit to 50 matches in human output
                print(f"{m['path']}:{m['line']}")
                print(f"  {m['content']}")
                print()
            if len(matches) > 50:
                print(f"\n(Showing first 50 of {len(matches)} matches)")

    elif args.stats:
        stats = explorer.get_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("Codebase Statistics")
            print("=" * 80)
            print(f"Total files: {stats['total_files']}")
            print(f"Total size: {stats['total_size_human']}")
            print("\nBy extension:")
            for ext, data in sorted(stats['by_extension'].items(), key=lambda x: x[1]['size'], reverse=True):
                print(f"  {ext:20} {data['count']:>6} files  {data['size_human']:>10}")
            print("\nLargest files:")
            for f in stats['largest_files']:
                print(f"  {f['path']:60} {f['size_human']:>10}")
            print("\nRecently modified:")
            for f in stats['recently_modified']:
                print(f"  {f['path']:60} {f['modified_human']:>20}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
