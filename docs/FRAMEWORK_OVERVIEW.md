# Actifix Framework Overview

Actifix is a self-improving error management system that captures prioritized tickets, preserves operational context, and keeps the development workflow auditable. It is stdlib-first, resilient under failure, and designed to feed AI copilots with consistent context.

## What Actifix provides
- Structured error capture with priority classification (P0-P4).
- Deduplication via duplicate guards and ticket repository checks.
- Context capture (stack traces, file snippets, system state) with configurable limits.
- Durable persistence backed by `data/actifix.db`, with fallback queue support.
- Self-development mode to keep regressions visible during work.

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

## Ticket lifecycle (high-level)
1. Exception raised or manual capture call.
2. Raise_AF captures context, deduplicates, and classifies priority.
3. Ticket stored in `data/actifix.db`.
4. DoAF or CLI processes tickets, records completion evidence, and updates status.

## Release notes and version history
See `CHANGELOG.md` for full history. Recent highlights:

| Version | Highlights |
|---------|------------|
| **4.0.41** (2026-01-21) | Added multi-agent workflow smoke tests to verify gitignore isolation, ignored agent directories, and develop-only flow, keeping binaries out. |
| **4.0.40** (2026-01-21) | Version indicator UI now uses an all-black border and text so the status is readable against light/dark backgrounds. |
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
