# Actifix - Self-Improving Error Management Framework

> The framework that tracks and improves itself.
> Read `AGENTS.md` before making changes.

Note: `CLAUDE.md` is a repo-local symlink to `AGENTS.md` for tool compatibility; treat them as the same instructions.

Actifix captures, prioritizes, and deduplicates production errors. Tickets include rich context for AI copilots, and the framework can monitor its own development to keep regressions visible. Everything is stdlib-first with resilient persistence in `data/actifix.db`.

## Highlights
- Zero-dependency capture: `enable_actifix_capture()` drops in without extra packages.
- AI-ready tickets: stack traces, file context, system state, remediation notes.
- Self-development mode: the framework can ticket its own regressions.
- Durable persistence: atomic writes, fallback queues, and database-first storage.
- Always-on context: the `modules.screenscan` module keeps a last-minute screenshot ring buffer for debugging UI/app behavior.

## Screenscan module (mandatory)
`modules.screenscan` is a **critical, always-on** module. It captures screenshots **2x per second** (configurable), stores them in an **optimized SQLite ring-buffer table**, and retains **only the last minute** of frames (no unbounded growth). Performance is critical: capture+persist runs in a **worker thread** and must never block API request handling.

Enforcement:
- System health **must** include `modules.screenscan` and will be treated as degraded/failed when screenscan is not running (unless explicitly allowed for headless/test).
- The module must be covered by tests (ring-buffer correctness + worker lifecycle) and must stay green.
- Screenshots are sensitive: do not write image bytes into logs, AgentVoice, or Raise_AF ticket context.

## Quickstart
1. Clone and enter the repo:
   ```bash
   git clone https://github.com/gmanldn/actifix.git
   cd actifix
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install -e .
   python3 -m pip install -e "[dev]"  # optional tooling
   ```
3. Start the development launcher (sets Raise_AF guard automatically):
   ```bash
   python3 scripts/start.py
   ```
4. Run a health check:
   ```bash
   python3 -m actifix.main health
   ```
   Verify that `modules.screenscan` is present in the output.
5. Read the docs index for deeper guides:
   ```text
   docs/INDEX.md
   ```

## Capture an error
```python
import sys
import actifix

actifix.enable_actifix_capture()

try:
    risky_operation()
except Exception as exc:
    actifix.record_error(
        message=str(exc),
        source=f"{__file__}:{sys._getframe().f_lineno}",
        run_label="production-api",
        error_type=type(exc).__name__,
        capture_context=True,
    )
```

## Self-development mode
```python
import actifix

actifix.bootstrap_actifix_development()
actifix.track_development_progress(
    "Feature complete",
    "AI telemetry integrated",
)
```

## Core CLI commands
- `python3 -m actifix.main init`
- `python3 -m actifix.main record ManualRecord "message" "module.py:42" --priority P2`
- `python3 -m actifix.main process --max-tickets 5`
- `python3 -m actifix.main stats`
- `python3 -m actifix.main quarantine list`
- `python3 -m actifix.main test`
- `ACTIFIX_CHANGE_ORIGIN=raise_af python3 Do_AF.py [batch_size]`

## Database-first workflow
- Canonical store: `data/actifix.db` (tickets, event log, rollups).
- Use Raise_AF, DoAF, the CLI, or SQL for ticket lifecycle work.
- Avoid manual edits to the database or legacy Markdown task lists.

## Raise_AF Ticketing Requirement

All code changes to Actifix must originate from a ticket created via `actifix.raise_af.record_error()`. This ensures:
- Every change is tracked and documented
- Regressions are visible in the ticket system
- AI assistants have context for improvements

Before making changes, always set:
```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
```

Create tickets programmatically:
```python
import actifix

actifix.record_error(
    message="Description of issue or improvement",
    source="module.py:line",
    error_type="BugFix",  # or "Feature", "Refactor", etc.
    priority=actifix.TicketPriority.P2,
)
```

## Workflow guardrails
- Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or making changes.
- Capture errors via `actifix.raise_af.record_error(...)` and re-raise when needed.
- Keep `docs/INDEX.md` in sync with documentation changes.

## Multi-Agent Workflow

Actifix supports multiple AI agents working together on the codebase.

### Collaboration Model
- **Work on `develop`**: Agents make changes directly on the `develop` branch. No per-change branches requiredjust regular commits and pushes after each ticket.
- **Isolated State**: Each agent uses a unique `ACTIFIX_DATA_DIR` for local database (`data/actifix.db`), logs, and state to prevent conflicts.
- **Database Untracked**: `data/actifix.db` is in `.gitignore`, allowing independent ticket views and processing per agent without merge issues.

### Quick-Start Agent Setup
```bash
# Create isolated dir for this agent
mkdir -p ~/actifix-agent-$(date +%s)/data
export ACTIFIX_DATA_DIR=~/actifix-agent-$(date +%s)

# Enforce workflow guard
export ACTIFIX_CHANGE_ORIGIN=raise_af

# View tickets
python3 scripts/view_tickets.py

# Process (manual or auto)
python3 Do_AF.py 1  # or fix manually per AGENTS.md
```

Agents sync via git pull/push after commits.

## Documentation
- `docs/INDEX.md` - documentation hub
- `docs/QUICKSTART.md` - hands-on setup
- `docs/FRAMEWORK_OVERVIEW.md` - architecture and release notes
- `docs/DEVELOPMENT.md` - workflow and quality gates
