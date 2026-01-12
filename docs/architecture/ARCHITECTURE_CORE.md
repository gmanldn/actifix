# ARCHITECTURE_CORE.md

## Quality-First System Architecture

---

## 1. Purpose and Scope

This document defines the **core, non-negotiable architecture** of the system.

It intentionally:

- Describes *how the system must behave*, not domain features
- Encodes **quality guarantees**, not implementation preferences
- Applies equally to human and AI contributors
- Serves as the **authoritative reference** for architecture, governance, and execution discipline

Anything not consistent with this document is considered **architectural drift**.

---

## 2. Architectural Philosophy

This system is built around five primary quality principles:

1. **Determinism**  
   No silent skips, no hidden state, no "probably fine" outcomes.

2. **Auditability**  
   Every meaningful action leaves a durable, inspectable trail.

3. **Enforcement Over Convention**  
   Rules are executable and verified, not advisory.

4. **Durability and Safety**  
   Crashes, partial writes, concurrent execution, and restarts are first-class design concerns.

5. **Continuity Over Time**  
   Decisions, constraints, and rationale persist across sessions, contributors, and automation.

Convenience is explicitly subordinate to quality.

---

## 3. Execution Model

### 3.1 Single Canonical Entrypoint

The system must be started from **one canonical entrypoint**, located at the project root.

Responsibilities of the entrypoint:

- Establish correct runtime environment (paths, config, logging)
- Initialise all global services in a defined order
- Perform pre-run safety checks
- Clean up residual processes from previous runs
- Gate optional platform-specific integrations

**No component may assume it is run directly.**

### 3.2 Environment Normalisation

At startup, the system must:

- Resolve and validate configuration sources
- Normalise import paths
- Initialise logging and correlation context
- Fail fast on invalid or ambiguous environment state

Implicit or "best effort" environment handling is prohibited.

---

## 4. Governance Model

### 4.1 Documentation-First Architecture

Documentation is a **first-class artifact**, not a by-product.

Rules:

- Documentation is created **before or alongside** code
- All documentation lives in a dedicated `docs/` hierarchy
- A central `INDEX.md` catalogs all documentation
- Each document must clearly state:
  - Purpose
  - Scope
  - Interfaces or guarantees
  - Known limitations

### 4.2 Forbidden Parallel Planning

To prevent architectural entropy, the following are **explicitly forbidden**:

- Standalone planning documents
- Roadmaps, design plans, or implementation plans
- Parallel TODO or task lists

All planning is centralised into **a single task registry**.

### 4.3 Decision Persistence

Architectural and design decisions must be:

- Recorded chronologically
- Accompanied by explicit rationale ("why", not just "what")
- Cross-referenced when superseded or conflicted

Decisions are treated as **state**, not commentary.

---

## 5. Task and Workflow Control

### 5.1 Single Source of Task Truth

All work is tracked through the **canonical `tickets` table in `data/actifix.db`**.

Rules:

- Tickets are created programmatically via `actifix.raise_af.record_error()` and the DoAF pipeline.
- Manual Markdown task files (e.g., `TASK_LIST.md`, `ACTIFIX-LIST.md`) are retired; they exist only in archives and never in active storage.
- Tasks must include acceptance criteria.
- Task completion requires validation, not declaration.

### 5.2 Definition of Done

A task is considered complete **only when all of the following are true**:

1. All relevant tests pass
2. Coverage requirements are met
3. Changes are committed
4. Changes are pushed to the canonical branch

Local-only completion is explicitly invalid.

---

## 6. Quality Gates

### 6.1 Test Execution Guarantees

The testing system must:

- Declare the full test plan before execution
- Execute exactly the declared plan
- Fail if the executed test count differs from the plan
- Provide deterministic, numbered progress reporting

Silent skips or partial execution are treated as failures.

### 6.2 Coverage Enforcement

Coverage is enforced as a **contract**, not a metric:

- Minimum thresholds are mandatory
- Critical paths may impose stricter thresholds
- Regressions are not permitted

Coverage checks are part of the standard execution pipeline.

---

## 7. Observability and Logging

### 7.1 Centralised Logging

All logging must:

- Route through a single logging system
- Write only to controlled locations
- Use structured formats where possible
- Be categorised by concern (runtime, errors, performance, security, testing)

Ad-hoc logging is prohibited.

### 7.2 Correlation and Traceability

A correlation identifier must:

- Be generated at the start of execution
- Propagate through all components
- Be attached to logs, errors, and derived artifacts

This enables end-to-end traceability across systems and time.

---

## 8. Failure and Error Philosophy

### 8.1 Errors as Structured Data

Errors are treated as:

- Structured events
- Inputs to governance systems
- Persisted artifacts

They are **never discarded, ignored, or handled silently**.

### 8.2 Mandatory Error Governance

All errors must flow through a central error governance system that:

- Deduplicates failures deterministically
- Records full context
- Tracks lifecycle from detection to resolution
- Prevents bypass paths

Manual or out-of-band error handling is prohibited.

---

## 9. Durability and Safety Guarantees

The system must assume:

- Unexpected termination can occur at any time
- Concurrent processes may exist
- Filesystem operations may be interrupted

As a result:

- Writes must be atomic
- State must be recoverable
- Corruption must be quarantined, not fatal
- Health checks must detect degraded states

---

## 10. Architecture Compliance

Any component, tool, or automation interacting with the system must:

- Respect this architecture
- Enforce its guarantees
- Refuse operation if invariants are violated

Architecture is enforced through **code, tests, and process**, not trust.

---

## 11. Summary

This architecture prioritises:

- Correctness over speed
- Visibility over convenience
- Enforcement over convention
- Continuity over local optimisation

It is intentionally strict.  
Relaxation of any rule requires an explicit recorded decision.
