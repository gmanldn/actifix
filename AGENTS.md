# Actifix Agent Instructions

All Changes Must Start via Raise_AF

## Mandatory Rules

1. **Branch workflow**: Create branch → work → commit → merge to develop → delete branch → push
2. **Tests required**: `python test.py --coverage` must pass with 95%+ coverage before commit
3. **Version bump**: Increment version in `pyproject.toml` after every commit
4. **No plan docs**: Never create `*_PLAN.md`, `ROADMAP.md`, `DESIGN.md` files
5. **All errors via raise_af**: Use `actifix.raise_af.record_error()` for all error capture
6. **Raise_AF gate**: Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or making changes (enforced)

```bash
# Commit convention
git commit -m "type(scope): description"
# types: feat|fix|refactor|test|docs|chore|perf
```

---

## Architecture

```
src/actifix/
├── bootstrap.py      # System init. Use ActifixContext or bootstrap()
├── state_paths.py    # Path management. Use get_actifix_paths()
├── config.py         # Config. Use load_config()
├── raise_af.py       # ERROR CAPTURE. Use record_error()
├── do_af.py          # Ticket processing. Use get_open_tickets(), mark_ticket_complete()
├── health.py         # Health checks. Use get_health()
├── quarantine.py     # Isolate bad data. Use quarantine_content()
├── api.py            # REST API server
├── main.py           # CLI entrypoint
├── log_utils.py      # Atomic file ops. Use atomic_write()
└── persistence/      # Storage layer (atomic.py, storage.py, queue.py, manager.py)
```

**Dependency rule**: Lower layers cannot import higher layers. bootstrap → state_paths → config → log_utils → persistence → raise_af → do_af → api → main

---

## Core APIs

### Record an error
```python
from actifix.raise_af import record_error, TicketPriority
record_error(message="Error msg", source="file.py:42", priority=TicketPriority.P1)
```

### Process tickets
```python
from actifix.do_af import get_open_tickets, mark_ticket_complete, get_ticket_stats
tickets = get_open_tickets()  # Sorted by priority (P0 first)
mark_ticket_complete("ACT-20260110-abc12", "Fixed by adding null check")
```

### System init
```python
from actifix.bootstrap import ActifixContext
with ActifixContext() as paths:
    # System ready, exceptions auto-captured
```

### Paths
```python
from actifix.state_paths import get_actifix_paths
paths = get_actifix_paths()
# paths.list_file, paths.logs_dir, paths.state_dir, etc.
```

---

## File Locations

| File | Path | Purpose |
|------|------|---------|
| Ticket list | `actifix/ACTIFIX-LIST.md` | All open/completed tickets |
| Recent errors | `actifix/ACTIFIX.md` | Last 20 errors (rollup) |
| Audit log | `actifix/AFLog.txt` | Event history |
| Quarantine | `actifix/quarantine/` | Isolated corrupt data |
| State | `.actifix/` | Internal state, fallback queue |

---

## Ticket Format (ACTIFIX-LIST.md)

```markdown
## Active Items

### ACT-20260110-XXXXX - [P1] ErrorType: Message
- **Priority**: P1
- **Source**: `file.py:42`
- **Created**: 2026-01-10T12:00:00Z
- **Duplicate Guard**: `hash`
- **Status**: Open

<details><summary>Stack Trace Preview</summary>...</details>
<details><summary>AI Remediation Notes</summary>...</details>

## Completed Items
(same format, checkboxes marked [x])
```

---

## Priority Levels

| Priority | SLA | Trigger keywords |
|----------|-----|------------------|
| P0 | 1hr | fatal, crash, corrupt, data loss |
| P1 | 4hr | database, security, auth, core |
| P2 | 24hr | Default for most errors |
| P3 | 72hr | warning, deprecation |
| P4 | 1wk | style, lint, format |

---

## Error Flow

```
Exception → bootstrap (exception handler) → record_error()
  → check_duplicate_guard() → skip if exists
  → capture context (stack, files, system state)
  → classify_priority()
  → redact_secrets()
  → append to ACTIFIX-LIST.md (or fallback queue if fails)
  → update ACTIFIX.md rollup
  → log to AFLog.txt
```

---

## Critical Rules

- **Atomic writes only**: Use `atomic_write()`, never raw `open().write()`
- **Never suppress errors**: Always `record_error()` then re-raise
- **Paths via ActifixPaths**: Never construct paths manually
- **Duplicate guards**: System auto-deduplicates; don't bypass
- **Fallback queue**: If main storage fails, errors queue to `.actifix/actifix_fallback_queue.json` and replay on recovery
