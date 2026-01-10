# Actifix Quickstart

Rapid guide to install Actifix, bootstrap error capture, and view the web interface on macOS, Linux, and Windows (via WSL).

## Prerequisites
- Python 3.10+ with `pip` and `venv`
- Git
- Disk space: ~100MB plus room for logs and tickets
- OS notes:
  - **macOS:** Install Command Line Tools (`xcode-select --install`), optionally `brew install python`.
  - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install -y python3 python3-venv python3-pip git`.
  - **Windows:** Use **WSL2** (Ubuntu recommended), then run the Linux steps inside the WSL shell.

## 5-Minute Setup
1) Clone and enter the repo  
   ```bash
   git clone https://github.com/gmanldn/actifix.git
   cd actifix
   ```
2) (Optional) Create a virtual environment  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows/WSL: source .venv/bin/activate
   ```
3) Install Actifix (and tooling)  
   ```bash
   pip install -e .            # Runtime
   pip install -e ".[dev]"     # + tests, linting
   ```
4) Initialize the workspace (creates `actifix/`, `.actifix/`, `logs/`)  
   ```bash
   python -m actifix.main init
   ```
5) Verify health  
   ```bash
   python -m actifix.main health   # or: actifix-health
   ```

## Bootstrap Error Capture
Minimal snippet to enable capture and generate your first ticket:
```python
import sys
sys.path.insert(0, "src")
import actifix

actifix.bootstrap_actifix_development()  # enables capture + directories

try:
    raise RuntimeError("Demo failure")
except Exception as exc:
    actifix.record_error(
        message=str(exc),
        source="demo.py:10",
        run_label="quickstart",
        error_type=type(exc).__name__,
    )
```
Then check `actifix/ACTIFIX-LIST.md` and `actifix/ACTIFIX.md` for the captured ticket.

## Useful Commands
- `python -m actifix.main record P2 "message" "module.py:42"`: manual ticket.
- `python -m actifix.main process --max-tickets 5`: process pending tickets.
- `python -m actifix.main stats`: ticket counts by status/priority.
- `python -m actifix.main quarantine list|repair`: inspect or repair quarantined items.
- `python -m actifix.main test`: lightweight self-test smoke.

## Web Interface (Static Demo)
The repo ships a CDN-based React page you can serve locally:
```bash
cd actifix-frontend
python3 -m http.server 8080
```
Open http://localhost:8080 to view the dashboard-style demo. No build step is required.

## Directory Layout & Environment
- Defaults: tickets in `actifix/`, state in `.actifix/`, logs in `logs/`.
- Override via env vars: `ACTIFIX_DATA_DIR`, `ACTIFIX_STATE_DIR`, `ACTIFIX_LOGS_DIR`, `ACTIFIX_CAPTURE_ENABLED=1`.
- Generated artifacts: `ACTIFIX-LIST.md` (tickets), `ACTIFIX.md` (rollup), `ACTIFIX-LOG.md` (history), `AFLog.txt` (audit).

## Next Steps
- Integrate into your app by calling `actifix.enable_actifix_capture()` early and `actifix.install_exception_handler()` during development to auto-capture uncaught exceptions.
- Run the full suite when developing the framework itself: `python test.py` and `python test.py --coverage`.
