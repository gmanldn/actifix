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

Version: 2.5.2 (Generic)
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .state_paths import (
    get_actifix_state_dir,
    get_actifix_paths,
    get_raise_af_sentinel,
    init_actifix_files,
    ActifixPaths,
)
from .log_utils import log_event
from .config import get_config


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

# AI remediation notes sizing and context gating
AI_REMEDIATION_MAX_CHARS = int(os.getenv("ACTIFIX_AI_REMEDIATION_MAX_CHARS", "2000"))
AI_REMEDIATION_DRY_RUN_ENV = "ACTIFIX_AI_REMEDIATION_DRY_RUN"
CONTEXT_TRUNCATION_CHARS = int(os.getenv("ACTIFIX_CONTEXT_TRUNCATION_CHARS", "4096"))
SYSTEM_STATE_ENV_CACHE_TTL_SECONDS = int(os.getenv("ACTIFIX_SYSTEM_STATE_CACHE_TTL", "30"))
MINIMAL_CONTEXT_PRIORITIES = {
    token.strip().upper()
    for token in os.getenv("ACTIFIX_CONTEXT_MINIMAL_PRIORITIES", "P1").split(",")
    if token.strip()
}
STRUCTURED_MESSAGE_ENV = "ACTIFIX_ENFORCE_STRUCTURED_MESSAGES"
STRUCTURED_MESSAGE_ENFORCED = os.getenv(STRUCTURED_MESSAGE_ENV, "0").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

# Environment variable to enable/disable capture
ACTIFIX_CAPTURE_ENV_VAR = "ACTIFIX_CAPTURE_ENABLED"
ACTIFIX_CHANGE_ORIGIN_ENV = "ACTIFIX_CHANGE_ORIGIN"
ACTIFIX_ENFORCE_RAISE_AF_ENV = "ACTIFIX_ENFORCE_RAISE_AF"
DUPLICATE_REOPEN_WINDOW = timedelta(hours=24)

# Fallback queue for when database writes are unavailable
FALLBACK_QUEUE_FILE = get_actifix_state_dir() / "actifix_fallback_queue.json"
LEGACY_FALLBACK_QUEUE = ".actifix_fallback_queue.json"

# Caches for repeated operations
_PATH_CACHE: Dict[str, ActifixPaths] = {}
_PATH_CACHE_STATS: Dict[str, int] = {"hits": 0, "misses": 0}
_SYSTEM_STATE_ENV_CACHE: Dict[str, Any] = {
    "signature": None,
    "payload": {},
    "timestamp": 0.0,
}

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


def _path_cache_key(base_dir: Optional[Path]) -> str:
    """Produce a cache key for Actifix paths based on the base directory."""
    if base_dir:
        try:
            return str(Path(base_dir).resolve())
        except Exception:
            return str(base_dir)
    return "default"


def _get_cached_actifix_paths(base_dir: Optional[Path] = None) -> ActifixPaths:
    """Cache Actifix path lookups to reduce repeated resolution cost."""
    key = _path_cache_key(base_dir)
    cached = _PATH_CACHE.get(key)
    if cached:
        _PATH_CACHE_STATS["hits"] += 1
        return cached

    _PATH_CACHE_STATS["misses"] += 1
    project_root = Path(base_dir).resolve().parent if base_dir else None
    paths = get_actifix_paths(project_root=project_root, base_dir=base_dir)
    _PATH_CACHE[key] = paths
    return paths


def _snapshot_path_cache_stats() -> Dict[str, int]:
    """Return a snapshot of the path cache metrics."""
    return {
        "hits": _PATH_CACHE_STATS["hits"],
        "misses": _PATH_CACHE_STATS["misses"],
        "cache_size": len(_PATH_CACHE),
    }


def _get_cached_env_vars() -> Dict[str, str]:
    """Cache sanitized environment snapshots used in system state."""
    now = time.time()
    env_vars = {
        k: redact_secrets_from_text(str(v))
        for k, v in os.environ.items()
        if k.startswith(("ACTIFIX", "PYTHONPATH"))
    }
    signature = tuple(sorted(env_vars.items()))

    cache_entry = _SYSTEM_STATE_ENV_CACHE
    if (
        cache_entry["signature"] == signature
        and now - cache_entry["timestamp"] < SYSTEM_STATE_ENV_CACHE_TTL_SECONDS
    ):
        return dict(cache_entry["payload"])

    cache_entry["signature"] = signature
    cache_entry["payload"] = dict(env_vars)
    cache_entry["timestamp"] = now
    return dict(env_vars)


def _truncate_context_text(text: str, max_chars: int) -> str:
    """Truncate context text while keeping head/tail lines for readability."""
    if not text or len(text) <= max_chars:
        return text

    # Reserve space for truncation marker
    marker = "\n... (truncated) ...\n"
    marker_len = len(marker)
    available = max_chars - marker_len

    # Split available space between head and tail
    head_size = available // 2
    tail_size = available - head_size  # Use remaining space for tail

    head = text[:head_size]
    tail = text[-tail_size:]
    head_border = head.rfind("\n")
    tail_border = tail.find("\n")

    head = head[: head_border] if head_border > 0 else head
    tail = tail[tail_border + 1 :] if tail_border >= 0 else tail

    return f"{head}{marker}{tail}"


def _ensure_structured_message(message: str) -> str:
    """Ensure the ticket message includes structured sections when enforced."""
    if not message:
        return message

    lower = message.lower()
    if all(section.lower() in lower for section in ("Root Cause", "Impact", "Action")):
        return message

    return (
        f"Root Cause: {message.strip()}\n"
        "Impact: Requires focused token and robustness work.\n"
        "Action: Implement the described improvements and document the results."
    )


def _compact_value(value: Any) -> Optional[Any]:
    """Recursively compact values for the fallback queue payload."""
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    if isinstance(value, dict):
        compacted = {}
        for key, val in value.items():
            condensed = _compact_value(val)
            if condensed is not None:
                compacted[key] = condensed
        return compacted if compacted else None
    if isinstance(value, list):
        compacted = [_compact_value(item) for item in value]
        compacted = [item for item in compacted if item is not None]
        return compacted if compacted else None
    return value


def _compact_queue_entry(entry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Strip empty fields and trim whitespace before persisting to the fallback queue."""
    compacted = {}
    for key, value in entry_dict.items():
        refined = _compact_value(value)
        if refined is not None:
            compacted[key] = refined
    return compacted


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


def enforce_raise_af_only(
    paths: Optional[ActifixPaths] = None,
    change_origin: Optional[str] = None,
) -> None:
    """
    Enforce Raise_AF-only change policy.

    Requires ACTIFIX_CHANGE_ORIGIN=raise_af (unless enforcement explicitly
    disabled via ACTIFIX_ENFORCE_RAISE_AF=0). Sentinel file in state dir
    enables enforcement by default for this repo.
    """
    active_paths = paths or _get_cached_actifix_paths()
    sentinel = get_raise_af_sentinel(active_paths)

    enforce_flag = os.getenv(ACTIFIX_ENFORCE_RAISE_AF_ENV, "1").strip().lower()
    enforcement_enabled = enforce_flag not in {"0", "false", "no", "off"} or sentinel.exists()

    if not enforcement_enabled:
        return

    origin = (change_origin or os.getenv(ACTIFIX_CHANGE_ORIGIN_ENV, "")).strip().lower()
    if origin != "raise_af":
        raise PermissionError(
            "Raise_AF policy enforced: set ACTIFIX_CHANGE_ORIGIN=raise_af and begin changes via actifix.raise_af.record_error()."
        )


def generate_entry_id() -> str:
    """Generate a short unique ID for Actifix tickets."""
    now = datetime.now(timezone.utc)
    return f"ACT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"


def generate_ticket_id() -> str:
    """Backward-compatible ticket ID generator."""
    return generate_entry_id()


def _normalize_for_guard(text: str) -> str:
    """Normalize free text for guard generation and comparisons."""
    if not text:
        return ""

    normalized = re.sub(r'/[^\s]+/', '/PATH/', text)
    normalized = re.sub(r'\d+', '0', normalized)
    return normalized.lower().strip()[:200]


def _stack_signature_for_guard(stack_trace: Optional[str]) -> str:
    """
    Produce a lightweight signature from the first meaningful stack line.
    Focus on the error content rather than call-site noise.
    """
    if not stack_trace:
        return ""

    for line in stack_trace.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.lower().startswith("traceback"):
            continue
        return _normalize_for_guard(cleaned)
    return ""


def generate_duplicate_guard(
    source: str,
    message: str,
    error_type: str = "unknown",
    stack_trace: Optional[str] = None,
) -> str:
    """Generate a message-focused duplicate guard for deduplication."""
    normalized_message = _normalize_for_guard(message)
    normalized_error = _normalize_for_guard(error_type or "unknown")
    stack_signature = _stack_signature_for_guard(stack_trace)

    guard_input = f"{normalized_error}:{normalized_message}:{stack_signature}"
    hash_suffix = hashlib.sha256(guard_input.encode()).hexdigest()[:8]
    message_slug = (normalized_message.replace(" ", "-") or "message")[:40]

    return f"ACTIFIX-{message_slug}-{hash_suffix}"


def redact_secrets_from_text(text: str) -> str:
    """
    Redact secrets and PII from text.

    Removes or masks:
    - API keys (various formats)
    - Passwords in URLs or config
    - Authorization tokens
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

        # Authorization tokens (e.g., Bearer)
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
    return _truncate_context_text(redact_secrets_from_text(trace), CONTEXT_TRUNCATION_CHARS)


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
                snippet_text = "\n".join(
                    f"{i+start+1}: {line}" for i, line in enumerate(snippet_lines)
                )
                context[str(source_path)] = _truncate_context_text(
                    snippet_text,
                    CONTEXT_TRUNCATION_CHARS,
                )
            else:
                # Just get first N lines
                context[str(source_path)] = "\n".join(lines[:max_lines])
        except Exception:
            pass

    return context


def capture_system_state() -> Dict[str, Any]:
    """Capture system state for debugging context."""
    state = {
        "cwd": str(Path.cwd()),
        "python_version": sys.version,
        "platform": sys.platform,
        "env_vars": _get_cached_env_vars(),
        "path_cache": _snapshot_path_cache_stats(),
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


def preview_ai_remediation_notes(
    entry: 'ActifixEntry',
    max_chars: Optional[int] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Preview the structured AI remediation notes and token metrics."""
    limit = max_chars or AI_REMEDIATION_MAX_CHARS
    stack_snippet = _truncate_context_text(
        entry.stack_trace or "(No stack trace captured)",
        CONTEXT_TRUNCATION_CHARS,
    )

    notes_parts = [
        f"Root Cause: {entry.error_type} @ {entry.source}",
        f"Impact: ticket {entry.entry_id} ({entry.priority.value}) requires a code-level fix",
        f"Action: Implement the documented robustness improvements and re-run {Path(__file__).stem} tests",
        "",
        "STACK TRACE:",
        stack_snippet,
    ]

    if entry.file_context:
        notes_parts.append("")
        notes_parts.append("FILE CONTEXT SNAPSHOTS:")
        for path, snippet in list(entry.file_context.items())[:3]:
            lines = [line for line in snippet.splitlines() if line.strip()]
            if not lines:
                continue
            first = lines[0][:200]
            last = lines[-1][:200]
            notes_parts.append(f"- {Path(path).name}: {first} ... {last}")

    state_keys = sorted(entry.system_state.keys())
    if state_keys:
        notes_parts.append("")
        notes_parts.append("SYSTEM STATE KEYS:")
        notes_parts.append(", ".join(state_keys))

    full_notes = "\n".join(notes_parts)
    truncated = _truncate_context_text(full_notes, limit)
    truncated = truncated.strip()

    stats = {
        "ai_notes_char_count": len(truncated),
        "ai_notes_char_limit": limit,
        "ai_notes_truncated": len(full_notes) > len(truncated),
        "ai_notes_overflow": max(0, len(full_notes) - len(truncated)),
        "stack_snippet_chars": len(stack_snippet),
    }

    return truncated, stats


def generate_ai_remediation_notes(entry: 'ActifixEntry', max_chars: Optional[int] = None) -> str:
    """Generate detailed AI remediation notes for AI processing."""
    notes, stats = preview_ai_remediation_notes(entry, max_chars=max_chars)
    metrics = entry.system_state.setdefault("ai_remediation_metrics", {})
    metrics.update(stats)

    if os.getenv(AI_REMEDIATION_DRY_RUN_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        entry.system_state["ai_remediation_preview"] = notes
        return notes

    return notes




def ensure_scaffold(base_dir: Path) -> None:
    """Create Actifix directory and artifacts if missing."""
    base_dir.mkdir(parents=True, exist_ok=True)
    paths = _get_cached_actifix_paths(base_dir=base_dir)
    init_actifix_files(paths)




def _get_fallback_queue_file(base_dir: Path) -> Path:
    """
    Resolve the canonical fallback queue file in the state directory.

    Uses ActifixPaths to honor ACTIFIX_STATE_DIR overrides and ensures the
    directory exists. A legacy queue file in the base directory is still
    read for backward compatibility and then migrated.
    """
    paths = _get_cached_actifix_paths(base_dir=base_dir)
    queue_file = paths.fallback_queue_file
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    return queue_file


def _load_existing_queue(primary: Path, legacy: Path) -> tuple[list, Path]:
    """Load queue contents from primary or legacy locations."""
    for candidate in (primary, legacy):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8")), candidate
            except Exception:
                return [], primary
    return [], primary


def _persist_queue(queue: list, target: Path, legacy: Path) -> None:
    """Write queue to primary location and clean up legacy path if needed."""
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first for atomicity - only delete legacy after successful write
    temp_path = target.parent / f"{target.name}.tmp"
    try:
        # Write to temporary file
        temp_path.write_text(json.dumps(queue, indent=2, default=str), encoding="utf-8")

        # Move temp file to target (atomic operation on most filesystems)
        temp_path.replace(target)

        # Only unlink legacy file after successful write to target
        if legacy.exists() and legacy != target:
            try:
                legacy.unlink()
            except Exception:
                pass
    except Exception:
        # Clean up temp file if it exists and write failed
        try:
            temp_path.unlink()
        except Exception:
            pass
        raise


def _queue_to_fallback(entry: ActifixEntry, base_dir: Path) -> bool:
    """Queue entry to fallback file when database writes fail."""
    queue_file = _get_fallback_queue_file(base_dir)
    legacy_file = base_dir / LEGACY_FALLBACK_QUEUE
    try:
        queue, source_path = _load_existing_queue(queue_file, legacy_file)

        # Add entry to queue
        queue.append(_compact_queue_entry(entry.to_dict()))

        # Write back
        _persist_queue(queue, queue_file, legacy_file)
        return True
    except Exception:
        return False


def _entry_from_dict(entry_dict: Dict[str, Any]) -> ActifixEntry:
    """Rebuild an ActifixEntry from serialized fallback data."""
    created_at = entry_dict.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            created_at = datetime.now(timezone.utc)
    elif not isinstance(created_at, datetime):
        created_at = datetime.now(timezone.utc)

    priority = entry_dict.get("priority", "P2")
    if isinstance(priority, str):
        try:
            priority = TicketPriority(priority)
        except Exception:
            priority = TicketPriority.P2

    return ActifixEntry(
        message=entry_dict.get("message", ""),
        source=entry_dict.get("source", ""),
        run_label=entry_dict.get("run_label", ""),
        entry_id=entry_dict.get("entry_id", ""),
        created_at=created_at,
        priority=priority,
        error_type=entry_dict.get("error_type", "unknown"),
        stack_trace=entry_dict.get("stack_trace", ""),
        file_context=entry_dict.get("file_context", {}) or {},
        system_state=entry_dict.get("system_state", {}) or {},
        ai_remediation_notes=entry_dict.get("ai_remediation_notes", ""),
        duplicate_guard=entry_dict.get("duplicate_guard", ""),
        format_version=entry_dict.get("format_version", "1.0"),
        correlation_id=entry_dict.get("correlation_id"),
    )


def replay_fallback_queue(base_dir: Path = ACTIFIX_DIR) -> int:
    """Replay entries from fallback queue to the database."""
    queue_file = _get_fallback_queue_file(base_dir)
    legacy_file = base_dir / LEGACY_FALLBACK_QUEUE

    try:
        queue, source_path = _load_existing_queue(queue_file, legacy_file)
        if not queue:
            return 0

        replayed = 0
        failed = []
        from .persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()

        for entry_dict in queue:
            try:
                entry = _entry_from_dict(entry_dict)
                created = repo.create_ticket(entry)
                if created or repo.check_duplicate_guard(entry.duplicate_guard):
                    replayed += 1
                else:
                    failed.append(entry_dict)
            except Exception:
                failed.append(entry_dict)

        # Update queue with only failed entries
        if failed:
            _persist_queue(failed, queue_file, legacy_file)
        else:
            queue_file.unlink(missing_ok=True)
            if source_path != queue_file:
                source_path.unlink(missing_ok=True)

        return replayed
    except Exception:
        return 0


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
    force_context: bool = False,
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
        force_context: Ignore priority gates when True and keep context capture.

    Returns:
        ActifixEntry with all captured context, or None if duplicate detected
    """
    # Resolve paths
    active_paths = paths or (
        _get_cached_actifix_paths(base_dir=base_dir)
        if base_dir
        else _get_cached_actifix_paths()
    )
    base_dir_path = active_paths.base_dir

    # Enforce Raise_AF-only policy before proceeding
    enforce_raise_af_only(active_paths)
    
    # Clean inputs
    clean_message = message.strip()
    clean_source = source.strip() or "unknown"
    clean_run_label = run_label.strip() or "unspecified"
    clean_error_type = error_type.strip() or "unknown"

    if STRUCTURED_MESSAGE_ENFORCED:
        clean_message = _ensure_structured_message(clean_message)

    ensure_scaffold(base_dir_path)
    init_actifix_files(active_paths)

    # Capture stack trace early so duplicate guards can incorporate error context
    resolved_stack_trace = stack_trace if stack_trace is not None else capture_stack_trace()

    # Generate duplicate guard early for checking
    duplicate_guard = generate_duplicate_guard(
        clean_source,
        clean_message,
        clean_error_type,
        resolved_stack_trace,
    )

    # LOOP PREVENTION: Check if this error already has a ticket
    if not skip_duplicate_check:
        try:
            from .persistence.ticket_repo import get_ticket_repository
            repo = get_ticket_repository()
            existing = repo.check_duplicate_guard(duplicate_guard)
            if existing and existing['status'] in ('Open', 'In Progress'):
                return None
        except Exception:
            pass

    # Auto-classify priority if not provided
    if isinstance(priority, str):
        try:
            priority = TicketPriority(priority)
        except Exception:
            priority = None

    if priority is None:
        priority = classify_priority(clean_error_type, clean_message, clean_source)

    effective_capture_context = capture_context
    context_gate_triggered = (
        capture_context
        and not force_context
        and priority.value in MINIMAL_CONTEXT_PRIORITIES
    )
    if context_gate_triggered:
        effective_capture_context = False

    config = get_config()

    env_flag = os.getenv(ACTIFIX_CAPTURE_ENV_VAR, "").strip().lower()
    _positive_capture = {"1", "true", "yes", "on", "debug"}
    _negative_capture = {"0", "false", "no", "off"}
    capture_enabled = config.capture_enabled

    if env_flag in _positive_capture:
        capture_enabled = True
    elif env_flag in _negative_capture:
        capture_enabled = False

    if paths is not None and env_flag not in _negative_capture:
        capture_enabled = True

    if not capture_enabled:
        _log_capture_disabled(clean_source, clean_error_type)
        return None

    context_meta = {
        "requested": capture_context,
        "effective": effective_capture_context,
        "priority_gate": priority.value if context_gate_triggered else None,
        "force_context": force_context,
        "token_savings_estimate": CONTEXT_TRUNCATION_CHARS if context_gate_triggered else 0,
    }

    # THROTTLE CHECK: Prevent ticket floods
    try:
        from .security.ticket_throttler import get_ticket_throttler, TicketThrottleError

        if config.ticket_throttling_enabled:
            throttler = get_ticket_throttler()
            throttler.check_throttle(priority, clean_error_type)
    except TicketThrottleError as e:
        # Throttle limit exceeded - log and return None
        try:
            import logging
            logger = logging.getLogger("actifix.raise_af")
            logger.warning(f"Ticket throttled: {e}")
        except Exception:
            pass
        return None
    except Exception:
        # Throttle check failed - continue anyway (fail open)
        pass

    # Capture context
    path_cache_snapshot = _snapshot_path_cache_stats()
    file_context = {}
    if effective_capture_context:
        file_context = capture_file_context(clean_source)
        system_state = capture_system_state()
    else:
        system_state = {"path_cache": path_cache_snapshot}

    system_state.setdefault("path_cache", path_cache_snapshot)
    system_state.setdefault("context_control", context_meta)
    system_state.setdefault("context_control", context_meta)

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
        stack_trace=resolved_stack_trace,
        file_context=file_context,
        system_state=system_state,
        duplicate_guard=duplicate_guard,
        correlation_id=correlation_id,
    )

    # Generate AI remediation notes
    if not skip_ai_notes:
        entry.ai_remediation_notes = generate_ai_remediation_notes(entry)

    # Try database first, fall back to queue
    try:
        from .persistence.ticket_repo import get_ticket_repository
        repo = get_ticket_repository()
        created = repo.create_ticket(entry)
        if not created:
            return None

        # Record ticket creation in throttler
        try:
            from .security.ticket_throttler import get_ticket_throttler

            if config.ticket_throttling_enabled:
                throttler = get_ticket_throttler()
                throttler.record_ticket(priority, entry.entry_id, clean_error_type)
        except Exception:
            # Throttle recording failure shouldn't block ticket creation
            pass

        log_event(
            "TICKET_CREATED",
            f"Recorded ticket {entry.entry_id}",
            ticket_id=entry.entry_id,
            extra={"run": entry.run_label},
        )
        replay_fallback_queue(base_dir_path)
    except Exception:
        log_event(
            "FALLBACK_QUEUE",
            f"Queued ticket {entry.entry_id} for later replay",
            ticket_id=entry.entry_id,
            extra={"run": entry.run_label},
        )
        _queue_to_fallback(entry, base_dir_path)

    return entry


def _append_rollup_entry(paths: ActifixPaths, entry: ActifixEntry) -> None:
    """No-op: rollup/history are now database views."""
    return None


def _read_recent_entries(recent_path: Path) -> list[str]:
    """Read recent rollup entries from the database view."""
    try:
        from .persistence.database import get_database_pool

        pool = get_database_pool()
        with pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT created_at, id, priority, error_type, message
                FROM v_recent_tickets
                ORDER BY created_at DESC
                """
            )
            entries = []
            for row in cursor.fetchall():
                message = (row["message"] or "").replace("\n", " ").strip()
                entries.append(
                    f"{row['created_at']} | {row['id']} | {row['priority']} | "
                    f"{row['error_type']} | {message}"
                )
            return entries
    except Exception:
        return []


def _append_recent(entry: ActifixEntry, base_dir: Path) -> None:
    """Compatibility shim (no-op)."""
    return None


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
