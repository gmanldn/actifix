# Actifix - Self-Improving Error Management Framework

> **The framework that tracks and improves itself.** 🚀  
> **Always read AGENTS.md before making changes.**

Actifix is a self-improving error management framework that captures rich context, prioritizes issues, and produces AI-ready tickets. It can even watch its own codebase, generate tickets for its own problems, and guide fixes through AI copilots.

## What Actifix Offers

- 🎯 **Production-grade capture**: Priority classification (P0–P4), duplicate guards, atomic writes, fallback queues, and secret redaction out of the box.
- 📦 **Drop-in usage**: Pure-stdlib Python package—import it, call `enable_actifix_capture()`, and start recording tickets immediately.
- 🧠 **AI-native**: Generates remediation notes, normalized context, and 200k-token-friendly bundles for Claude, GPT, or any LLM.
- 🔁 **Self-improvement mode**: Actifix watches its own development, opening tickets against itself as you code.
- 🗂️ **Transparent artifacts**: SQLite ticket database (`data/actifix.db`) is the canonical store; `ACTIFIX.md`, `ACTIFIX-LOG.md`, and `AFLog.txt` are generated, read-only snapshots for auditing and diagnostics.
- 🛠️ **Configurable by environment**: Tune data/state directories, context capture limits, and capture enablement with env vars—no code changes needed.

## How It Works (Lifecycle)

1) **Capture**: `enable_actifix_capture()` installs the global hooks; `record_error(...)` ingests an exception with stack trace, file context, and system state.  
2) **Normalize**: Secret redaction, priority inference, duplicate guard hashing, and optional manual priority override.  
3) **Persist**: Ticket data lands inside the canonical `data/actifix.db`; Markdown rollups and logs under `actifix/` are generated from that table and must not be edited manually.  
4) **Dispatch (planned)**: `DoAF` ticket processor will route items for AI/automation, dedupe, and mark completion.  
5) **Improve**: Self-development mode raises tickets against Actifix itself, keeping the framework honest and continually improving.

## Feature Breakdown

- **Error intelligence**: Auto-priority (P0–P4), deduplication, remediation hints, and stack/file/system snapshots.  
- **Reliability guards**: Atomic writes, fallback queues, normalized paths, and configurable storage roots for container, server, or local use.  
- **Security by default**: Secret redaction for API keys, passwords, and PII before anything is persisted.  
- **AI readiness**: Compact, consistent context suitable for large-context models; remediation notes tailored for copilots.  
- **Self-development**: Bootstrap once and Actifix tracks its own regressions, milestones, and open work.  
- **Zero-dependency core**: Uses Python stdlib only—easy to embed anywhere.

## Quick Start

### Install / Import
```bash
git clone https://github.com/gmanldn/actifix.git
cd actifix
# Pure stdlib; no pip install required to start using the framework
```

> `python scripts/start.py` now watches `pyproject.toml` once per minute and restarts the static frontend server automatically when the project version changes so the UI refreshes after pushes.

### Capture Your First Error
```python
import sys
sys.path.insert(0, 'src')
import actifix

actifix.enable_actifix_capture()  # install the capture hooks

try:
    risky_operation()
except Exception as e:
    actifix.record_error(
        message=str(e),
        source='my_module.py:42',
        run_label='my-application',
        error_type=type(e).__name__,
        capture_context=True,  # include file/system context
    )
```

### Turn On Self-Development Mode
```python
import actifix

actifix.bootstrap_actifix_development()  # installs handlers and creates scaffold
actifix.create_initial_ticket()
actifix.track_development_progress(
    "New feature completed",
    "Implemented advanced error tracking"
)
```

### Inspect Tickets
```bash
sqlite3 data/actifix.db "SELECT id, priority, status, message, run_label FROM tickets ORDER BY
    CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
    created_at DESC LIMIT 30;"
cat actifix/ACTIFIX.md        # latest 20 entries (read-only audit rollup)
tail -n 50 actifix/AFLog.txt  # lifecycle log (generated from the DB)
```

## Core API Surface

- `enable_actifix_capture()`: Install global exception handling and capture hooks.  
- `record_error(message, source, run_label, error_type, priority=None, capture_context=False)`: Persist a ticket with optional priority override and context capture.  
- `bootstrap_actifix_development()`: Enable Actifix to track its own development lifecycle.  
- `track_development_progress(title, detail)`: Log milestones as tickets.  
- `create_initial_ticket()`: Seed the project with a starter ticket in self-development mode.

See `src/actifix/` for implementation details: `raise_af.py` (capture engine), `bootstrap.py` (self-development), and `state_paths.py` (state management).

## Raise_AF Ticketing Requirement

All work must begin by logging the condition through `actifix.raise_af.record_error(...)` so a structured row lands in `data/actifix.db` with the proper priority and context. Legacy Markdown lists such as `TASK_LIST.md`, `Actifix-list.md`, or `ACTIFIX-LIST.md` have been removed—tickets are created, queried, and completed only through the database, DoAF, or the Actifix API. This keeps the RaiseAF pipeline as the single source of truth and ensures the AI/automation workflow stays honest. Enforcement is active: set `ACTIFIX_CHANGE_ORIGIN=raise_af` (default enforced) before running Actifix or changes fail fast.

## Database-first Workflow

- **Canonical store**: `data/actifix.db` holds every ticket, duplicate guard, status change, and remediation note. Treat it as the only writable source.
- **Generated artifacts**: `ACTIFIX.md`, `ACTIFIX-LOG.md`, and `AFLog.txt` live inside `actifix/` for auditing; they are mirrors of the ticket database and must never be edited directly.
- **Ticket access**: Use `actifix.raise_af.record_error`, `actifix.do_af` helpers, the REST API, or raw `sqlite3` queries to inspect, update, or complete work.
- **Automation rule**: Manual Markdown task lists are forbidden—automation, AI, and developers rely on the schema in `data/actifix.db` to coordinate work.

## Configuration (Environment Variables)

- `ACTIFIX_CAPTURE_ENABLED`: Enable/disable capture (`1`, `true`, `yes`, `on`, `debug`).  
- `ACTIFIX_CHANGE_ORIGIN`: Must be `raise_af` when enforcement is on (default).  
- `ACTIFIX_ENFORCE_RAISE_AF`: Set to `0` only for emergency bypass (default `1`).  
- `ACTIFIX_DATA_DIR`: Data directory for tickets (default `./actifix`).  
- `ACTIFIX_STATE_DIR`: State directory (default `./.actifix`).  
- `ACTIFIX_FILE_CONTEXT_MAX_CHARS`: File context length (default `2000`).  
- `ACTIFIX_SYSTEM_STATE_MAX_CHARS`: System state length (default `1500`).

## Files and Directories

```
actifix/
├── src/actifix/          # Core framework
│   ├── raise_af.py       # Error capture engine
│   ├── bootstrap.py      # Self-development system
│   ├── state_paths.py    # State management
│   └── __init__.py       # Main API surface
├── test/                 # Test suite
│   └── test_actifix_basic.py
├── data/                 # Runtime storage
│   └── actifix.db        # SQLite ticket database (canonical source of truth and only writable registry)
├── actifix/              # Generated snapshots (do not edit)
│   ├── ACTIFIX.md        # Error rollup (last 20 entries)
│   ├── ACTIFIX-LOG.md    # Completion log derived from the DB
│   └── AFLog.txt         # Lifecycle audit trail (read-only)
└── docs/                 # Documentation
```

## Usage Patterns

- **Production monitoring**: Enable capture in your app entrypoint; let Actifix classify and dedupe, then pull Markdown tickets into your ops workflow.  
- **Developer safety net**: Keep capture on in local/dev; Actifix auto-opens tickets for regressions and flaky behaviors while you work.  
- **AI-assisted debugging**: Feed the ticket Markdown (with remediation notes) to your copilot for suggested fixes.  
- **Self-hosted improvement**: Run `bootstrap_actifix_development()` inside this repo; Actifix will ticket its own issues while you add features.

-It is absolutely critical that when an AI agent is asked to 'work on' or 'complete' tickets that it actually makes the needed changes to the codebase and checks they are made using actifix rules.

-Commit and push after every single ticket completed ALWAYS. Keep the working directory clean.


## Roadmap Snapshot

- ✅ Core capture, state management, bootstrap/self-development, Markdown artifacts, basic tests.  
- 🚧 In progress: DoAF ticket processor, validation framework, richer AI context.  
- 🗺️ Planned: Health monitoring, circuit breakers, retry/notification system, telemetry, AI integrations, web dashboard.

## Testing & Demo

```bash
# Basic tests
ACTIFIX_CAPTURE_ENABLED=1 python3 -m pytest test/test_actifix_basic.py -v

# Self-improvement demo (creates tickets against the framework itself)
python3 test/test_actifix_basic.py
```

## License

See [LICENSE](LICENSE) for details.

## Credits

Inspired by the sophisticated Actifix system from pokertool. Generalized and enhanced for universal use across any project.

---

**Built with ❤️ by the Actifix community — the framework that improves itself.**
