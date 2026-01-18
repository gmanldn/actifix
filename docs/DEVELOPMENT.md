# Actifix Development Guide

Actifix follows a quality-first workflow: architecture compliance, deterministic testing, and traceable tickets. Every change must honor the Raise_AF gate and keep documentation accurate.

## Core rules
1. **Raise_AF gate**: set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or editing files.
2. **Architecture awareness**: review `docs/architecture/MAP.yaml` and `docs/architecture/DEPGRAPH.json` before structural changes.
3. **Documentation discipline**: update `docs/INDEX.md` and relevant guides alongside changes.
4. **Error capture**: log errors with `actifix.raise_af.record_error(...)` and re-raise when appropriate.
5. **Commit hygiene**: bump `pyproject.toml` version after every commit.

## Setup and start
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m pip install -e "[dev]"
python3 scripts/start.py
```

## Multi-Agent Development
For collaborative AI agent workflows, use isolated environments to avoid conflicts:

```bash
# Setup new agent (creates isolated data/logs/state)
scripts/setup-agent.sh

# Source agent config
source ~/actifix-agent-*/agent.env  # Path printed by script

# Now process tickets in isolation
python3 scripts/view_tickets.py
python3 Do_AF.py 1
```

Each agent gets unique `ACTIFIX_DATA_DIR`, keeping `data/actifix.db` untracked in git.

## Start work with Raise_AF
```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.main record DocChange "starting work" "docs/DEVELOPMENT.md:1" --priority P3
```

## Ticket completion quality gate
Tickets cannot be marked complete without evidence. Required fields:
- `completion_notes`: min 20 characters (what was done)
- `test_steps`: min 10 characters (how it was tested)
- `test_results`: min 10 characters (test evidence)

Recommended workflow:
```bash
ACTIFIX_CHANGE_ORIGIN=raise_af python3 scripts/interactive_ticket_review.py
```

Programmatic completion:
```python
from actifix.do_af import mark_ticket_complete

mark_ticket_complete(
    ticket_id="ACT-20260118-XXXXX",
    completion_notes="Added guard in raise_af to clamp payload size.",
    test_steps="Ran python3 test.py --coverage and manual CLI smoke test.",
    test_results="All tests passed; CLI record/health commands succeed.",
)
```

## Testing and quality gates
Common commands:
```bash
# Full test cycle with Actifix system tests + pytest
python3 test.py --coverage

# Fast coverage (skip slow tests)
python3 test.py --fast-coverage

# Quick pytest run
python3 -m pytest test/ -m "not slow"
```

Other checks:
```bash
python3 -m actifix.main test
python3 -m actifix.main health
python3 -m pytest test/test_architecture_validation.py -v
```

## Architecture updates
If you add or move modules:
1. Update `docs/architecture/MAP.yaml` and `docs/architecture/DEPGRAPH.json`.
2. Sync `docs/architecture/MODULES.md`.
3. Update `docs/INDEX.md` references.

## Documentation workflow
- Use `docs/FRAMEWORK_OVERVIEW.md` for release notes and feature narratives.
- Update `docs/INDEX.md` any time sections move.
- Avoid new standalone documentation files; merge into existing guides.

## Daemon Mode (macOS)
To run Actifix persistently as a user daemon (auto-start on login, auto-restart if crashed):

1. **Load daemon**:
   ```bash
   launchctl load ~/Library/LaunchAgents/actifix.plist
   ```

2. **Unload daemon**:
   ```bash
   launchctl unload ~/Library/LaunchAgents/actifix.plist
   ```

**Logs**: `logs/actifix.out.log` (stdout), `logs/actifix.err.log` (stderr)

**Notes**:
- Runs `scripts/start.py` with API watchdog (auto-restarts if port 5001 down).
- Uses project venv PATH.
- `KeepAlive: true` ensures restart on crash/exit.

## Commit and push
Commit format:
```bash
git commit -m "docs(workflow): refresh development and testing guides"
```
Always push after each ticket is complete.