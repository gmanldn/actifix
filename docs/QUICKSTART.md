# Actifix Quickstart

Actifix captures prioritized tickets with rich context and keeps a database-first audit trail. This guide gets you from clone to first ticket in minutes.

## Prerequisites
- Python 3.10+
- Git
- Optional: `venv` or another virtualenv manager

## Fast setup
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
3. Start the launcher (sets the Raise_AF guard automatically):
   ```bash
   python3 scripts/start.py
   ```
4. Verify the system health:
   ```bash
   python3 -m actifix.main health
   ```

## Launcher options
```bash
# Start everything (default)
python3 scripts/start.py

# Health check only
python3 scripts/start.py --health-only

# Setup only (no servers)
python3 scripts/start.py --setup-only

# Disable API server
python3 scripts/start.py --no-api

# Custom ports
python3 scripts/start.py --frontend-port 8081 --api-port 5002

# Auto-stop after a fixed duration (helpful for automation)
python3 scripts/start.py --run-duration 30
```

## Capture your first error
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
        run_label="quickstart",
        error_type=type(exc).__name__,
        capture_context=True,
    )
```

## Record a ticket from the CLI
```bash
python3 -m actifix.main record ManualProbe "Quickstart smoke test" "docs/QUICKSTART.md:1" --priority P2
```

## Inspect the ticket stream
```bash
sqlite3 data/actifix.db "SELECT id, priority, status, message FROM tickets ORDER BY created_at DESC LIMIT 5;"
sqlite3 data/actifix.db "SELECT * FROM v_recent_tickets;"
python3 -m actifix.main stats
```

## Self-development mode
```python
import actifix

actifix.bootstrap_actifix_development()
actifix.track_development_progress(
    "Quickstart verified",
    "Actifix captured its own startup path",
)
```

## Keep the workflow clean
- Tickets live in `data/actifix.db`; do not edit it manually.
- Always use Raise_AF (`actifix.raise_af.record_error`), DoAF, the CLI, or SQL for ticket lifecycle work.
- Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or making edits (the launcher sets it for you).

## Next steps
- `docs/INSTALLATION.md` for configuration and dependencies
- `docs/FRAMEWORK_OVERVIEW.md` for architecture and release notes
- `docs/DEVELOPMENT.md` for workflow, testing, and quality gates
