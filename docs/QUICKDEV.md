# Actifix QUICKDEV Guide

Focused instructions for AI agents and developers to build and ship Actifix add-on modules quickly. The goal: create well-documented, centrally managed microservice-style modules that plug into the existing runtime, health, and testing systems.

## What Makes a Module “Actifix-Ready”
- **Single entrypoint**: Each module exposes a clear entry file under `src/actifix/<name>.py` (or a package with `__init__.py`), referenced in `arch/MAP.yaml` and `arch/MODULES.md`.
- **Defined contract**: Document purpose, inputs/outputs, and dependencies. Keep contracts small and explicit.
- **Central observability**: Use `pokertool.master_logging.get_logger` (via `src/actifix/log_utils.py`) and emit structured events; never create custom log files.
- **Health and status**: Surface health signals via `get_health` or module-specific probes so the dashboard can show live status.
- **Error routing through ACTIFIX**: Capture and report issues with `raise_af.record_error`—never bypass the ACTIFIX pipeline.
- **Microservice mindset**: Treat each module as an independently testable unit with narrow APIs and no global state leakage.

## Blueprint for a New Module
1) **Name and domain**  
   - Pick a concise name (e.g., `alerts`, `ingest`, `scheduler`).  
   - Decide the domain (`runtime`, `infra`, `core`, or `tooling`) and owner for architecture docs.

2) **Entrypoint scaffold**  
   - Create `src/actifix/<module>.py` (or a package).  
   - Import logging via `from pokertool.master_logging import get_logger` (or `from actifix.log_utils import get_logger` depending on existing patterns).  
   - Add a `bootstrap()` or `run()` function that is side-effect free on import.

3) **API shape**  
   - Keep public functions pure where possible; isolate I/O in thin adapters.  
   - Accept explicit paths/state via `state_paths.get_actifix_paths()` instead of hardcoding directories.  
   - If exposing HTTP, register routes in `src/actifix/api.py` and prefix with `/api/<module>`; return JSON only.

4) **Contracts and dependencies**  
   - Declare contracts in code docstrings and mirror them in architecture docs (see “Register the module” below).  
   - Depend only on required subsystems (`infra.logging`, `infra.health`, `core.raise_af`, etc.); avoid circular deps.

5) **Health & metrics hooks**  
   - Provide `get_health(paths)` that returns status, warnings, and metrics relevant to the module.  
   - Emit structured events to logs for the dashboard blades to consume.

6) **Testing**  
   - Add pytest cases under `test/` using `test_<module>.py`.  
   - Use fixtures to isolate filesystem interactions (tmp dirs) and validate error handling through ACTIFIX.

## Fast Path: Building a Microservice-Style Add-On
1) **Scaffold**  
   ```bash
   touch src/actifix/<module>.py
   touch test/test_<module>.py
   ```
   Add a `bootstrap()` that wires dependencies but defers execution until called.

2) **Register the module**  
   - Update architecture docs (generated from `arch/MAP.yaml` / `arch/MODULES.md`) with the new entrypoint and contracts.  
   - Keep `modules` entries consistent: `id`, `domain`, `entrypoints`, `depends_on`, `contracts`.

3) **Expose API (optional)**  
   - In `src/actifix/api.py`, add a route that calls your module functions.  
   - Ensure CORS and JSON responses are handled via the shared Flask app.  
   - Keep routes thin; business logic stays inside the module.

4) **Wire health signals**  
   - Extend `get_health` or add a module-specific check callable from the API and dashboard.  
   - Return clear statuses: `OK`, `WARNING`, `ERROR`, `SLA_BREACH`.

5) **Capture errors through ACTIFIX**  
   - Wrap risky calls with `record_error(...)` providing `message`, `source`, `run_label`, and `error_type`.  
   - Avoid custom exception sinks; the ACTIFIX pipeline handles tickets and deduplication.

6) **Test and validate**  
   - Run `python test.py` and `python test.py --coverage` (target 95%+).  
   - Verify architecture compliance tests still pass (entrypoints present, docs fresh).

7) **Ship**  
   - Bump version in `pyproject.toml`.  
   - Commit with conventional message (`feat(<module>)`, `docs(<module>)`, etc.) and push to `develop`.

## Patterns for Clean Modules
- **Pure cores, thin edges**: keep core logic pure; confine filesystem, network, and API edges to adapters.  
- **State injection**: pass `paths = get_actifix_paths(project_root=...)` instead of reading env/global paths.  
- **Idempotent operations**: design for retries; use the persistence queue utilities when writing to disk.  
- **Observability first**: log correlation IDs and outcomes; surface summaries to the dashboard blades.  
- **No silent failures**: every caught exception that matters should raise an ACTIFIX ticket.

## Example Skeleton (Python)
```python
# src/actifix/alerts.py
from pokertool.master_logging import get_logger
from actifix.state_paths import get_actifix_paths
from actifix.raise_af import record_error

logger = get_logger(__name__)

def bootstrap(project_root=None):
    paths = get_actifix_paths(project_root=project_root)
    logger.info("alerts bootstrap started", extra={"paths": paths.as_dict()})
    return paths

def enqueue_alert(paths, payload):
    try:
        # core logic here (pure if possible)
        logger.info("alert queued", extra={"priority": payload.get("priority", "P2")})
    except Exception as exc:
        record_error(
            message=str(exc),
            source="alerts.py:enqueue_alert",
            run_label="alerts",
            error_type=type(exc).__name__,
        )
        raise
```

## Central Management Checklist
- Registered in `arch/MAP.yaml` and `arch/MODULES.md` with accurate entrypoints.
- Routes (if any) live in `src/actifix/api.py` and are JSON-only.
- Health signals emitted and visible on the dashboard.
- Logging goes through the shared logger; no new log files.
- Errors flow through ACTIFIX ticketing.
- Tests cover happy paths, error paths, and persistence/queue interactions where relevant.

Use this guide to keep modules elegant, observable, and fast to ship while remaining fully governed by the Actifix platform.

## Simple Ticket Attack

Use the simple ticket attack helper when you need a controlled backlog of simple issues to drive automation or DoAF experiments. The helper iterates through `record_error(...)` with 200 lightweight descriptions so every ticket goes through the Actifix method (duplicate guards, AI notes, and atomic writes).

```bash
ACTIFIX_CHANGE_ORIGIN=raise_af ACTIFIX_CAPTURE_ENABLED=1 python -m actifix.simple_ticket_attack
```

Options:
- `--count`: total tickets to create (default 200)
- `--start-index`: begin numbering at a different offset
- `--priority`: set P0–P3 for the entire batch
- `--run-label`: override the run label recorded in the tickets
- `--capture-context`: include file/system context in each ticket
- `--dry-run`: preview the messages without writing files

Run this whenever you want to "attack" a backlog of simple tickets while keeping the canonical Actifix workflow in charge (no manual edits to `ACTIFIX-LIST.md`).
