# Actifix Framework Overview

Actifix is a self‑improving error management system that captures prioritized, AI‑ready tickets, enforces architectural quality, and can even monitor its own development lifecycle.

## Quick highlights
- **Capture**: `enable_actifix_capture()` records stack traces, file snippets, system state, and remediation notes alongside automatic P0–P4 classification.
- **Self-development**: `bootstrap_actifix_development()` makes the framework ticket its own regressions so the repo improves with every commit.
- **Resilience**: Atomic writes, fallback queues, centralized logging, and `data/actifix.db` as the canonical ticket store keep the system recoverable.
- **AI-native**: Tickets are normalized for Claude, GPT, Ollama, and other copilots with contextual payloads tuned for large windows.

## Getting started
```bash
git clone https://github.com/gmanldn/actifix.git
cd actifix
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -e "[dev]"  # optional
python scripts/start.py            # enforces ACTIFIX_CHANGE_ORIGIN=raise_af while watching pyproject.toml
python -m actifix.main health
```

Enable capture:
```python
import actifix
actifix.enable_actifix_capture()
```
Record an error with context (stack, files, system state):
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
import actifix
actifix.bootstrap_actifix_development()
actifix.track_development_progress("Feature complete", "AI telemetry integrated")
```

## Architecture primer
- **RaiseAF (`src/actifix/raise_af.py`)** captures errors, prevents duplicates, and produces remediation notes.
- **State paths (`src/actifix/state_paths.py`)** centralize data/state/log locations (respect `ACTIFIX_DATA_DIR`, `ACTIFIX_STATE_DIR`).
- **Bootstrap (`src/actifix/bootstrap.py`)** wires self-development, installs exception handlers, and seeds the initial ticket state.

Refer to `docs/architecture/MAP.yaml`, `architecture/MODULES.md`, and `architecture/DEPGRAPH.json` for the canonical module graph; all changes must be reflected there.

## Release notes snapshot
| Version | Highlights |
|---------|------------|
| **3.3.2** (2026-01-17) | Stability release—10s pytest timeout, `--runslow` guard, slow-test tracker, developer loop reliability improvements.<br>Documented validations in `docs/DEVELOPMENT.md`. |
| **2.7.0** (2026-01-11) | Production-ready AI stack: multi-provider AI client, database persistence with ticket repository, migrations, health monitoring, quarantine, architecture compliance tooling. |
| **2.6.0** (2026-01-10) | Self-improving framework launch: AI-native tickets, self-development bootstrapping, CLI, transparent docs, environment tuning, web dashboard. |
| **2.5.0** and earlier | Foundation: basic capture, persistence, CLI, and tests. |

## Migration notes
- Tickets live exclusively in `data/actifix.db`; legacy Markdown task files were retired some time ago.
- Upgrading to 2.7.x requires ensuring AI provider configs and new environment variables are tuned (see README for env var references).

## Roadmap
1. **Ticket processing** – DoAF engine, validation framework, AI context builders.
2. **Advanced ops** – Monitoring, circuit breakers, retries, notifications, telemetry.
3. **AI integrations** – Claude/OpenAI/Ollama support, custom provider interfaces, automatic fix suggestions.

## Contribution checklist
1. Enable self-development mode so Actifix tickets its own regressions.
2. Run Raise_AF gates (`ACTIFIX_CHANGE_ORIGIN=raise_af`, `actifix.raise_af.record_error(...)`) before code changes.
3. Capture issues via Raise_AF/DoAF/CLI and mark them complete in `data/actifix.db`.
4. Update this document (release notes, architecture summary) and `docs/INDEX.md` for every change.
5. Maintain the architecture map (`docs/architecture/MAP.yaml` + `DEPGRAPH.json`).

## License & credits
Actifix is inspired by the Pokertool system and generalized for universal use. See `LICENSE` for terms.