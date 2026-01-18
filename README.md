# Actifix - Self-Improving Error Management Framework

> The framework that tracks and improves itself.
> Read `AGENTS.md` before making changes.

Actifix captures, prioritizes, and deduplicates production errors. Tickets include rich context for AI copilots, and the framework can monitor its own development to keep regressions visible. Everything is stdlib-first with resilient persistence in `data/actifix.db`.

## Highlights
- Zero-dependency capture: `enable_actifix_capture()` drops in without extra packages.
- AI-ready tickets: stack traces, file context, system state, remediation notes.
- Self-development mode: the framework can ticket its own regressions.
- Durable persistence: atomic writes, fallback queues, and database-first storage.

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

## Workflow guardrails
- Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or making changes.
- Capture errors via `actifix.raise_af.record_error(...)` and re-raise when needed.
- Keep `docs/INDEX.md` in sync with documentation changes.

## Documentation
- `docs/INDEX.md` - documentation hub
- `docs/QUICKSTART.md` - hands-on setup
- `docs/FRAMEWORK_OVERVIEW.md` - architecture and release notes
- `docs/DEVELOPMENT.md` - workflow and quality gates
