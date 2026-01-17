# Actifix - Self-Improving Error Management Framework

> The framework that tracks and improves itself. 🚀
> _Read `AGENTS.md` before making changes._

Actifix captures and prioritizes production errors, exposes a rich ticket stream for automation, and can even monitor its own development. It is AI-native, 100% stdlib, and built to keep working even when your systems are under stress.

## Highlights
- **Zero-dependency capture**: Drop in `actifix.enable_actifix_capture()` and immediately record prioritized, deduplicated tickets with stack, file, and system context.
- **AI-ready tickets**: Tickets include remediation notes, context windows tuned for Claude/GPT/Ollama, and normalized metadata for copilots.
- **Self-improvement**: `bootstrap_actifix_development()` lets Actifix watch its own code, automatically creating tickets whenever regressions occur.
- **Resilient persistence**: Atomic writes, fallback queues, and `data/actifix.db` as the canonical ticket store keep the system honest.

## Getting started (minutes)
1. `git clone https://github.com/gmanldn/actifix.git && cd actifix`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -e . && pip install -e "[dev]"`
4. `python scripts/start.py` (watches `pyproject.toml`, restarts the dev UI, and enforces the `ACTIFIX_CHANGE_ORIGIN=raise_af` guard).
5. Read [`docs/INDEX.md`](docs/INDEX.md) for concise links to installation, development, troubleshooting, and architecture guides.

## Capture & self-development
Enable capture:
```python
import actifix
actifix.enable_actifix_capture()
```
Record an error:
```python
actifix.record_error(
    message=str(exc),
    source=f"{__file__}:{sys._getframe().f_lineno}",
    run_label="production-api",
    error_type=type(exc).__name__,
    capture_context=True,
)
```
Track Actifix’s own development:
```python
actifix.bootstrap_actifix_development()
actifix.track_development_progress("Feature complete", "AI telemetry integrated")
```

## Core commands
- `python -m actifix.main record P2 "message" "module.py:42"`
- `python -m actifix.main process --max-tickets 5`
- `python -m actifix.main quarantine list`
- `python -m actifix.main test`

## Database-first workflow
- `data/actifix.db` is the only writable registry. All tickets, priority tiers, and remediation notes live here.
- Read-only rollups: `v_recent_tickets`, `v_ticket_history`, `event_log`.
- Legacy Markdown task lists (e.g., `TASK_LIST.md`) were retired—always use Raise_AF, DoAF, the CLI, or SQL to manage tickets.

## Environment variables
- `ACTIFIX_CAPTURE_ENABLED`: enable capture (`1`,`true`,`on`).
- `ACTIFIX_CHANGE_ORIGIN`: must be `raise_af` before running Actifix or committing changes.
- `ACTIFIX_DATA_DIR`, `ACTIFIX_STATE_DIR`, `ACTIFIX_LOGS_DIR`, `ACTIFIX_FILE_CONTEXT_MAX_CHARS`, `ACTIFIX_SYSTEM_STATE_MAX_CHARS` for tuning.

## Directory layout
```
actifix/
├── src/actifix/       # Core library (raise_af, bootstrap, state, APIs)
├── data/actifix.db    # Canonical ticket store
├── docs/              # Documentation (single source for updates)
├── logs/              # Rotating structured logs
├── test/              # Test suites and validators
├── actifix-frontend/  # Static dashboard
```

## Contribution guardrails
- Log every change via `actifix.raise_af.record_error(...)` before touching code.
- `ACTIFIX_CHANGE_ORIGIN=raise_af` must be set in your shell before running scripts or editing code.
- Do not author new `.md` task lists. Blend documentation updates into existing `docs/` files and keep `docs/INDEX.md` in sync.
- Always read and follow `AGENTS.md` instructions.

## Next references
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md): fast hands-on setup with snippets.
- [`docs/FRAMEWORK_OVERVIEW.md`](docs/FRAMEWORK_OVERVIEW.md): deeper architecture, release notes, and roadmap.
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md): workflow, testing, architecture, and documentation standards.