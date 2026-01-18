# Actifix Architecture Core

This document defines the core, non-negotiable architecture and quality guarantees of Actifix. Any change that conflicts with this document is considered architectural drift.

## Purpose and scope
- Describe how the system must behave, not just what it does.
- Encode quality guarantees, not implementation preferences.
- Apply equally to humans and AI agents.
- Serve as the authoritative reference for governance and execution discipline.

## Architectural philosophy
1. **Determinism**: no silent skips or ambiguous outcomes.
2. **Auditability**: every meaningful action leaves a durable trail.
3. **Enforcement over convention**: rules are executable and verified.
4. **Durability and safety**: crashes and partial writes are first-class concerns.
5. **Continuity over time**: decisions and constraints persist across sessions.

## Execution model
### Single canonical entrypoint
Actifix must be started from a single canonical entrypoint at the project root. The entrypoint is responsible for:
- Environment setup (paths, config, logging)
- Pre-run safety checks
- Core service initialization
- Optional platform integrations

### Environment normalization
Startup must:
- Validate configuration sources
- Normalize import paths
- Initialize logging and correlation context
- Fail fast on invalid state

## Governance model
### Documentation-first architecture
- Documentation is a first-class artifact.
- All docs live in `docs/` and are indexed in `docs/INDEX.md`.
- Each doc states purpose, scope, interfaces, and limitations.

### Forbidden parallel planning
- No standalone planning docs.
- No parallel TODO or task lists.
- Task tracking lives in the ticket database.

### Decision persistence
- Decisions are recorded chronologically with rationale.
- Superseded decisions must be referenced.

## Task and workflow control
### Single source of truth
All work is tracked in the `tickets` table within `data/actifix.db`. Tickets are created via Raise_AF and processed through DoAF or the CLI.

### Definition of done
A task is complete only when:
1. Tests pass.
2. Coverage requirements are met.
3. Changes are committed.
4. Changes are pushed to the canonical branch.

## Quality gates
- Test plans are declared before execution.
- Execution must match the declared plan.
- Coverage is enforced as a contract.

## Observability and logging
- All logging routes through centralized logging.
- Correlation IDs propagate through logs and tickets.

## Failure philosophy
- Errors are structured data and persisted.
- No silent suppression: capture, record, and re-raise.

## Durability and safety
- Writes are atomic.
- State is recoverable.
- Corruption is quarantined, not fatal.

## Compliance
Any component or tool interacting with Actifix must enforce these guarantees. Relaxing rules requires an explicit decision record.
