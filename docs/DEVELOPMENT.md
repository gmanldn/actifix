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
- `completion_notes` must include `Implementation:` and `Files:` sections
  - `Implementation:` describes the concrete code changes
  - `Files:` lists the modified file paths (must exist in repo)

Recommended workflow:
```bash
ACTIFIX_CHANGE_ORIGIN=raise_af python3 scripts/interactive_ticket_review.py
```

Programmatic completion:
```python
from actifix.do_af import mark_ticket_complete

mark_ticket_complete(
    ticket_id="ACT-20260118-XXXXX",
    completion_notes=(
        "Implementation: Added guard in raise_af to clamp payload size.\n"
        "Files:\n"
        "- src/actifix/raise_af.py"
    ),
    test_steps="Ran python3 test.py --coverage and manual CLI smoke test.",
    test_results="All tests passed; CLI record/health commands succeed.",
)
```

## Testing and quality gates
Common commands:
```bash
# Full test cycle with Actifix system tests + pytest
python3 test.py

# Coverage cycle (still avoids the heaviest suites unless you ask for --full)
python3 test.py --coverage

# Fast coverage (skip slow/integration tests)
python3 test.py --fast-coverage

# Full pytest suite (includes slow/hanging tests; may take a long time)
python3 test.py --full
```

Other checks:
```bash
python3 -m actifix.main test
python3 -m actifix.main health
python3 test.py --pattern architecture_validation
```

## Doctor command

Actifix includes a `doctor` command to diagnose common environment and configuration issues.
Running this command will:

- Verify that the `ACTIFIX_CHANGE_ORIGIN` environment variable is set to `raise_af`.
- Attempt to load the current Actifix configuration and report any errors.
- Run the builtin health check and print its report.
- Summarise open and completed ticket counts.

Usage:

```bash
python3 -m actifix.main doctor
```

The command exits with code 0 if all checks pass, or 1 if any issues are detected. Use it as a first step when troubleshooting your development environment.

## Module CLI
Use the CLI to list and toggle modules:
```bash
python3 -m actifix.main modules list
python3 -m actifix.main modules disable modules.yahtzee
python3 -m actifix.main modules enable modules.yahtzee
python3 -m actifix.main modules create sample_module --port 8123
```

**Persistence Safety**: Always use `atomic_write()` from `log_utils` for module state persistence. Raw `open/write` risks corruption under crash/load; atomic helpers ensure durability.


## Module testing harness
Use the module testing helpers to spin up blueprints in isolation:
```python
from actifix.testing import create_module_test_client

client = create_module_test_client("yahtzee", url_prefix=None)
assert client.get("/health").status_code == 200
```

## Module configuration
Module defaults and overrides live in `docs/FRAMEWORK_OVERVIEW.md#module-configuration`.
Set overrides via `ACTIFIX_MODULE_CONFIG_OVERRIDES` (JSON).

## Module registration
Runtime API registration uses the helper in `src/actifix/api.py` to enforce
consistent error handling and `/modules/<name>` prefixes. Keep module blueprints
aligned with that prefix to avoid registration failures.

## Module dependency validation
Declare module dependencies in `MODULE_DEPENDENCIES` and ensure every edge exists
in `docs/architecture/DEPGRAPH.json`. Startup will block modules with invalid edges
and record an error ticket.

## Architecture updates
If you add or move modules:
1. Update `docs/architecture/MAP.yaml` and `docs/architecture/DEPGRAPH.json`.
2. Sync `docs/architecture/MODULES.md`.
3. Update `docs/INDEX.md` references.

## Module status persistence
Module enable/disable state lives in `.actifix/module_statuses.json` using a versioned schema:
```json
{
  "schema_version": "module-statuses.v1",
  "statuses": {
    "active": ["runtime.api"],
    "disabled": ["modules.superquiz"],
    "error": []
  }
}
```
Writes must go through `atomic_write()` and the system will back up malformed JSON to
`module_statuses.corrupt.json` before restoring defaults.

## Module execution context
Module execution should use a sanitized environment via `actifix.modules.get_module_context()`.
Only allowlisted keys (plus `LC_`/`XDG_` prefixes) are exposed and sensitive names are excluded.
Values are also redacted with `redact_secrets_from_text()` to avoid leaking secrets into tickets.

## Frontend bundle builds
`scripts/start.py` now invokes `scripts.build_frontend.build_frontend()` so the
`actifix-frontend` sources are recopied into `actifix-frontend/dist/` every time the
launcher runs. This ensures the Azure-style dashboard assets stay up-to-date before
the API server and static host start; the built bundle is gitignored.

## Documentation workflow
- Use `docs/FRAMEWORK_OVERVIEW.md` for release notes and feature narratives.
- Update `docs/INDEX.md` any time sections move.
- Avoid new standalone documentation files; merge into existing guides.

## High-value backlog planning

The high-value idea queue currently holds P0 tickets such as `ACT-20260125-F0EA2` (saved filters/views), `ACT-20260125-AAD9E` (quick ticket/module search), `ACT-20260125-AA866` (recent activity feed), `ACT-20260125-2DD93` (severity badges and SLA timers), and several module SDK/experience requests (performance budgets, upgrade checklists, validators, testing examples, and scaffolding guidance). Treat this stream as an established backlog:

1. **Capture clarity** – For each HV ticket, record the intended behavior via `actifix.record_error(...)` (Raise_AF) if you need additional context, referencing the existing idea ID and describing any probing you've done.
2. **Break it down** – Draft a short spec in an existing doc (e.g., `docs/FRAMEWORK_OVERVIEW.md#module-configuration` or the relevant section of this guide) explaining how the feature interacts with the module/UI/AI surfaces, the data flow, and the required validations.
3. **Plan outcomes** – Identify the code paths, tests, and documentation updates needed for each piece so that DoAF can close its completion gates without manual intervention. Link those efforts back to the HV ticket in the completion notes and include the involved files (per the completion gating rules above).
4. **Track progress** – Update this section or the relevant doc when you convert an HV idea into concrete commits so agents and humans can see what is next in the queue without scanning the entire ticket list.

This approach keeps the priority lane lean, ensures every HV improvement has traceable requirements, and lets DoAF/agents focus on implementing rather than guessing what belongs in `Files:` or `Implementation:`.

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

### Ticket agent daemon
To run the background ticket agent under launchctl, include `--ticket-agent`
in the launcher arguments (and optionally `--ticket-agent-no-ai` or
`--ticket-agent-fallback-complete`).

## Background ticket agent status
Background ticket processing is available via the DoAF agent loop, but it is not enabled by default:

```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.do_af agent --idle-sleep 5 --idle-backoff-max 60 --renew-interval 300
```

Non-interactive fallback completion (no AI) can be enabled explicitly:

```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.do_af agent --no-ai --fallback-complete
```

The remaining readiness work is tracked in:

- `ACT-20260125-FD74D` - Background ticket agent loop with lease renewals, idle backoff, and clean shutdown. (completed)
- `ACT-20260125-FF6CC` - Non-interactive processing policy with deterministic fallback when AI is unavailable. (completed)
- `ACT-20260125-35DCB` - AgentVoice instrumentation for DoAF acquisition, dispatch, completion, and failures. (completed)
- `ACT-20260125-B760C` - Health/monitoring for agent liveness, last-run time, and backlog lag. (completed)
- `ACT-20260125-2FC6E` - Managed daemon/launcher support for the ticket agent with logs and restart policy. (completed)
- `ACT-20260125-71BDF` - Tests covering background processing, lease renewal, fallback, and AgentVoice logging.

## Commit and push
Commit format:
```bash
git commit -m "docs(workflow): refresh development and testing guides"
```
Always push after each ticket is complete.
Version guard: pre-commit and Do_AF enforce that `pyproject.toml` cannot be below `origin/develop`.
If the remote version is higher, the guard rewrites `pyproject.toml` to the remote version,
bumps the patch, and re-syncs frontend assets before allowing commit/push.
