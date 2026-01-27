# Actifix Architecture Modules

Last updated: 2026-01-20
Source of truth: `docs/architecture/MAP.yaml`

This document summarizes the modules in the Actifix architecture. Use `MAP.yaml` and `DEPGRAPH.json` for canonical topology and dependency validation.

## Runtime

### bootstrap.main
- Summary: system initialization and process orchestration
- Entrypoints: `src/actifix/main.py`, `src/actifix/bootstrap.py`
- Depends on: `runtime.config`, `infra.logging`, `infra.health`, `infra.persistence.database`
- Contracts: ensures environment setup; launches core services in order

### runtime.api
- Summary: public API surface and package exports
- Entrypoints: `src/actifix/__init__.py`, `src/actifix/api.py`
- Depends on: `core.raise_af`, `bootstrap.main`, `runtime.state`, `infra.health`
- Contracts: expose stable API; centralize package exports

### runtime.config
- Summary: configuration management and environment normalization
- Entrypoints: `src/actifix/config.py`
- Depends on: `infra.logging`
- Contracts: centralize configuration; validate environment state; fail fast on invalid config

### runtime.state
- Summary: state management and persistence paths
- Entrypoints: `src/actifix/state_paths.py`
- Depends on: `infra.logging`
- Contracts: atomic state operations; recoverable state management

### runtime.dock_icon
- Summary: macOS dock icon helper utilities
- Entrypoints: `src/actifix/dock_icon.py`
- Depends on: none
- Contracts: safe no-op on non-macOS; avoid side effects on import

## Infrastructure

### infra.logging
- Summary: centralized logging system with correlation tracking
- Entrypoints: `src/actifix/log_utils.py`
- Depends on: none
- Contracts: single logging sink; structured error logging; correlation IDs

### infra.health
- Summary: health monitoring and system status tracking
- Entrypoints: `src/actifix/health.py`
- Depends on: `infra.logging`
- Contracts: detect degraded states; surface system health; continuous monitoring

### infra.persistence.atomic
- Summary: atomic file operations for durability and safety
- Entrypoints: `src/actifix/persistence/atomic.py`
- Depends on: `infra.logging`
- Contracts: atomic writes; append with size limits; idempotent operations

### infra.persistence.api
- Summary: persistence package public API and exports
- Entrypoints: `src/actifix/persistence/__init__.py`
- Depends on: `infra.persistence.atomic`, `infra.persistence.storage`, `infra.persistence.queue`, `infra.persistence.manager`, `infra.persistence.health`, `infra.persistence.paths`
- Contracts: re-export persistence interfaces; keep API stable

### infra.persistence.storage
- Summary: storage backend abstraction (file, memory, JSON)
- Entrypoints: `src/actifix/persistence/storage.py`
- Depends on: `infra.logging`, `infra.persistence.atomic`
- Contracts: pluggable storage backends; consistent interface; error handling

### infra.persistence.queue
- Summary: persistence queue for asynchronous operations
- Entrypoints: `src/actifix/persistence/queue.py`
- Depends on: `infra.logging`, `infra.persistence.storage`
- Contracts: durable operation queue; replay capability; entry pruning

### infra.persistence.manager
- Summary: high-level persistence management with transactions
- Entrypoints: `src/actifix/persistence/manager.py`
- Depends on: `infra.logging`, `infra.persistence.storage`, `infra.persistence.queue`
- Contracts: transactional operations; document management; queue integration

### infra.persistence.health
- Summary: storage health checks and corruption detection
- Entrypoints: `src/actifix/persistence/health.py`
- Depends on: `infra.logging`, `infra.persistence.storage`
- Contracts: storage validation; integrity verification; corruption detection

### infra.persistence.paths
- Summary: storage path configuration and management
- Entrypoints: `src/actifix/persistence/paths.py`
- Depends on: `infra.logging`
- Contracts: centralized path configuration; directory helpers

### infra.persistence.cleanup_config
- Summary: cleanup configuration for ticket retention policies
- Entrypoints: `src/actifix/persistence/cleanup_config.py`
- Depends on: none
- Contracts: centralize cleanup settings; environment-driven defaults

### infra.persistence.ticket_cleanup
- Summary: ticket cleanup and retention policy execution
- Entrypoints: `src/actifix/persistence/ticket_cleanup.py`
- Depends on: `infra.persistence.ticket_repo`
- Contracts: retention policy enforcement; auto-cleanup test tickets

### infra.persistence.event_repo
- Summary: lightweight event repository for diagnostics and testing helpers
- Entrypoints: `src/actifix/persistence/event_repo.py`
- Depends on: none
- Contracts: store simple events for instrumentation; provide resettable hooks for tests

### infra.persistence.database
- Summary: SQLite database backend with connection pooling and schema management
- Entrypoints: `src/actifix/persistence/database.py`
- Depends on: `infra.logging`
- Contracts: thread-safe connection pooling; schema migrations; WAL mode for concurrency

### infra.persistence.ticket_repo
- Summary: ticket repository with CRUD operations and locking
- Entrypoints: `src/actifix/persistence/ticket_repo.py`
- Depends on: `infra.logging`, `infra.persistence.database`, `core.raise_af`
- Contracts: database CRUD for tickets; lease-based locking; duplicate prevention

## Core

### core.raise_af
- Summary: error capture and ticket creation system
- Entrypoints: `src/actifix/raise_af.py`
- Depends on: `infra.logging`, `core.quarantine`, `infra.persistence.ticket_repo`, `security.ticket_throttler`
- Contracts: capture all errors; create structured tickets; prevent duplication

### core.do_af
- Summary: ticket processing and automated remediation
- Entrypoints: `src/actifix/do_af.py`
- Depends on: `infra.logging`, `core.raise_af`, `core.ai_client`, `infra.persistence.ticket_repo`
- Contracts: process tickets systematically; integrate with AI systems; validate fixes

### core.quarantine
- Summary: error isolation and safe failure handling
- Entrypoints: `src/actifix/quarantine.py`
- Depends on: `infra.logging`, `runtime.state`
- Contracts: isolate corrupted state; prevent system-wide failures

### core.ai_client
- Summary: multi-provider AI integration with fallback chain
- Entrypoints: `src/actifix/ai_client.py`
- Depends on: `runtime.config`, `infra.logging`, `runtime.state`, `security.credentials`
- Contracts: provider integration; fallback; cost tracking

### core.error_taxonomy
- Summary: error classification and taxonomy
- Entrypoints: `src/actifix/error_taxonomy.py`
- Depends on: `core.raise_af`
- Contracts: pattern matching; priority classification; remediation hints

### core.recovery
- Summary: state recovery and transaction rollback
- Entrypoints: `src/actifix/recovery.py`
- Depends on: `infra.logging`, `infra.persistence.manager`
- Contracts: recover from incomplete operations; rollback failed transactions

### core.self_repair
- Summary: self-repair blueprints and logging orchestration
- Entrypoints: `src/actifix/self_repair.py`
- Depends on: `infra.logging`
- Contracts: publish recoverability blueprints and record verification hints via log events

## Tooling

### tooling.testing.system
- Summary: system-level test framework and test builder
- Entrypoints: `src/actifix/testing/system.py`
- Depends on: `infra.logging`, `runtime.state`
- Contracts: build system tests; validate dependencies; enforce architecture

### tooling.testing.reporting
- Summary: test cycle reporting and progress tracking
- Entrypoints: `src/actifix/testing/reporting.py`
- Depends on: `infra.logging`, `tooling.testing.system`
- Contracts: test inventory; numbered progress; cycle logs

### tooling.testing
- Summary: quality assurance and testing framework
- Entrypoints: `src/actifix/testing/__init__.py`, `test/test_runner.py`
- Depends on: `bootstrap.main`, `infra.logging`, `core.raise_af`, `tooling.testing.system`, `tooling.testing.reporting`
- Contracts: enforce quality gates; maintain test coverage; validate architecture

### tooling.simple_ticket_attack
- Summary: batch creation of lightweight tickets
- Entrypoints: `src/actifix/simple_ticket_attack.py`
- Depends on: `core.raise_af`, `runtime.state`
- Contracts: generate ticket sequences; keep `data/actifix.db` untouched by manual edits

### tooling.bounce
- Summary: script to stop and restart Actifix processes
- Entrypoints: `scripts/bounce.py`
- Depends on: `bootstrap.main`
- Contracts: stop frontend/API processes; relaunch via `scripts/start.py`

## Security

### security.api
- Summary: security module public API and exports
- Entrypoints: `src/actifix/security/__init__.py`
- Depends on: `security.auth`, `security.credentials`, `security.rate_limiter`, `security.secrets_scanner`
- Contracts: re-export security interfaces; centralize security exports

### security.auth
- Summary: authentication and authorization
- Entrypoints: `src/actifix/security/auth.py`
- Depends on: `infra.logging`, `security.credentials`
- Contracts: JWT validation; RBAC enforcement; session management

### security.credentials
- Summary: credential management and password hashing
- Entrypoints: `src/actifix/security/credentials.py`
- Depends on: `infra.logging`
- Contracts: PBKDF2 hashing; secure comparison; credential storage

### security.rate_limiter
- Summary: token bucket rate limiting
- Entrypoints: `src/actifix/security/rate_limiter.py`
- Depends on: `infra.logging`, `runtime.config`
- Contracts: enforce per-minute/hour/day limits; track request metrics

### security.secrets_scanner
- Summary: secrets and sensitive data detection
- Entrypoints: `src/actifix/security/secrets_scanner.py`
- Depends on: `infra.logging`
- Contracts: detect API keys; sanitize sensitive output

### security.ticket_throttler
- Summary: ticket flood protection with throttling
- Entrypoints: `src/actifix/security/ticket_throttler.py`
- Depends on: `runtime.state`, `core.raise_af`
- Contracts: enforce per-priority limits; emergency brake

## Plugins

### plugins.permissions
- Summary: plugin permission and capability management
- Entrypoints: `src/actifix/plugins/permissions.py`
- Depends on: `plugins.protocol`, `security.auth`
- Contracts: define permissions; enforce capability-based security

### plugins.protocol
- Summary: standard metadata and health contracts for plugins
- Entrypoints: `src/actifix/plugins/protocol.py`
- Depends on: none
- Contracts: define plugin metadata; health contracts

### plugins.registry
- Summary: registry managing plugin lifecycle and observability
- Entrypoints: `src/actifix/plugins/registry.py`
- Depends on: `infra.logging`, `plugins.protocol`
- Contracts: one-time registration; lifecycle logging

### plugins.validation
- Summary: metadata validation and capability enforcement
- Entrypoints: `src/actifix/plugins/validation.py`
- Depends on: `infra.logging`, `plugins.protocol`
- Contracts: validate metadata; enforce semantic versioning

### plugins.sandbox
- Summary: isolation layer and safe registration wrapper
- Entrypoints: `src/actifix/plugins/sandbox.py`
- Depends on: `core.raise_af`, `infra.logging`, `plugins.registry`, `plugins.validation`
- Contracts: contain plugin failures; report load failures

### plugins.loader
- Summary: entry-point discovery and registration
- Entrypoints: `src/actifix/plugins/loader.py`
- Depends on: `core.raise_af`, `infra.logging`, `plugins.registry`, `plugins.validation`, `plugins.sandbox`
- Contracts: discover plugins; validate and sandbox

### plugins.api
- Summary: public API exports for plugin authors
- Entrypoints: `src/actifix/plugins/__init__.py`
- Depends on: `plugins.protocol`, `plugins.registry`
- Contracts: re-export plugin helpers; document activation steps

### plugins.builtin
- Summary: built-in self-testing plugin
- Entrypoints: `src/actifix/plugins/builtin.py`
- Depends on: `plugins.registry`, `plugins.protocol`
- Contracts: exercise registry sandboxing and health checks

## Modules

### modules.core
- Summary: module execution helpers (env/context, config overrides)
- Entrypoints: `src/actifix/modules/__init__.py`
- Depends on: `runtime.config`, `core.raise_af`
- Contracts: build a sanitized module environment; resolve per-module config overrides with safe defaults

### modules.registry
- Summary: central registry for module lifecycle hooks
- Entrypoints: `src/actifix/modules/registry.py`
- Depends on: `infra.logging`, `core.raise_af`
- Contracts: track module registration and shutdown hooks; emit module lifecycle log events; invoke module `module_register`/`module_unregister` hooks

### modules.scaffold
- Summary: module scaffolding helpers for CLI workflows
- Entrypoints: `src/actifix/modules/scaffold.py`
- Depends on: `infra.logging`
- Contracts: generate module boilerplate and health tests; enforce module naming and location conventions

### modules.superquiz
- Summary: multi-player quiz experience served via the dashboard API
- Entrypoints: `src/actifix/modules/superquiz/__init__.py`
- Depends on: `runtime.state`, `infra.logging`, `core.raise_af`, `runtime.api`
- Contracts: expose the SuperQuiz GUI at `/modules/superquiz` on the runtime API server while continuing to use centralized logging and error capture

### modules.yahtzee
- Summary: two-player Yahtzee game module whose GUI is embedded in the dashboard API
- Entrypoints: `src/actifix/modules/yahtzee/__init__.py`
- Depends on: `runtime.state`, `infra.logging`, `core.raise_af`, `runtime.api`
- Contracts: expose the two-player Yahtzee GUI at `/modules/yahtzee` on the runtime API server while continuing to use centralized logging and error capture
