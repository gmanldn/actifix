"""
Actifix Quarantine - Corruption handling and malformed data isolation.

Provides quarantine system for corrupted or malformed tickets/data.
Corruption is quarantined, not fatal - allowing system to continue.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .log_utils import atomic_write, log_event
from .state_paths import get_actifix_paths, ensure_actifix_dirs, ActifixPaths


@dataclass
class QuarantineEntry:
    """A quarantined item."""
    
    entry_id: str
    original_source: str
    reason: str
    content: str
    quarantined_at: datetime
    file_path: Path


def generate_quarantine_id() -> str:
    """Generate unique quarantine entry ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"quarantine_{timestamp}"


def quarantine_content(
    content: str,
    source: str,
    reason: str,
    paths: Optional[ActifixPaths] = None,
) -> QuarantineEntry:
    """
    Quarantine malformed or corrupted content.
    
    Args:
        content: The content to quarantine.
        source: Original source (e.g., file path, ticket ID).
        reason: Reason for quarantine.
        paths: Optional paths override.
    
    Returns:
        QuarantineEntry with details.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    ensure_actifix_dirs(paths)
    
    # Generate entry
    entry_id = generate_quarantine_id()
    quarantined_at = datetime.now(timezone.utc)
    
    # Create quarantine file
    filename = f"{entry_id}.md"
    file_path = paths.quarantine_dir / filename
    
    # Format quarantine content
    quarantine_content = f"""# Quarantined Content

- **Entry ID**: {entry_id}
- **Source**: {source}
- **Reason**: {reason}
- **Quarantined At**: {quarantined_at.isoformat()}

## Original Content

```
{content}
```

## Recovery Notes

To recover this content:
1. Review the content above
2. Fix any issues
3. Manually reintegrate if needed
4. Delete this file when resolved
"""
    
    atomic_write(file_path, quarantine_content)
    
    # Log the quarantine
    log_event(
        "CONTENT_QUARANTINED",
        f"Quarantined content from {source}: {reason}",
        extra={
            "entry_id": entry_id,
            "source": source,
            "reason": reason,
        }
    )
    
    return QuarantineEntry(
        entry_id=entry_id,
        original_source=source,
        reason=reason,
        content=content,
        quarantined_at=quarantined_at,
        file_path=file_path,
    )


def quarantine_file(
    file_path: Path,
    reason: str,
    paths: Optional[ActifixPaths] = None,
) -> Optional[QuarantineEntry]:
    """
    Quarantine an entire file.
    
    Args:
        file_path: Path to file to quarantine.
        reason: Reason for quarantine.
        paths: Optional paths override.
    
    Returns:
        QuarantineEntry if successful, None if file doesn't exist.
    """
    if not file_path.exists():
        return None
    
    content = file_path.read_text()
    source = str(file_path)
    
    entry = quarantine_content(content, source, reason, paths)
    
    # Move original file
    backup_name = f"{entry.entry_id}_original{file_path.suffix}"
    if paths is None:
        paths = get_actifix_paths()
    
    backup_path = paths.quarantine_dir / backup_name
    shutil.copy2(file_path, backup_path)
    
    return entry


def list_quarantine(
    paths: Optional[ActifixPaths] = None,
) -> list[QuarantineEntry]:
    """
    List all quarantined items.
    
    Args:
        paths: Optional paths override.
    
    Returns:
        List of QuarantineEntry objects.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    entries = []
    
    if not paths.quarantine_dir.exists():
        return entries
    
    for file_path in paths.quarantine_dir.glob("quarantine_*.md"):
        content = file_path.read_text()
        
        # Parse entry from content
        entry_id = file_path.stem
        
        # Extract metadata
        source = ""
        reason = ""
        quarantined_at = datetime.now(timezone.utc)
        original_content = ""
        
        for line in content.split("\n"):
            if line.startswith("- **Entry ID**:"):
                entry_id = line.split(":")[1].strip()
            elif line.startswith("- **Source**:"):
                source = line.split(":", 1)[1].strip()
            elif line.startswith("- **Reason**:"):
                reason = line.split(":", 1)[1].strip()
            elif line.startswith("- **Quarantined At**:"):
                try:
                    dt_str = line.split(":", 1)[1].strip()
                    quarantined_at = datetime.fromisoformat(dt_str)
                except ValueError:
                    pass
        
        # Extract original content
        if "## Original Content" in content:
            parts = content.split("## Original Content")
            if len(parts) > 1:
                content_section = parts[1]
                if "```" in content_section:
                    code_parts = content_section.split("```")
                    if len(code_parts) >= 2:
                        original_content = code_parts[1].strip()
        
        entries.append(QuarantineEntry(
            entry_id=entry_id,
            original_source=source,
            reason=reason,
            content=original_content,
            quarantined_at=quarantined_at,
            file_path=file_path,
        ))
    
    # Sort by date (newest first)
    entries.sort(key=lambda e: e.quarantined_at, reverse=True)
    
    return entries


def remove_quarantine(
    entry_id: str,
    paths: Optional[ActifixPaths] = None,
) -> bool:
    """
    Remove an item from quarantine.
    
    Args:
        entry_id: Entry ID to remove.
        paths: Optional paths override.
    
    Returns:
        True if removed, False if not found.
    """
    if paths is None:
        paths = get_actifix_paths()
    
    # Find and remove the quarantine file
    file_path = paths.quarantine_dir / f"{entry_id}.md"
    
    if file_path.exists():
        file_path.unlink()
        
        # Also remove original file backup if exists
        for backup in paths.quarantine_dir.glob(f"{entry_id}_original*"):
            backup.unlink()
        
        log_event(
            "QUARANTINE_REMOVED",
            f"Removed quarantine entry: {entry_id}",
        )
        return True
    
    return False


def get_quarantine_count(paths: Optional[ActifixPaths] = None) -> int:
    """Get count of quarantined items."""
    if paths is None:
        paths = get_actifix_paths()
    
    if not paths.quarantine_dir.exists():
        return 0
    
    return len(list(paths.quarantine_dir.glob("quarantine_*.md")))
