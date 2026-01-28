# Actifix Troubleshooting Guide

This guide lists common issues and fixes aligned to the current CLI and scripts.

## Import errors: No module named actifix
```bash
python3 -m pip install -e .
```

If you are running from a repo checkout without install:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/actifix/src"
```

## Raise_AF guard failures
Symptoms:
- "ACTIFIX_CHANGE_ORIGIN must be set to raise_af"

Fix:
```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
```

If you are using the launcher, it sets this automatically:
```bash
python3 scripts/start.py
```

## Tickets not being created
Checklist:
- `ACTIFIX_CAPTURE_ENABLED` is set to `1` or `true`.
- `ACTIFIX_CHANGE_ORIGIN=raise_af` is set.

Quick test:
```bash
python3 -m actifix.main record ManualProbe "ticket probe" "docs/TROUBLESHOOTING.md:1" --priority P2
```

## Database locked or slow
Symptoms:
- `sqlite3.OperationalError: database is locked`

Actions:
- Ensure no stale Actifix processes are running.
- Avoid running multiple test suites that write to `data/actifix.db` concurrently.
- Reproduce concurrency behavior with:
  ```bash
  python3 test_threading_barrier_debug.py
  ```
- Review ticket locking logic in `src/actifix/persistence/ticket_repo.py`.

## Frontend or API missing
If the dashboard fails to start, install web dependencies:
```bash
python3 -m pip install -e "[web]"
```

Restart the launcher:
```bash
python3 scripts/start.py
```

## Permission errors on data/actifix.db
```bash
ls -la data/actifix.db
chmod 600 data/actifix.db
```

## Health check failures
```bash
python3 -m actifix.main health
sqlite3 data/actifix.db "SELECT timestamp, level, event_type, message FROM event_log ORDER BY timestamp DESC LIMIT 50;"
python3 -m actifix.main logs tail --limit 50
```

## Still stuck?
- Review `docs/DEVELOPMENT.md` for workflow guidance.
- Inspect `logs/` and `.actifix/` for recent activity.
- Capture the failure via Raise_AF before retrying.
