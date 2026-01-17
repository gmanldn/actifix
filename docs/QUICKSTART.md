# Actifix Quickstart

> **The Self-Improving Error Management Framework** 🚀

## What is ACTIFIX?

ACTIFIX is a sophisticated error tracking and management framework that can **track and improve itself**. Unlike traditional error logging systems, ACTIFIX is designed from the ground up for AI-assisted development, comprehensive context capture, and production-grade reliability.

### 🎯 Feature Highlights
- **Error intelligence:** Rich captures (stack, file snippets, system state), auto-priority (P0–P4), duplicate guards, remediation notes.
- **AI-native:** Produces consistent, compact tickets ready for Claude, GPT, or any LLM to propose fixes.
- **Self-development:** Bootstrap once and ACTIFIX will open tickets against its own codebase as you work.
- **Reliability & safety:** Atomic writes, fallback queues, secret redaction, and health checks to avoid silent failures.
- **Human-readable artifacts:** SQLite ticket database (`data/actifix.db`), rollup views (`v_recent_tickets`, `v_ticket_history`), and audit events (`event_log`).

### 💡 Why Choose ACTIFIX?

**For Development Teams:**
- Replace scattered error logs with organized, prioritized tickets.
- Get AI-ready error descriptions for faster debugging.
- Track development progress and regression prevention.

**For Production Systems:**
- Capture critical errors with enough context for immediate action.
- Automatically classify severity for proper escalation.
- Maintain audit trails for compliance and post-mortems.

**For AI-Assisted Development:**
- Generate comprehensive context for AI debugging sessions.
- Enable AI assistants to suggest specific fixes with full error context.
- Create self-improving systems that track their own enhancement tickets.

### 🔄 The Self-Improvement Advantage

What makes ACTIFIX unique is its ability to **improve itself**:

```python
# ACTIFIX tracking its own development
import actifix
actifix.bootstrap_actifix_development()

# Now when ACTIFIX encounters a bug in its own code,
# it automatically creates a ticket to fix itself!
```

This creates a continuous improvement loop where the framework gets better over time by tracking and fixing its own issues.

### 🛠️ Real-World Use Cases

**1. Production Error Monitoring**
```python
# In your production application
import actifix
actifix.enable_actifix_capture()

# Automatically capture API failures
try:
    response = api_client.fetch_user_data(user_id)
except APIException as e:
    actifix.record_error(
        message=f"API failure: {e}",
        source=f"{__file__}:{sys._getframe().f_lineno}",
        run_label="production-api",
        error_type="APIException",
        priority=actifix.TicketPriority.P1  # High priority for production
    )
```

**2. Development Bug Tracking**
```python
# During development - ACTIFIX tracks its own issues!
import actifix
actifix.bootstrap_actifix_development()

# Any bugs in your development code get automatically captured
def experimental_feature():
    # If this crashes, ACTIFIX creates a ticket automatically
    return risky_new_algorithm()
```

**3. AI-Assisted Debugging**
```python
# Generate rich context for AI assistants
try:
    complex_data_processing()
except Exception as e:
    ticket = actifix.record_error(
        message=str(e),
        source="data_processor.py:157",
        run_label="ml-pipeline",
        capture_context=True  # Includes file snippets and system state
    )
    
    # The ticket now contains everything an AI needs to suggest a fix!
    print(f"Ticket {ticket.entry_id} ready for AI analysis")
```

**4. Team Collaboration**
```python
# Track progress and share context with your team
actifix.track_development_progress(
    "Database migration completed",
    "Successfully migrated 1M+ user records to new schema. "
    "Performance improved by 40%. Ready for production deployment."
)
```

### 📊 What You Get

After setup, ACTIFIX emits structured data in these locations:

- **`data/actifix.db`** - SQLite `tickets` table (priority, status, metadata, context, AI notes); this is the only writable registry.
- **`v_recent_tickets`** - Read-only rollup of the last 20 errors (derived from the database for quick audits).
- **`v_ticket_history`** - Generated completion log (chronological history from the DB).
- **`event_log`** - Lifecycle audit trail (read-only diagnostic stream sourced from the ticket table).

> **Tasking reminder:** `data/actifix.db` is the canonical source of truth for tasks. The repository no longer ships with `TASK_LIST.md`, `Actifix-list.md`, or any other writable Markdown task list—the migration to a database-first workflow is complete. Use `actifix.raise_af`, DoAF, the REST API, or direct SQL queries against `data/actifix.db` to create, view, and complete tickets, and treat the DB views as the read-only rollups.

Each ticket includes:
- 🆔 Unique ID (e.g., `ACT-20261001-ABC123`)
- 🎯 Auto-assigned priority (P0-P4) 
- 📍 Precise source location
- 🕐 Creation timestamp
- 🔍 Stack trace preview
- 🤖 AI remediation notes
- ✅ Progress checklist (Documented → Functioning → Tested → Completed)

---

## Quick Setup Guide

Rapid guide to install ACTIFIX, bootstrap error capture, and view the web interface on macOS, Linux, and Windows (via WSL).

## Prerequisites
- Python 3.10+ with `pip` and `venv`
- Git
- Disk space: ~100MB plus room for logs and tickets
- OS notes:
  - **macOS:** Install Command Line Tools (`xcode-select --install`), then `brew install python git` for the latest runtimes.
  - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install -y python3 python3-venv python3-pip git`.
  - **Windows:** Use **WSL2** (Ubuntu recommended). Install WSL from the Microsoft Store, reboot, open the Ubuntu shell, then follow the Linux steps.

## Platform Setup Cheat-Sheet
- **macOS:**  
  ```bash
  xcode-select --install             # if not already installed
  brew install python git            # installs python3/pip3
  git clone https://github.com/gmanldn/actifix.git
  cd actifix
  python3 -m venv .venv && source .venv/bin/activate
  pip install -e . && pip install -e ".[dev]"
  ```
- **Linux (Ubuntu/Debian):**  
  ```bash
  sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
  git clone https://github.com/gmanldn/actifix.git
  cd actifix
  python3 -m venv .venv && source .venv/bin/activate
  pip install -e . && pip install -e ".[dev]"
  ```
- **Windows via WSL2:**  
  1) Install WSL2 + Ubuntu.  
  2) Open Ubuntu shell and run the Linux commands above.  
  3) To serve the dashboard to Windows, access via `http://localhost:8080` (WSL forwards to Windows).

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
Then use `sqlite3 data/actifix.db "SELECT id, priority, status, message FROM tickets ORDER BY created_at DESC LIMIT 5;"` and `sqlite3 data/actifix.db "SELECT * FROM v_recent_tickets;"` to inspect the capture.

## Task Registry
`data/actifix.db` is the **single authoritative registry** for Actifix tasks. Always create tickets via `actifix.record_error(...)`, `DoAF`, or the CLI—the database is the only writeable source of truth. Legacy Markdown task lists were retired long ago and no longer exist in this workspace.

## Useful Commands
- `python -m actifix.main record P2 "message" "module.py:42"`: manual ticket.
- `python -m actifix.main process --max-tickets 5`: process pending tickets.
- `python -m actifix.main stats`: ticket counts by status/priority.
- `python -m actifix.main quarantine list|repair`: inspect or repair quarantined items.
- `python -m actifix.main test`: lightweight self-test smoke.

## Web Interface (Actifix Dashboard)
The repo ships a CDN-based React dashboard you can serve locally:
```bash
cd actifix-frontend
python3 -m http.server 8080
```
Open http://localhost:8080 to view the Actifix dashboard. No build step is required.

## Directory Layout & Environment
- Defaults: tickets in `data/actifix.db`, data dir in `actifix/`, state in `.actifix/`, logs in `logs/`.
- Override via env vars: `ACTIFIX_DATA_DIR`, `ACTIFIX_STATE_DIR`, `ACTIFIX_LOGS_DIR`, `ACTIFIX_CAPTURE_ENABLED=1`.
- Generated artifacts: `data/actifix.db` (tickets), `v_recent_tickets` (rollup), `v_ticket_history` (history), `event_log` (audit).

## Next Steps
- Integrate into your app by calling `actifix.enable_actifix_capture()` early and `actifix.install_exception_handler()` during development to auto-capture uncaught exceptions.
- Run the full suite when developing the framework itself: `python test/test_runner.py` and `python test/test_runner.py --coverage`.
