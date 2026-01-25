# Actifix Framework Overview

Actifix is a self-improving error management system that captures prioritized tickets, preserves operational context, and keeps the development workflow auditable. It is stdlib-first, resilient under failure, and designed to feed AI copilots with consistent context.

## What Actifix provides

**Dashboard Panes**:
- =Ê **Overview**: Health metrics, recent tickets, system stats
- <« **Tickets**: Priority lanes (P0-P4), ticket details modal
- =Ü **Logs**: Live structured logs with filtering
- ™ **System**: Resources, paths, git status, recent events
- >é **Modules**: System/user modules with toggle controls
- =¡ **Ideas**: Submit requests ’ AI generates actionable tickets
- =' **Settings**: AI provider config, status, feedback log

- Structured error capture with priority classification (P0-P4).
- Deduplication via duplicate guards and ticket repository checks.
- Context capture (stack traces, file snippets, system state) with configurable limits.
- Durable persistence backed by `data/actifix.db`, with fallback queue support.
- Self-development mode to keep regressions visible during work.
- Module error logs redact secrets before ticket persistence.
- Module blueprints register in a sandbox; failures mark module status as error.
- Module endpoints support access rules: public, local-only, auth-required.
- Module endpoints are rate limited per module (default 60/min, 600/hour, 2000/day).

## Architecture primer
Core modules and their roles:
- **bootstrap**: system initialization and development tracking (`src/actifix/bootstrap.py`).
- **raise_af**: error capture and ticket creation (`src/actifix/raise_af.py`).
- **do_af**: ticket processing and remediation (`src/actifix/do_af.py`).
- **persistence**: SQLite-backed ticket repository, atomic writes, queues.
- **health**: system health checks and status reporting.

Canonical architecture references:
- `docs/architecture/MAP.yaml`
- `docs/architecture/DEPGRAPH.json`
- `docs/architecture/MODULES.md`

## Multi-Agent Development Workflow

Actifix supports multiple AI agents working **directly on `develop`** simultaneously (no per-change branches required):

- **Isolated State**: Database (`data/actifix.db`), logs, state untracked in `.gitignore`. Use `scripts/setup-agent.sh` for unique `ACTIFIX_DATA_DIR` per agent.
- **No Branches**: Work/push directly to `develop`. Sync via `git pull` before starting.
- **Merge Strategy**: Conventional commits after each ticket. Pre-commit rejects binaries; GitHub Actions enforces tests.
- **Naming**: Ticket-based commit messages: `type(scope): description (TICKET-ID)`.
- **Coordination**: View shared priorities via `python3 scripts/view_tickets.py`. Process highest-P first.

Agents stay in sync through git; local isolation prevents data conflicts.

## Module metadata and permissions
Each module should expose `MODULE_METADATA` with capability hints and permission declarations.
Required keys:
- `name`, `version`, `description`
- `capabilities` (dict)
- `data_access` (dict)
- `network` (dict)
- `permissions` (list of permission names from `plugins.permissions.PermissionRegistry`)

Example:
```json
{
  "name": "modules.yhatzee",
  "version": "1.0.0",
  "description": "Two-player Yhatzee module with local GUI.",
  "capabilities": {"gui": true, "health": true},
  "data_access": {"state_dir": true},
  "network": {"external_requests": false},
  "permissions": ["logging", "fs_read"]
}
```

## Module lifecycle and helpers

Actifix now ships with a shared `ModuleBase` helper for any GUI module. It merges
`MODULE_DEFAULTS` with `ACTIFIX_MODULE_CONFIG_OVERRIDES`, keeps sanitized
Actifix paths handy, exposes a default health response, and centralizes `log_event` +
`record_error` calls so every module records errors with a consistent run label
(e.g., `superquiz-gui`).

The API also walks every `modules.*` node declared in `docs/architecture/DEPGRAPH.json`
via `ModuleRegistry`. The registry lazy-imports `actifix.modules.<name>`, persists
enable/disable/error states inside `.actifix/module_statuses.json` (atomic writes,
`module-statuses.v1` schema), and enforces lifecycle hooks (`module_register`,
`module_unregister`). Disabled modules are skipped during startup and the registry
drives the same state file that `python3 -m actifix.main modules enable/disable`
updates so the CLI, launcher, and tests all read from one source of truth.

## Module configuration
Module defaults come from Actifix config with optional overrides via `ACTIFIX_MODULE_CONFIG_OVERRIDES`.

| Module | Default host | Default port | Override key |
|--------|--------------|--------------|--------------|
| shootymcshoot | 127.0.0.1 | 8040 | shootymcshoot |
| yhatzee | 127.0.0.1 | 8090 | yhatzee |
| superquiz | 127.0.0.1 | 8070 | superquiz |
| pokertool | 127.0.0.1 | 8060 | pokertool |

Override example:
```json
{
  "yhatzee": {"port": 9101, "host": "127.0.0.2"},
  "superquiz": {"port": 9103}
}
```

Launching `scripts/start.py` now brings the PokerTool service online alongside the other modules. Use `--pokertool-port` to move it off `127.0.0.1:8060` or `--no-pokertool` to skip it when you only need the frontend/API stack. The module writes a `POKERTOOL_SERVICE_START` event to Actifix’s structured log repository so you can verify the service published a heartbeat while the launcher is running.

The launcher now starts the standalone SuperQuiz GUI on its configured host/port (default `127.0.0.1:8070`) and probes `/health` to validate Flask and related dependencies before reporting the endpoint alongside the dashboard, backend, and Yhatzee servers. Use `--superquiz-port` to adjust the binding or `--no-superquiz` to skip the extra GUI when you do not need it.

## Ticket lifecycle (high-level)
1. Exception raised or manual capture call.
2. Raise_AF captures context, deduplicates, and classifies priority.
3. Ticket stored in `data/actifix.db`.
4. DoAF or CLI processes tickets, records completion evidence, and updates status.

## Background ticket agent
Actifix can run a long-lived ticket agent loop with lease renewal and idle backoff:

```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.do_af agent --idle-sleep 5 --idle-backoff-max 60 --renew-interval 300
```

Use `--no-ai` for non-interactive environments. To deterministically complete
tickets without AI, add `--fallback-complete`. Use `--priority P0 --priority P1`
to scope what the agent will pick up. The agent emits AgentVoice entries for
ticket acquisition, dispatch, success, and failure.

The launcher can run the agent alongside services via:
`python3 scripts/start.py --ticket-agent`.

## Background ticket agent roadmap
Actifix is ready for manual/CLI processing today, but background ticket agents need dedicated work.
The following tickets track the gap closures in detail:

- `ACT-20260125-FD74D` - Background ticket agent loop with lease renewals, idle backoff, and clean shutdown. (completed)
- `ACT-20260125-FF6CC` - Non-interactive processing policy with deterministic fallback when AI is unavailable. (completed)
- `ACT-20260125-35DCB` - AgentVoice instrumentation for DoAF acquisition, dispatch, completion, and failures. (completed)
- `ACT-20260125-B760C` - Health/monitoring for agent liveness, last-run time, and backlog lag. (completed)
- `ACT-20260125-2FC6E` - Managed daemon/launcher support for the ticket agent with logs and restart policy. (completed)
- `ACT-20260125-71BDF` - Tests covering background processing, lease renewal, fallback, and AgentVoice logging.

## Module health aggregation
`GET /api/modules/<module_id>/health` returns the aggregated health response:
```json
{
  "module": "yhatzee",
  "module_id": "modules.yhatzee",
  "module_status": "active",
  "status": "ok",
  "http_status": 200,
  "elapsed_ms": 12,
  "response": {"status": "ok"}
}
```
Status values: `ok`, `missing`, `timeout`, `error`.

## Release notes and version history
See `CHANGELOG.md` for full history. Recent highlights:

| Version | Highlights |
|---------|------------|
| **7.0.7** (2026-01-29) | Launcher now rebuilds the frontend via `scripts/build_frontend.py` before starting services so the GUI matches the backend version every time. The new `test/test_start_frontend_sync.py` ensures the build step fires and surfaces failures cleanly. |
| **7.0.4** (2026-01-29) | Workflow enforcement release that now requires agents to read the README, AGENTS, and `docs/INDEX.md` (plus referenced docs) before making changes, keeping Actifix rules first. |
| **7.0.2** (2026-01-28) | Patch release that makes `scripts/start.py` aggressively clean up stale Actifix processes and compiled bytecode before every launch so the runtime always begins from a clean slate. |
| **7.0.1** (2026-01-27) | Patch release that keeps the version-sync story aligned (docs, assets, UI/API) while capturing the latest release workflow content before the next milestone. |
| **7.0.0** (2026-01-26) | Big-point release aligning API and UI versions with refreshed release notes, synchronizing the version sync guidance, and keeping the screenscan/status story front-and-center before unlocking the next milestone. |
| **6.0.19** (2026-01-25) | **AgentVoice (AgentThoughts)** enforced for modules (info+error stream in `agent_voice` table, capped at 1,000,000 rows). **Start launcher** reports full runtime status and hard-restarts services on version change. |
| **4.0.49** (2026-01-21) | **ShootyMcShoot module**: React hello world holding page at `/modules/shootymcshoot` (127.0.0.1:8040). Follows ModuleBase pattern with metadata, health endpoint, local-only access. |
| **4.0.48** (2026-01-18) | **Ideas pane (=¡)**: Submit natural language feature requests/ideas via dashboard. AI analyzes and generates detailed tickets with priority, technical implementation details, success criteria, and remediation notes. Tickets created via `/api/ideas` ’ `ai_client.generate_fix()` ’ `record_error(source='gui_ideas')`. |
| **4.0.43** (2026-01-21) | Added OpenRouter Grok4 Fast support in AI provider options so the dashboard can pick the high-speed Grok4 endpoint when requested. |
| **4.0.42** (2026-01-21) | Redesigned the settings panel with gradient cards, status chips, and richer AI/system context so configuration feels themed and informative. |
| **4.0.41** (2026-01-21) | Added multi-agent workflow smoke tests to verify gitignore isolation, ignored agent directories, and develop-only flow, keeping binaries out. |
| **4.0.2** (2026-01-20) | Fixed API module parsing so `/api/modules` always returns system/user buckets, keeping the quick test cycle green after the dashboard refresh. |
| **4.0.0** (2026-01-18) | Monochrome compact dashboard refresh, AI settings + status sync with Do_AF, default Mimo Flash v2 free fallback, faster test suite defaults. |
| **3.3.11** (2026-01-18) | Documentation consolidation, quickstart refresh, and workflow accuracy cleanup. |
| **3.3.x** | Ongoing reliability improvements: test runner performance, database hardening, and workflow safeguards. |
| **2.7.0** (2026-01-11) | Multi-provider AI integration, database persistence, health monitoring, quarantine, architecture compliance tooling. |
| **2.6.0** (2026-01-10) | Self-improving framework launch, AI-native tickets, CLI, web dashboard, configuration. |
| **2.5.0** (2026-01-09) | Initial framework foundations and persistence scaffolding. |

## Migration notes
- Tickets live exclusively in `data/actifix.db`; legacy Markdown task lists are retired.
- Use Raise_AF, DoAF, or the CLI for ticket lifecycle operations.
- Configuration is environment-first; see `docs/INSTALLATION.md`.

## AgentVoice (AgentThoughts) Review Log

Actifix maintains an `agent_voice` table (also referred to as "AgentThoughts") inside `data/actifix.db`.
This is a review/audit stream intended to show what modules and agents are doing over time.

Rules:
- Every module must emit *informational* AgentVoice rows for key lifecycle events (startup/config/registration).
- Every module must emit *error* AgentVoice rows when capturing errors (in addition to Raise_AF tickets).
- Retention is capped at 1,000,000 rows; oldest rows are pruned automatically.

Enforcement points (centralized so coverage is consistent):
- `ModuleBase.log_gui_init()` emits AgentVoice INFO (best-effort).
- `ModuleBase.record_module_error()` emits AgentVoice ERROR (best-effort) and then calls `record_error()` to persist the canonical ticket.
- `actifix.api._register_module_blueprint()` emits AgentVoice INFO/ERROR for module registration outcomes (registered/disabled/failed), so modules are covered even if they don't explicitly call ModuleBase.

## Roadmap
1. **Ticket processing**: DoAF reliability and remediation automation.
2. **Operational tooling**: dashboards, health automation, and alerting.
3. **AI integration**: provider robustness and prompt compression workflows.

## Contribution checklist
1. Set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running Actifix or editing files.
2. Record work via `actifix.raise_af.record_error(...)`.
3. Run quality gates (tests, architecture validation) before committing.
4. Update docs and architecture artifacts with structural changes.

## License
Actifix is licensed under the terms in `docs/legal/LICENSE.md`.
