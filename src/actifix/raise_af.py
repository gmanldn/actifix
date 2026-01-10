#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RaiseAF - Generic error capture system with context and AI integration.

This is a generic version of the sophisticated error tracking system,
designed to capture errors with comprehensive context for AI-assisted resolution.

Key Features:
- Error capture with detailed context (stack traces, file snippets, system state)
- Auto-priority classification (P0-P4) based on error characteristics  
- Duplicate prevention using normalized "duplicate guards"
- Secret/PII redaction for security
- AI remediation notes generation
- Fallback queue for reliability
- 200k context window management for AI integration
- Configurable for any project/framework

Version: 2.0.0 (Generic)
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from .state_paths import get_actifix_state_dir, get_actifix_paths, ActifixPaths


class TicketPriority(str, Enum):
    """Priority levels for ACTIFIX tickets."""
    P0 = "P0"  # Critical - system down, data loss
    P1 = "P1"  # High - core functionality broken
    P2 = "P2"  # Medium - important but workaround exists
    P3 = "P3"  # Low - minor issues, cosmetic
    P4 = "P4"  # Trivial - nice to have


@dataclass
class ActifixEntry:
    """Enhanced ACTIFIX entry with detailed context."""
    message: str
    source: str
    run_label: str
    entry_id: str
    created_at: datetime
    # Enhanced fields
    priority: TicketPriority = TicketPriority.P2
    error_type: str = "unknown"
    stack_trace: str = ""
    file_context: Dict[str, str] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    ai_remediation_notes: str = ""
    duplicate_guard: str = ""
    # Format version for future migrations
    format_version: str = "1.0"
    # Correlation ID for tracing
    correlation_id: Optional[str] = None

    @property
    def ticket_id(self) -> str:
        """Alias for compatibility with older ticket structures."""
        return self.entry_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat()
        }


# Get project root and actifix directories
PROJECT_ROOT = Path.cwd()
ACTIFIX_DIR = PROJECT_ROOT / "actifix"

# Maximum context size for AI integration (200k tokens ~= 800k chars)
MAX_CONTEXT_CHARS = 800_000
FILE_CONTEXT_MAX_CHARS = int(os.getenv("ACTIFIX_FILE_CONTEXT_MAX_CHARS", "2000"))
SYSTEM_STATE_MAX_CHARS = int(os.getenv("ACTIFIX_SYSTEM_STATE_MAX_CHARS", "1500"))

# Environment variable to enable/disable capture
ACTIFIX_CAPTURE_ENV_VAR = "ACTIFIX_CAPTURE_ENABLED"

# Fallback queue for when ACTIFIX-LIST.md is unwritable
FALLBACK_QUEUE_FILE = get_actifix_state_dir() / "actifix_fallback_queue.json"

# Module-level counter for capture disabled logging (avoid log spam)
_capture_disabled_log_count = 0
_capture_disabled_log_max = 5


def _log_capture_disabled(source: str, error_type: str) -> None:
    """Log when Actifix capture is disabled."""
    global _capture_disabled_log_count

    if _capture_disabled_log_count >= _capture_disabled_log_max:
        return

    _capture_disabled_log_count += 1

    try:
        import logging
        logger = logging.getLogger("actifix.raise_af")
        logger.debug(
            f"Actifix capture disabled (set {ACTIFIX_CAPTURE_ENV_VAR}=1 to enable). "
            f"Skipped: {error_type} from {source}"
        )
    except Exception:
        pass


def _get_current_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    try:
        # Try to get from threading context
        import threading
        thread_local = getattr(threading, 'actifix_correlation_id', None)
        if thread_local:
            return thread_local

        # Try to get from exception if one is being handled
        import sys
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            correlation_id = getattr(exc_info[1], 'correlation_id', None)
            if correlation_id:
                return correlation_id

        return None
    except Exception:
        return None


def generate_entry_id() -> str:
    """Generate a short unique ID for Actifix tickets."""
    now = datetime.now(timezone.utc)
    return f"ACT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"


def generate_ticket_id() -> str:
    """Backward-compatible ticket ID generator."""
    return generate_entry_id()


def generate_duplicate_guard(source: str, message: str, error_type: str = "unknown") -> str:
    """Generate a unique duplicate guard for deduplication."""
    # Normalize message for deduplication
    normalized = re.sub(r'\d+', 'N', message)
    normalized = re.sub(r'/[^\s]+/', '/PATH/', normalized)
    normalized = normalized.lower().strip()[:200]

    guard_input = f"{error_type}:{source}:{normalized}"
    hash_suffix = hashlib.sha256(guard_input.encode()).hexdigest()[:8]

    return f"ACTIFIX-{source.replace('/', '-').replace('.', '-')[:40]}-{hash_suffix}"


def redact_secrets_from_text(text: str) -> str:
    """
    Redact secrets and PII from text.

    Removes or masks:
    - API keys (various formats)
    - Passwords in URLs or config
    - Bearer tokens
    - AWS credentials
    - Email addresses
    - IP addresses (optional, keep for debugging)
    - Credit card-like numbers
    - Social security-like numbers
    """
    if not text:
        return text

    # Patterns to redact (pattern, replacement)
    patterns = [
        # sk- style API keys
        (r'(sk-[A-Za-z0-9]{16,})', r'***API_KEY_REDACTED***'),

        # API Keys (generic patterns)
        (r'(?i)(api[_-]?key|apikey|api_secret|api_token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?',
         r'\1=***REDACTED***'),
        (r'(?i)(secret[_-]?key|secret_token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?',
         r'\1=***REDACTED***'),

        # Bearer tokens
        (r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]+)', r'\1***REDACTED***'),
        (r'(?i)(authorization[:\s]+)([a-zA-Z0-9_\-\.]+)', r'\1***REDACTED***'),

        # AWS credentials
        (r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\']?([A-Z0-9]{16,})["\']?',
         r'\1=***REDACTED***'),
        (r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{20,})["\']?',
         r'\1=***REDACTED***'),

        # Passwords in URLs
        (r'(://[^:]+:)([^@]+)(@)', r'\1***REDACTED***\3'),

        # Password fields
        (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{4,})["\']?',
         r'\1=***REDACTED***'),

        # Private keys
        (r'-----BEGIN [A-Z]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z]+ PRIVATE KEY-----',
         '***PRIVATE_KEY_REDACTED***'),

        # Email addresses (partial redaction)
        (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
         r'***@\2'),

        # Credit card-like numbers (13-19 digits)
        (r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{1,7})\b', '***CARD_REDACTED***'),

        # SSN-like patterns
        (r'\b(\d{3}[-\s]?\d{2}[-\s]?\d{4})\b', '***SSN_REDACTED***'),

        # Generic tokens (long hex strings)
        (r'(?i)(token|key|secret|credential)["\']*\s*[=:]\s*["\']?([a-f0-9]{32,})["\']?',
         r'\1=***REDACTED***'),

        # OpenAI/Claude API keys
        (r'(sk-[a-zA-Z0-9]{20,})', '***API_KEY_REDACTED***'),
        (r'(claude[_-]?api[_-]?key\s*[=:]\s*)[^\s]+', r'\1***REDACTED***'),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    return result


def capture_stack_trace() -> str:
    """Capture current stack trace with context, redacting secrets."""
    trace = traceback.format_exc()
    return redact_secrets_from_text(trace)


def capture_file_context(source: str, max_lines: int = 50) -> Dict[str, str]:
    """
    Capture file context around error location.
    Returns dict mapping file paths to relevant snippets.
    """
    context = {}

    # Try to find the source file
    source_path = None
    if ":" in source:
        file_part = source.split(":")[0]
        # Try various path resolutions
        for candidate in [
            PROJECT_ROOT / "src" / file_part,
            PROJECT_ROOT / file_part,
            Path(file_part)
        ]:
            if candidate.exists():
                source_path = candidate
                break

    if source_path and source_path.exists():
        try:
            content = source_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Try to extract line number
            line_num = 0
            if ":" in source:
                try:
                    line_num = int(source.split(":")[1])
                except (ValueError, IndexError):
                    pass

            if line_num > 0:
                # Get context around the error line
                start = max(0, line_num - 10)
                end = min(len(lines), line_num + 10)
                snippet_lines = lines[start:end]
                context[str(source_path)] = "\n".join(
                    f"{i+start+1}: {line}" for i, line in enumerate(snippet_lines)
                )
            else:
                # Just get first N lines
                context[str(source_path)] = "\n".join(lines[:max_lines])
        except Exception:
            pass

    return context


def capture_system_state() -> Dict[str, Any]:
    """Capture system state for debugging context."""
    env_vars = {
        k: redact_secrets_from_text(str(v))
        for k, v in os.environ.items()
        if k.startswith(("ACTIFIX", "PYTHONPATH"))
    }

    state = {
        "cwd": str(Path.cwd()),
        "python_version": sys.version,
        "platform": sys.platform,
        "env_vars": env_vars,
    }

    # Try to get git info
    try:
        git_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        ).stdout.strip()
        git_commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        ).stdout.strip()
        state["git_branch"] = git_branch
        state["git_commit"] = git_commit
    except Exception:
        pass

    return state


def classify_priority(error_type: str, message: str, source: str) -> TicketPriority:
    """Automatically classify ticket priority based on error characteristics."""
    error_lower = error_type.lower()
    msg_lower = message.lower()

    # P0: Critical
    if any(x in error_lower for x in ["fatal", "crash", "corrupt", "dataloss"]):
        return TicketPriority.P0
    if any(x in msg_lower for x in ["data loss", "corrupt", "crash"]):
        return TicketPriority.P0

    # P1: High
    if any(x in error_lower for x in ["database", "security", "auth"]):
        return TicketPriority.P1
    if "core" in source.lower() or "main" in source.lower():
        return TicketPriority.P1

    # P3: Low
    if any(x in error_lower for x in ["warning", "deprecat"]):
        return TicketPriority.P3

    # P4: Trivial
    if any(x in error_lower for x in ["style", "lint", "format"]):
        return TicketPriority.P4

    # Default: P2
    return TicketPriority.P2


def generate_ai_remediation_notes(entry: 'ActifixEntry') -> str:
    """Generate detailed AI remediation notes for AI processing."""
    notes_parts = [
        f"Error Type: {entry.error_type}",
        f"Error Message: {entry.message}",
        f"Source Location: {entry.source}",
        f"Priority: {entry.priority.value}",
        "",
        "REMEDIATION REQUIREMENTS:",
        "1. Read and follow ALL project documentation",
        "2. Identify root cause from stack trace and file context",
        "3. Implement fix following existing code patterns",
        "4. Write comprehensive tests (95%+ coverage required)",
        "5. Update documentation if behavior changes",
        "6. Run full test suite to ensure no regressions",
        "7. Commit with conventional message format",
        "8. Ensure code quality standards are met",
        "",
        "STACK TRACE:",
        entry.stack_trace or "(No stack trace captured)",
        "",
    ]

    # Add file context if available
    if entry.file_context:
        notes_parts.append("FILE CONTEXT:")
        for path, snippet in entry.file_context.items():
            notes_parts.append(f"\n--- {path} ---")
            notes_parts.append(snippet[:FILE_CONTEXT_MAX_CHARS])

    # Add system state
    notes_parts.append("\nSYSTEM STATE:")
    notes_parts.append(json.dumps(entry.system_state, indent=2, default=str)[:SYSTEM_STATE_MAX_CHARS])

    full_notes = "\n".join(notes_parts)

    # Ensure we don't exceed max context
    if len(full_notes) > MAX_CONTEXT_CHARS:
        full_notes = full_notes[:MAX_CONTEXT_CHARS] + "\n... (truncated for context window)"

    return full_notes


def check_duplicate_guard(duplicate_guard: str, base_dir: Path) -> bool:
    """
    Check if a ticket with the same duplicate guard already exists.
    Returns True if duplicate exists, False otherwise.
    """
    actifix_list = base_dir / "ACTIFIX-LIST.md"
    if not actifix_list.exists():
        return False

    content = actifix_list.read_text(encoding="utf-8")
    return duplicate_guard in content


def get_completed_guards(base_dir: Path) -> set:
    """Get all duplicate guards from the Completed Items section."""
    actifix_list = base_dir / "ACTIFIX-LIST.md"
    if not actifix_list.exists():
        return set()

    content = actifix_list.read_text(encoding="utf-8")

    # Find completed section
    completed_start = content.find("## Completed Items")
    if completed_start == -1:
        return set()

    completed_section = content[completed_start:]

    # Extract all duplicate guards from completed section
    guards = set()
    for line in completed_section.splitlines():
        if "Duplicate Guard" in line and "`" in line:
            # Extract guard from: - **Duplicate Guard**: `ACTIFIX-xxx`
            match = re.search(r'`(ACTIFIX-[^`]+)`', line)
            if match:
                guards.add(match.group(1))

    return guards


def ensure_scaffold(base_dir: Path) -> None:
    """Create Actifix directory and baseline files if missing."""
    base_dir.mkdir(parents=True, exist_ok=True)

    actifix_md = base_dir / "ACTIFIX.md"
    if not actifix_md.exists():
        actifix_md.write_text(
            "# Actifix Error Rollup\n"
            "Tracks the last 20 errors from recent runs. This file is regenerated by RaiseAF.py.\n\n"
            "## Recent Errors (last 20)\n"
            "_No entries yet. Use RaiseAF.py to record errors._\n",
            encoding="utf-8",
        )

    actifix_list = base_dir / "ACTIFIX-LIST.md"
    if not actifix_list.exists():
        actifix_list.write_text(
            "# Actifix Ticket List\n"
            "Tickets generated from recent errors. Update checkboxes as work progresses.\n\n"
            "## Active Items\n"
            "_None_\n\n"
            "## Completed Items\n"
            "_None_\n",
            encoding="utf-8",
        )

    actifix_log = base_dir / "ACTIFIX-LOG.md"
    if not actifix_log.exists():
        actifix_log.write_text(
            "# Actifix Fix Log\n"
            "Chronological log of Actifix ticket completions.\n\n"
            "## Entries\n"
            "_None_\n",
            encoding="utf-8",
        )

    aflog = base_dir / "AFLog.txt"
    if not aflog.exists():
        aflog.write_text(
            "Actifix Detailed Lifecycle Log\n"
            "Entries are appended by DoAF.py after each ticket is processed.\n\n",
            encoding="utf-8",
        )


def _read_recent_entries(path: Path) -> List[str]:
    if not path.exists():
        return []

    entries: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- "):
            entries.append(line.strip())
    return entries


def _write_recent_entries(path: Path, lines: List[str]) -> None:
    header = (
        "# Actifix Error Rollup\n"
        "Tracks the last 20 errors from recent runs. This file is regenerated by RaiseAF.py.\n\n"
        "## Recent Errors (last 20)\n"
    )
    body = "\n".join(lines) if lines else "_No entries yet. Use RaiseAF.py to record errors._"
    content = f"{header}{body}\n"
    path.write_text(content, encoding="utf-8")


def _append_recent(entry: ActifixEntry, base_dir: Path) -> None:
    actifix_md = base_dir / "ACTIFIX.md"
    recent = _read_recent_entries(actifix_md)
    line = (
        f"- {entry.created_at.isoformat()} | run={entry.run_label} | "
        f"source={entry.source} | type={entry.error_type} | id={entry.entry_id} | {entry.message}"
    )
    recent.append(line)
    trimmed = recent[-20:]  # Keep only last 20
    _write_recent_entries(actifix_md, trimmed)


def _queue_to_fallback(entry: ActifixEntry, base_dir: Path) -> bool:
    """Queue entry to fallback file when ACTIFIX-LIST.md is unwritable."""
    queue_file = base_dir / ".actifix_fallback_queue.json"
    try:
        # Read existing queue
        queue = []
        if queue_file.exists():
            try:
                queue = json.loads(queue_file.read_text(encoding="utf-8"))
            except Exception:
                queue = []

        # Add entry to queue
        queue.append(entry.to_dict())

        # Write back
        queue_file.write_text(json.dumps(queue, indent=2, default=str), encoding="utf-8")
        return True
    except Exception:
        return False


def replay_fallback_queue(base_dir: Path = ACTIFIX_DIR) -> int:
    """Replay entries from fallback queue to ACTIFIX-LIST.md."""
    queue_file = base_dir / ".actifix_fallback_queue.json"
    if not queue_file.exists():
        return 0

    try:
        queue = json.loads(queue_file.read_text(encoding="utf-8"))
        if not queue:
            return 0

        replayed = 0
        failed = []

        for entry_dict in queue:
            try:
                # Reconstruct entry
                entry = ActifixEntry(
                    message=entry_dict.get("message", ""),
                    source=entry_dict.get("source", ""),
                    run_label=entry_dict.get("run_label", ""),
                    entry_id=entry_dict.get("entry_id", ""),
                    created_at=datetime.fromisoformat(entry_dict.get("created_at", datetime.now(timezone.utc).isoformat())),
                    priority=TicketPriority(entry_dict.get("priority", "P2")),
                    error_type=entry_dict.get("error_type", "unknown"),
                    stack_trace=entry_dict.get("stack_trace", ""),
                    duplicate_guard=entry_dict.get("duplicate_guard", ""),
                )
                _append_ticket_impl(entry, base_dir)
                replayed += 1
            except Exception:
                failed.append(entry_dict)

        # Update queue with only failed entries
        if failed:
            queue_file.write_text(json.dumps(failed, indent=2, default=str), encoding="utf-8")
        else:
            queue_file.unlink(missing_ok=True)

        return replayed
    except Exception:
        return 0


def _append_ticket_impl(entry: ActifixEntry, base_dir: Path) -> None:
    """Internal implementation of ticket append."""
    path = base_dir / "ACTIFIX-LIST.md"
    content = path.read_text(encoding="utf-8")

    # Build detailed ticket block
    block = [
        f"### {entry.entry_id} - [{entry.priority.value}] {entry.error_type}: {entry.message[:100]}",
        f"- **Priority**: {entry.priority.value}",
        f"- **Error Type**: {entry.error_type}",
        f"- **Source**: `{entry.source}`",
        f"- **Run**: {entry.run_label}",
        f"- **Created**: {entry.created_at.isoformat()}",
        f"- **Duplicate Guard**: `{entry.duplicate_guard}`",
    ]

    # Add correlation ID if present
    if entry.correlation_id:
        block.append(f"- **Correlation ID**: `{entry.correlation_id}`")

    # Add status and tracking fields
    block.extend([
        f"- **Status**: Open",
        f"- **Owner**: None",
        f"- **Branch**: None",
        f"- **Lease Expires**: None",
        "",
        "**Checklist:**",
        "- [ ] Documented",
        "- [ ] Functioning",
        "- [ ] Tested",
        "- [ ] Completed",
        "",
    ])

    # Add stack trace summary if available
    if entry.stack_trace and len(entry.stack_trace) > 10:
        trace_preview = entry.stack_trace[-500:].strip()
        block.extend([
            "<details>",
            "<summary>Stack Trace Preview</summary>",
            "",
            "```",
            trace_preview,
            "```",
            "</details>",
            "",
        ])

    # Add AI notes preview
    if entry.ai_remediation_notes:
        notes_preview = entry.ai_remediation_notes[:300].strip()
        block.extend([
            "<details>",
            "<summary>AI Remediation Notes</summary>",
            "",
            notes_preview,
            "...",
            "</details>",
            "",
        ])

    block_text = "\n".join(block)

    if "## Active Items" not in content:
        content = (
            "# Actifix Ticket List\n"
            "Tickets generated from recent errors. Update checkboxes as work progresses.\n\n"
            "## Active Items\n\n"
            "## Completed Items\n"
            "_None_\n"
        )

    # Remove placeholder if present
    content = content.replace("## Active Items\n_None_", "## Active Items\n")

    insertion_point = content.find("## Completed Items")
    if insertion_point == -1:
        content = f"{content.rstrip()}\n\n{block_text}\n"
    else:
        before = content[:insertion_point].rstrip()
        after = content[insertion_point:]
        content = f"{before}\n\n{block_text}\n{after.lstrip()}"

    path.write_text(content, encoding="utf-8")


def _append_ticket(entry: ActifixEntry, base_dir: Path) -> bool:
    """Append ticket to ACTIFIX-LIST.md with fallback queue support."""
    try:
        _append_ticket_impl(entry, base_dir)
        # Try to replay any queued entries
        replay_fallback_queue(base_dir)
        return True
    except (PermissionError, OSError, IOError):
        # ACTIFIX-LIST.md is unwritable, use fallback queue
        _queue_to_fallback(entry, base_dir)
        return False


def record_error(
    message: str,
    source: str,
    run_label: str = "unspecified",
    base_dir: Optional[Path] = None,
    error_type: str = "unknown",
    priority: Optional[TicketPriority | str] = None,
    stack_trace: Optional[str] = None,
    capture_context: bool = True,
    skip_duplicate_check: bool = False,
    skip_ai_notes: bool = False,
    paths: Optional[ActifixPaths] = None,
) -> Optional[ActifixEntry]:
    """
    Record an error across Actifix files with detailed context.

    Args:
        message: Error message to record
        source: Source file/function for the error
        run_label: Run label or identifier
        base_dir: Actifix directory (defaults to actifix/ folder)
        error_type: Type of error (e.g., ValueError, RuntimeError)
        priority: Optional priority override (auto-classified if None)
        stack_trace: Optional stack trace (captured automatically if None)
        capture_context: Whether to capture file and system context
        skip_duplicate_check: Skip duplicate checking (use for testing only)
        skip_ai_notes: Skip AI notes generation (for performance)
        paths: Optional ActifixPaths override (takes precedence over base_dir)

    Returns:
        ActifixEntry with all captured context, or None if duplicate detected
    """
    # Resolve paths
    active_paths = paths
    if active_paths is None:
        active_paths = get_actifix_paths(base_dir=base_dir) if base_dir else get_actifix_paths()
    base_dir_path = active_paths.base_dir
    
    # Clean inputs
    clean_message = message.strip()
    clean_source = source.strip() or "unknown"
    clean_run_label = run_label.strip() or "unspecified"
    clean_error_type = error_type.strip() or "unknown"

    # Capture is opt-in: only raise tickets when explicitly enabled
    env_flag = os.getenv(ACTIFIX_CAPTURE_ENV_VAR, "").strip().lower()
    capture_enabled = env_flag in {"1", "true", "yes", "on", "debug"}
    
    if paths is not None and env_flag not in {"0", "false", "no", "off"}:
        # Explicit paths imply caller wants capture even if env is unset
        capture_enabled = True
    if not capture_enabled:
        _log_capture_disabled(clean_source, clean_error_type)
        return None

    ensure_scaffold(base_dir_path)

    # Generate duplicate guard early for checking
    duplicate_guard = generate_duplicate_guard(clean_source, clean_message, clean_error_type)

    # LOOP PREVENTION: Check if this error already has a ticket
    if not skip_duplicate_check:
        if check_duplicate_guard(duplicate_guard, base_dir_path):
            # Duplicate detected - don't create another ticket
            return None

        # Also check completed guards to prevent recreating fixed issues
        completed_guards = get_completed_guards(base_dir_path)
        if duplicate_guard in completed_guards:
            # This error was already fixed - don't recreate
            return None

    # Auto-classify priority if not provided
    if isinstance(priority, str):
        try:
            priority = TicketPriority(priority)
        except Exception:
            priority = None
    
    if priority is None:
        priority = classify_priority(clean_error_type, clean_message, clean_source)

    # Capture stack trace if not provided
    if stack_trace is None:
        stack_trace = capture_stack_trace()

    # Capture context
    file_context = {}
    system_state = {}
    if capture_context:
        file_context = capture_file_context(clean_source)
        system_state = capture_system_state()

    # Capture correlation ID from context
    correlation_id = _get_current_correlation_id()

    entry = ActifixEntry(
        message=clean_message,
        source=clean_source,
        run_label=clean_run_label,
        entry_id=generate_entry_id(),
        created_at=datetime.now(timezone.utc),
        priority=priority,
        error_type=clean_error_type,
        stack_trace=stack_trace,
        file_context=file_context,
        system_state=system_state,
        duplicate_guard=duplicate_guard,
        correlation_id=correlation_id,
    )

    # Generate AI remediation notes
    if not skip_ai_notes:
        entry.ai_remediation_notes = generate_ai_remediation_notes(entry)

    _append_ticket(entry, base_dir_path)
    _append_recent(entry, base_dir_path)

    return entry


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record an Actifix error with detailed context (v2.0.0)"
    )
    parser.add_argument("--message", required=True, help="Error message to record")
    parser.add_argument("--source", default="unknown", help="Source file/function for the error")
    parser.add_argument("--run", dest="run_label", default="manual", help="Run label or identifier")
    parser.add_argument("--error-type", default="unknown", help="Type of error (e.g., ValueError)")
    parser.add_argument(
        "--priority",
        choices=["P0", "P1", "P2", "P3", "P4"],
        default=None,
        help="Priority level (auto-classified if not specified)"
    )
    parser.add_argument(
        "--stack-trace",
        default=None,
        help="Stack trace (captured automatically if not provided)"
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Skip file and system context capture"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=ACTIFIX_DIR,
        help="Actifix directory (defaults to actifix/ folder)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    print("[Actifix v2.0.0] Recording error with detailed context...")

    # Parse priority if provided
    priority = None
    if args.priority:
        priority = TicketPriority[args.priority]

    entry = record_error(
        message=args.message,
        source=args.source,
        run_label=args.run_label,
        base_dir=args.base_dir,
        error_type=args.error_type,
        priority=priority,
        stack_trace=args.stack_trace,
        capture_context=not args.no_context
    )

    if entry:
        print(f"[Actifix] Recorded as {entry.entry_id}")
        print(f"[Actifix] Priority: {entry.priority.value}")
        print(f"[Actifix] Created: {entry.created_at.isoformat()}")
        print(f"[Actifix] Duplicate Guard: {entry.duplicate_guard}")
    else:
        print("[Actifix] Not recorded (capture disabled or duplicate detected)")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
