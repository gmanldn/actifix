# Actifix Quickstart

Actifix is a self-improving error management framework that captures prioritized tickets, feeds AI copilots, and keeps watching its own development.

## Why it matters
- **AI-ready capture** with stack, file, system context, and remediation notes tailored for Claude/GPT/Ollama.
- **Self-development mode** that tickets regressions in the framework while you code.
- **Production resilience** with atomic writes, fallback queues, and a database-first workflow.

## Prerequisites
- Python 3.10+ and Git
- Optional: `venv` or another virtualenv manager
- `ACTIFIX_CHANGE_ORIGIN` must be set to `raise_af` before running scripts or editing code (see README)

## Setup in minutes
1. Clone and enter the repo
   ```bash
   git clone https://github.com/gmanldn/actifix.git
   cd actifix
   ```
2. Create a virtual environment and install
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   pip install -e "[dev]"  # optional tooling
   ```
3. Initialize Actifix and start the watcher
   ```bash
   python scripts/start.py  # watches pyproject.toml and enforces raise_af guard
   python -m actifix.main health
   ```

## Capture your first error
```python
import sys
sys.path.insert(0, "src")
import actifix

actifix.enable_actifix_capture()
try:
    risky_operation()
except Exception as exc:
    actifix.record_error(
        message=str(exc),
        source=f"{__file__}:{sys._getframe().f_lineno}",
        run_label="quickstart",
        error_type=type(exc).__name__,
        capture_context=True,
    )
```

## Self-development mode (Actifix watches itself)
```python
import actifix
actifix.bootstrap_actifix_development()
actifix.track_development_progress(
    "Quickstart verified",
    "Actifix captured its own startup path"
)
```

## Inspect the ticket stream
- `sqlite3 data/actifix.db "SELECT id, priority, status, message FROM tickets ORDER BY created_at DESC LIMIT 5;"`
- `sqlite3 data/actifix.db "SELECT * FROM v_recent_tickets;"`
- `python -m actifix.main stats`
- `python -m actifix.main record P2 "test" "demo.py:10"`

## Keep the workflow clean
- Tickets live exclusively in `data/actifix.db`; legacy Markdown task lists were removed.
- Use Raise_AF (`actifix.raise_af.record_error`), DoAF, or the CLI to create, inspect, process, and close tickets.
- Read [`docs/FRAMEWORK_OVERVIEW.md`](FRAMEWORK_OVERVIEW.md) for architecture, release notes, and roadmap, and [`docs/DEVELOPMENT.md`](DEVELOPMENT.md) for workflow standards.