# Actifix Agent Instructions

All Changes Must Start via Raise_AF

## Mandatory Rules

1. **Workflow**: Work directly on `develop` with regular pushes; no per-change branches required.
1.1 **Readme** Always read the readme
3. **Version bump**: Increment version in `pyproject.toml` after every commit
4. **No plan docs**: Never create `*_PLAN.md`, `ROADMAP.md`, `DESIGN.md` files
5. **No new documentation files**: Do not create new documentation files (e.g., feature-specific `.md` files). Instead, blend content into existing docs:
   - Use `docs/FRAMEWORK_OVERVIEW.md` for feature documentation and release notes
   - Update `docs/INDEX.md` to cross-reference new sections
   - Update `docs/DEVELOPMENT.md` for development workflow changes
   - Maintain the existing documentation hierarchy
6. **All errors via raise_af**: Use `actifix.raise_af.record_error()` for all error capture
7. **Raise_AF gate**: Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or making changes (enforced)
8. **Architecture graph first**: Always open `docs/architecture/MAP.yaml` and `docs/architecture/DEPGRAPH.json` before starting work so you understand the canonical module/edge graph, and ensure every change is reflected there before committing
9. **Rules** 
Always follow the actifix rules.
Always commit after every ticket and push.

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
# paths.base_dir, paths.logs_dir, paths.state_dir, etc.
```

---

## File Locations

| File | Path | Purpose |
|------|------|---------|
| **Ticket database** | `data/actifix.db` | **CANONICAL SQLite store for all tickets** |
| Quarantine | `actifix/quarantine/` | Isolated corrupt data |
| State | `.actifix/` | Internal state, fallback queue |

**Note**: The database (`data/actifix.db`) is the single source of truth. All ticket data is stored here.

---

## Ticket Format (SQLite `tickets` table)

```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    priority TEXT NOT NULL,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT NOT NULL,
    run_label TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    duplicate_guard TEXT UNIQUE,
    status TEXT DEFAULT 'Open',
    owner TEXT,
    locked_by TEXT,
    lease_expires TIMESTAMP,
    branch TEXT,
    stack_trace TEXT,
    file_context TEXT,
    system_state TEXT,
    ai_remediation_notes TEXT,
    correlation_id TEXT,
    completion_summary TEXT,
    documented BOOLEAN DEFAULT 0,
    functioning BOOLEAN DEFAULT 0,
    tested BOOLEAN DEFAULT 0,
    completed BOOLEAN DEFAULT 0
);
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
  → persist to `data/actifix.db` via `TicketRepository`
```

---

## Critical Rules

- **Atomic writes only**: Use `atomic_write()`, never raw `open().write()`
- **Never suppress errors**: Always `record_error()` then re-raise
- **Paths via ActifixPaths**: Never construct paths manually
- **Duplicate guards**: System auto-deduplicates; don't bypass
- **Fallback queue**: If main storage fails, errors queue to `.actifix/actifix_fallback_queue.json` and replay on recovery