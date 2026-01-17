# Actifix Development Guide

Actifix follows a quality-first workflow: architecture compliance, deterministic tests, and traceable errors. Every change must honor the Raise_AF gate, keep documentation current, and leave a clear audit trail.

## Core principles
1. **Architecture compliance** – Respect `docs/architecture/MAP.yaml` + `DEPGRAPH.json` before importing across modules.
2. **Quality gates** – Run testing, formatting, linting, type checking, and architecture validation before committing.
3. **Documentation-first** – Update `docs/FRAMEWORK_OVERVIEW.md`, `docs/INDEX.md`, and affected architecture files together with code changes.
4. **Fail-fast & traceable** – Capture every exception through `actifix.raise_af` with correlation-aware logging.

## Setup & workflow
```bash
git clone https://github.com/gmanldn/actifix.git
cd actifix
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -e "[dev]"  # optional tooling
python scripts/start.py  # enforces ACTIFIX_CHANGE_ORIGIN=raise_af
```
Run Raise_AF before edits:
```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python -m actifix.main record P3 "starting work" "your_module.py:10"
```

## Quality gates checklist
- `python -m pytest test/ --cov=src/actifix --cov-report=term-missing`
- `black --check src/ test/`
- `isort --check-only src/ test/`
- `mypy src/actifix/`
- `python -m actifix.testing --validate-architecture`
- `python -m actifix.health --comprehensive`

Slow tests default to a 10s timeout; use `--runslow` to include hanging suites and review the slow-test tracker for regressions.

## Testing & architecture
- Tests must be deterministic, clean up after themselves, and include both positive and negative paths.
- Groupings: `test/unit/`, `test/integration/`, `test/architecture/`, fixtures in `test/fixtures/`.
- Use `tooling.testing` rules to keep QA aligned with architecture contracts.

## Coding standards
- Always use typed signatures with docstrings.
- Log through `actifix.log_utils` with correlation IDs; wrap logical operations inside correlation contexts.
- Errors must flow through `actifix.raise_af.record_error(...)` and be re-raised if the caller needs to fail.

## Documentation workflow
1. Plan new sections inside `docs/FRAMEWORK_OVERVIEW.md` (release notes, new features, migration notes).
2. Update `docs/INDEX.md` with any new entries or references.
3. Reflect architecture changes in `docs/architecture/MAP.yaml`, `DEPGRAPH.json`, and `MODULES.md`.
4. Document examples in relevant guides (Quickstart for setup, README for overview, Monitoring/Troubleshooting for operations).

## Release and delivery
1. Increment `pyproject.toml` version for every release.
2. Document releases in `docs/FRAMEWORK_OVERVIEW.md` (Release Notes & Version History section).
3. Keep `CHANGELOG.md` for historical references.
4. Commit with conventional format (e.g., `feat(core): ...`) and push after every ticket.
5. Tag releases after all quality gates pass.

## Monitoring & security
- Capture sensitive data with secret redaction and never log raw credentials.
- Keep bootstrap latency under 5 seconds; error capture should stay <100ms.
- Track health via `python -m actifix.health --status` and component checks for logging/quarantine/state.

## Documentation standards reminder
- No new standalone `.md` tasks—blend content into existing docs.
- Use `docs/FRAMEWORK_OVERVIEW.md` for roadmap, release notes, and feature narratives.
- Update architecture maps and cross references whenever structure changes.
- Maintain the Raise_AF requirement: log any blockers through `actifix.raise_af.record_error(...)` before skipping rules.