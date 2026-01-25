#!/usr/bin/env python3
"""
Do_AF.py - Automated ticket batch processing subsystem.

This script processes Actifix tickets in batches using the integrated AI client:
- Claude Code (local CLI) - default
- Claude API (Anthropic API key)
- OpenAI CLI - fallback
- OpenAI API (OpenAI API key)
- Ollama (local)
- Free alternatives (manual/web)

Usage:
    python Do_AF.py [batch_size]

Arguments:
    batch_size: Number of tickets to process (default: 1)
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from actifix.do_af import get_open_tickets, process_next_ticket
from actifix.state_paths import get_actifix_paths
from actifix.raise_af import enforce_raise_af_only, record_error, TicketPriority
from actifix.ai_client import get_ai_client
from actifix.log_utils import atomic_write


def process_single_ticket() -> Optional[str]:
    """
    Process a single ticket using the integrated AI client.

    The AI client automatically handles fallback between multiple providers:
    1. Claude Code (local CLI)
    2. OpenAI CLI session
    3. Claude API (if ANTHROPIC_API_KEY set)
    4. OpenAI API (if OPENAI_API_KEY set)
    5. Ollama (local)
    6. Free alternatives (manual/web)

    Returns:
        Ticket ID if processed successfully, None otherwise.
    """
    # Process using built-in AI system via do_af
    ticket = process_next_ticket(use_ai=True)

    if ticket:
        print(f"✓ Processed ticket {ticket.ticket_id}")
        return ticket.ticket_id
    else:
        print("✗ No tickets processed")
        return None


def git_commit_and_push(ticket_id: str, message: str):
    """Commit and push changes after completing a ticket."""
    try:
        # Stage all changes
        subprocess.run(["git", "add", "."], check=True, cwd=Path.cwd())

        # Commit with message
        commit_msg = f"fix(ticket): {message}\n\nCompleted ticket {ticket_id}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            cwd=Path.cwd()
        )

        bumped_version = ensure_remote_version_guard()
        if bumped_version:
            commit_msg = f"chore(release): bump version to {bumped_version}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                check=True,
                cwd=Path.cwd()
            )

        # Push to remote
        subprocess.run(["git", "push"], check=True, cwd=Path.cwd())

        print(f"✓ Committed and pushed changes for {ticket_id}")
        return True

    except Exception as e:
        print(f"✗ Git operation failed: {e}")
        record_error(
            message=f"Git operation failed: {e}",
            source="scripts/Do_AF.py:git_commit_and_push",
            error_type=type(e).__name__,
            priority=TicketPriority.P2,
        )
        return False


def increment_version():
    """Increment version in pyproject.toml as per AGENTS.md rules."""
    try:
        pyproject_path = Path.cwd() / "pyproject.toml"
        content = pyproject_path.read_text()

        # Simple version increment (patch version)
        match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
        if match:
            major, minor, patch = match.groups()
            new_patch = int(patch) + 1
            new_version = f"{major}.{minor}.{new_patch}"
            new_content = re.sub(
                r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"',
                f'version = "{new_version}"',
                content
            )
            atomic_write(pyproject_path, new_content)
            print(f"✓ Version incremented to {new_version}")
            return True

        return False

    except Exception as e:
        print(f"✗ Failed to increment version: {e}")
        record_error(
            message=f"Version increment failed: {e}",
            source="scripts/Do_AF.py:increment_version",
            error_type=type(e).__name__,
            priority=TicketPriority.P2,
        )
        return False


def _read_version_from_pyproject(pyproject_path: Path) -> Optional[str]:
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    return match.group(0).split('"')[1] if match else None


def _parse_version_tuple(version: str) -> Optional[tuple[int, int, int]]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _read_remote_version() -> Optional[str]:
    fetch = subprocess.run(
        ["git", "fetch", "origin", "develop"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    if fetch.returncode != 0:
        record_error(
            message=f"Git fetch failed: {fetch.stderr.strip()}",
            source="scripts/Do_AF.py:_read_remote_version",
            error_type="GitFetchError",
            priority=TicketPriority.P2,
        )
        return None
    result = subprocess.run(
        ["git", "show", "origin/develop:pyproject.toml"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        record_error(
            message=f"Failed to read remote pyproject.toml: {result.stderr.strip()}",
            source="scripts/Do_AF.py:_read_remote_version",
            error_type="GitShowError",
            priority=TicketPriority.P2,
        )
        return None
    match = re.search(r'version\s*=\s*"([^"]+)"', result.stdout)
    return match.group(1) if match else None


def ensure_remote_version_guard() -> Optional[str]:
    """Ensure local version is greater than or equal to origin/develop."""
    pyproject_path = Path.cwd() / "pyproject.toml"
    local_version = _read_version_from_pyproject(pyproject_path)
    remote_version = _read_remote_version()
    if not local_version or not remote_version:
        record_error(
            message="Unable to verify remote version; aborting push.",
            source="scripts/Do_AF.py:ensure_remote_version_guard",
            error_type="VersionSyncError",
            priority=TicketPriority.P2,
        )
        raise RuntimeError("Unable to verify remote version")

    local_tuple = _parse_version_tuple(local_version)
    remote_tuple = _parse_version_tuple(remote_version)
    if not local_tuple or not remote_tuple:
        record_error(
            message="Version parsing failed; aborting push.",
            source="scripts/Do_AF.py:ensure_remote_version_guard",
            error_type="VersionParseError",
            priority=TicketPriority.P2,
        )
        raise RuntimeError("Version parsing failed")

    if local_tuple >= remote_tuple:
        return None

    new_version = (remote_tuple[0], remote_tuple[1], remote_tuple[2] + 1)
    new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    content = pyproject_path.read_text(encoding="utf-8")
    updated = re.sub(
        r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"',
        f'version = "{new_version_str}"',
        content,
        count=1,
    )
    atomic_write(pyproject_path, updated)
    subprocess.run(
        [sys.executable, str(Path.cwd() / "scripts" / "build_frontend.py")],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["git", "add", "pyproject.toml", "actifix-frontend/index.html", "actifix-frontend/app.js"],
        check=True,
        cwd=Path.cwd(),
    )
    print(f"✓ Version refreshed and bumped to {new_version_str}")
    return new_version_str


def process_batch(batch_size: int):
    """
    Process a batch of tickets using the integrated AI client.

    Args:
        batch_size: Number of tickets to process
    """
    print(f"\n{'='*60}")
    print(f"Do_AF Batch Processing")
    print(f"Batch size: {batch_size}")
    print(f"AI Client: Automatic fallback (Claude > OpenAI > Ollama > Free)")
    print(f"{'='*60}\n")

    # Show available providers
    ai_client = get_ai_client()
    print("Checking AI backends...")
    if ai_client._is_claude_local_available():
        print("  ✓ Claude Code CLI available")
    if ai_client._has_claude_api_key():
        print("  ✓ Claude API key configured")
    if ai_client._has_openai_api_key():
        print("  ✓ OpenAI API key configured")
    if ai_client._is_ollama_available():
        print("  ✓ Ollama available locally")
    print()

    processed_count = 0

    for i in range(batch_size):
        print(f"\n--- Ticket {i+1}/{batch_size} ---")

        ticket_id = process_single_ticket()

        if ticket_id:
            processed_count += 1

            # Increment version
            increment_version()

            # Commit and push after each ticket
            tickets = get_open_tickets()
            remaining = len(tickets)
            git_commit_and_push(
                ticket_id,
                f"Processed via Do_AF ({processed_count}/{batch_size}, {remaining} remaining)"
            )
        else:
            print("No more tickets to process or processing failed")
            break

    print(f"\n{'='*60}")
    print(f"Batch complete: {processed_count}/{batch_size} tickets processed")
    print(f"{'='*60}\n")


def main():
    """Main entry point for Do_AF.py."""
    parser = argparse.ArgumentParser(
        description="Do_AF - Automated batch ticket processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Do_AF.py          # Process 1 ticket (default)
  python Do_AF.py 5        # Process 5 tickets
  python Do_AF.py --help   # Show this help
        """
    )
    parser.add_argument(
        "batch_size",
        type=int,
        nargs="?",
        default=1,
        help="Number of tickets to process (default: 1)"
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        print("Error: batch_size must be at least 1")
        return 1

    # Ensure ACTIFIX_CHANGE_ORIGIN is set
    paths = get_actifix_paths()
    try:
        enforce_raise_af_only(paths)
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please set ACTIFIX_CHANGE_ORIGIN=raise_af before running Do_AF.py")
        return 1

    # Process batch using integrated AI client
    try:
        process_batch(args.batch_size)
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
