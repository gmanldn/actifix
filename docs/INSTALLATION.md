# Actifix Installation Guide

Actifix is a self-improving error management framework with a database-first ticket store. This guide covers installation, configuration, and initial verification.

## Requirements
- Python 3.10+
- Git
- macOS, Linux, or WSL on Windows
- Disk: 100MB+ plus space for logs and tickets

## Install from source (recommended)
```bash
git clone https://github.com/gmanldn/actifix.git
cd actifix
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m pip install -e "[dev]"  # optional tooling
python3 -m pip install -e "[web]"  # optional Flask dashboard
```

## Install from PyPI (when available)
```bash
python3 -m pip install actifix
```

## Initialize Actifix
```bash
# Creates .actifix/, data/, and logs/ if missing
python3 -m actifix.main init
```

## Verify installation
```bash
python3 -m actifix.main health
python3 -m actifix.main stats
```

## Configuration model
Actifix reads configuration from environment variables and optional programmatic overrides via `load_config()`. There is no standalone CLI for config generation.

### Core environment variables
- `ACTIFIX_CHANGE_ORIGIN=raise_af` (required before running Actifix or making changes)
- `ACTIFIX_CAPTURE_ENABLED=1` to enable capture
- `ACTIFIX_PROJECT_ROOT` to override project root detection
- `ACTIFIX_DATA_DIR`, `ACTIFIX_STATE_DIR`, `ACTIFIX_LOGS_DIR` for custom paths

### Capture tuning
- `ACTIFIX_FILE_CONTEXT_MAX_CHARS` (default 2000)
- `ACTIFIX_SYSTEM_STATE_MAX_CHARS` (default 1500)
- `ACTIFIX_AI_REMEDIATION_MAX_CHARS` (default 2000)
- `ACTIFIX_CONTEXT_TRUNCATION_CHARS` (default 4096)

### Ticket and throttling limits
- `ACTIFIX_MAX_MESSAGE_LENGTH` (default 5000)
- `ACTIFIX_MAX_FILE_CONTEXT_BYTES` (default 1048576)
- `ACTIFIX_MAX_OPEN_TICKETS` (default 10000)
- `ACTIFIX_TICKET_THROTTLING_ENABLED` (default true)
- `ACTIFIX_MAX_P2_TICKETS_PER_HOUR`, `ACTIFIX_MAX_P3_TICKETS_PER_4H`, `ACTIFIX_MAX_P4_TICKETS_PER_DAY`

### Testing defaults
- `ACTIFIX_FAST_COVERAGE=1` to use fast coverage in `test.py --coverage`
- `ACTIFIX_DISABLE_XDIST=1` to disable pytest-xdist
- `ACTIFIX_XDIST_WORKERS=<N>` to set worker count

## Directory layout
```
actifix/
├── src/actifix/        # Core library
├── data/actifix.db     # Canonical ticket store
├── .actifix/           # Internal state, fallback queue
├── logs/               # Optional runtime logs
├── docs/               # Documentation
├── test/               # Test suite
└── actifix-frontend/   # Static dashboard assets
```

## Integration snippet
```python
from actifix.raise_af import record_error

try:
    risky_operation()
except Exception as exc:
    record_error(
        message=str(exc),
        source="app.py:42",
        run_label="production",
        error_type=type(exc).__name__,
    )
    raise
```

## Troubleshooting
If you hit issues during setup, start with `docs/TROUBLESHOOTING.md`.
