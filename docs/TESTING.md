# Actifix Testing Guide

Actifix testing is a two-stage flow: system checks via the Actifix test runner and pytest for the full suite. `python3 test.py` is the canonical entry point; it runs the system suite, kicks off pytest, and captures artifactory so you should prefer it to invoking pytest directly. Tests are categorized by markers, not directories.

## Quick commands
```bash
# Full test cycle (system checks + pytest)
python3 test.py --coverage

# Fast coverage (skip slow/integration tests)
python3 test.py --fast-coverage

# Quick pytest pass (pattern filters are forwarded to pytest by the runner)
python3 test.py --pattern "not slow"
```

## Test runner overview
`test.py` orchestrates:
1. System tests via `actifix.testing`.
2. Pytest with optional coverage.
3. Ticket creation for failed system or pytest tests.
4. Stage logs written to `ACTIFIX_STATE_DIR/test_logs` (default `.actifix/test_logs`).

## Coverage expectations
Coverage settings live in `pyproject.toml`:
- Target: 95% minimum (`fail_under = 95`).
- Report: `term-missing` with missing lines.

## Marker-based organization
Markers are defined in `pytest.ini` and enforced with `--strict-markers`.
Common markers:
- `unit`, `integration`, `slow`, `very_slow`
- `db`, `api`, `architecture`, `performance`, `concurrent`

See `docs/TEST_MARKERS_GUIDE.md` for detailed usage.

## Test artifacts
- `ACTIFIX_STATE_DIR/test_logs` (default `.actifix/test_logs`) contains cycle logs, inventories, and stage summaries.
- `ACTIFIX_STATE_DIR/test_logs/pytest_performance_<run_id>.json` captures slow-test timing data.
- `.pytest_results.xml` is generated during `test.py` runs for failure ticketing.

## Recommended workflow
1. Run `python3 test.py --fast-coverage` while iterating (skips `slow`, `very_slow`, `performance`, `db`, `integration`, `concurrent`).
2. Run `python3 test.py --coverage` before commit.
3. Validate architecture if you touched module boundaries:
   ```bash
   python3 test.py --pattern architecture_validation
   ```
