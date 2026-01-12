# Actifix Architecture Modules

Generated: 2026-01-10T20:35:39.679117+00:00
Source Commit: Current Development

This file catalogs the architectural modules of the Actifix system. It provides a domain-driven breakdown of functionality, ownership, and dependencies.

## bootstrap.main

**Domain:** runtime  
**Owner:** runtime  
**Summary:** Main entrypoint orchestrating system initialization and process management  
**Entrypoints:** src/actifix/main.py, src/actifix/bootstrap.py  
**Contracts:** ensures environment setup; launches core services in correct order  
**Depends on:** runtime.config, infra.logging, infra.health  

## runtime.api

**Domain:** runtime  
**Owner:** runtime  
**Summary:** Public API surface and package exports  
**Entrypoints:** src/actifix/__init__.py, src/actifix/api.py  
**Contracts:** expose stable API; centralize package exports  
**Depends on:** core.raise_af, bootstrap.main, runtime.state, infra.health  

## runtime.config

**Domain:** runtime  
**Owner:** runtime  
**Summary:** Configuration management and environment normalization  
**Entrypoints:** src/actifix/config.py  
**Contracts:** centralize configuration; validate environment state; fail fast on invalid config  
**Depends on:** infra.logging  

## runtime.state

**Domain:** runtime  
**Owner:** runtime  
**Summary:** State management and persistence paths  
**Entrypoints:** src/actifix/state_paths.py  
**Contracts:** atomic state operations; recoverable state management  
**Depends on:** infra.logging  

## runtime.dock_icon

**Domain:** runtime  
**Owner:** runtime  
**Summary:** macOS dock icon helper utilities  
**Entrypoints:** src/actifix/dock_icon.py  
**Contracts:** safe no-op on non-macOS; avoid side effects on import  
**Depends on:** None  

## infra.logging

**Domain:** infra  
**Owner:** infra  
**Summary:** Centralized logging system with correlation tracking  
**Entrypoints:** src/actifix/log_utils.py  
**Contracts:** single logging sink; structured error logging; correlation IDs  

## infra.health

**Domain:** infra  
**Owner:** infra  
**Summary:** Health monitoring and system status tracking  
**Entrypoints:** src/actifix/health.py  
**Contracts:** detect degraded states; surface system health; continuous monitoring  
**Depends on:** infra.logging  

## infra.persistence.api

**Domain:** infra  
**Owner:** persistence  
**Summary:** Persistence package public API and exports  
**Entrypoints:** src/actifix/persistence/__init__.py  
**Contracts:** re-export persistence interfaces; keep API stable  
**Depends on:** infra.persistence.atomic, infra.persistence.storage, infra.persistence.queue, infra.persistence.manager, infra.persistence.health, infra.persistence.paths  

## infra.persistence.atomic

**Domain:** infra  
**Owner:** persistence  
**Summary:** Atomic file operations for durability and safety  
**Entrypoints:** src/actifix/persistence/atomic.py  
**Contracts:** atomic writes; append with size limits; idempotent operations  
**Depends on:** infra.logging  

## infra.persistence.storage

**Domain:** infra  
**Owner:** persistence  
**Summary:** Storage backend abstraction (file, memory, JSON)  
**Entrypoints:** src/actifix/persistence/storage.py  
**Contracts:** pluggable storage backends; consistent interface; error handling  
**Depends on:** infra.logging, infra.persistence.atomic  

## infra.persistence.queue

**Domain:** infra  
**Owner:** persistence  
**Summary:** Persistence queue for asynchronous operations  
**Entrypoints:** src/actifix/persistence/queue.py  
**Contracts:** durable operation queue; replay capability; entry pruning  
**Depends on:** infra.logging, infra.persistence.storage  

## infra.persistence.manager

**Domain:** infra  
**Owner:** persistence  
**Summary:** High-level persistence management with transactions  
**Entrypoints:** src/actifix/persistence/manager.py  
**Contracts:** transactional operations; document management; queue integration  
**Depends on:** infra.logging, infra.persistence.storage, infra.persistence.queue  

## infra.persistence.health

**Domain:** infra  
**Owner:** persistence  
**Summary:** Storage health checks and corruption detection  
**Entrypoints:** src/actifix/persistence/health.py  
**Contracts:** storage validation; integrity verification; corruption detection  
**Depends on:** infra.logging, infra.persistence.storage  

## infra.persistence.paths

**Domain:** infra  
**Owner:** persistence  
**Summary:** Storage path configuration and management  
**Entrypoints:** src/actifix/persistence/paths.py  
**Contracts:** centralized path configuration; directory helpers  
**Depends on:** infra.logging  

## infra.persistence.database

**Domain:** infra  
**Owner:** persistence  
**Summary:** SQLite database backend with connection pooling and schema management  
**Entrypoints:** src/actifix/persistence/database.py  
**Contracts:** thread-safe connection pooling; automatic schema migrations; WAL mode for concurrency  
**Depends on:** infra.logging  

## infra.persistence.ticket_repo

**Domain:** infra  
**Owner:** persistence  
**Summary:** Ticket repository with CRUD operations, locking, and duplicate prevention  
**Entrypoints:** src/actifix/persistence/ticket_repo.py  
**Contracts:** database CRUD for tickets; lease-based locking for DoAF agents; duplicate guard enforcement  
**Depends on:** infra.logging, infra.persistence.database, core.raise_af  

## core.raise_af

**Domain:** core  
**Owner:** core  
**Summary:** Error capture and ticket creation system  
**Entrypoints:** src/actifix/raise_af.py  
**Contracts:** capture all errors; create structured tickets; prevent duplication  
**Depends on:** infra.logging, core.quarantine  

## core.do_af

**Domain:** core  
**Owner:** core  
**Summary:** Ticket processing and automated remediation  
**Entrypoints:** src/actifix/do_af.py  
**Contracts:** process tickets systematically; integrate with AI systems; validate fixes  
**Depends on:** infra.logging, core.raise_af  

## core.ai_client

**Domain:** core  
**Owner:** core  
**Summary:** Multi-provider AI integration with automatic fallback chain  
**Entrypoints:** src/actifix/ai_client.py  
**Contracts:** Claude local auth detection; Claude API integration; OpenAI GPT-4 Turbo support; Ollama local model support; free alternative prompts; automatic provider fallback; cost tracking and logging  
**Depends on:** runtime.config, infra.logging, runtime.state  

## core.error_taxonomy

**Domain:** core  
**Owner:** core  
**Summary:** Enhanced error classification and taxonomy system  
**Entrypoints:** src/actifix/error_taxonomy.py  
**Contracts:** sophisticated error pattern matching; priority classification; remediation hints generation; extensible pattern system  
**Depends on:** core.raise_af  

## core.quarantine

**Domain:** core  
**Owner:** core  
**Summary:** Error isolation and safe failure handling  
**Entrypoints:** src/actifix/quarantine.py  
**Contracts:** isolate corrupted state; prevent system-wide failures  
**Depends on:** infra.logging, runtime.state  

## tooling.simple_ticket_attack

**Domain:** tooling  
**Owner:** tooling  
**Summary:** Batch creation of lightweight tickets through the Actifix pipeline  
**Entrypoints:** src/actifix/simple_ticket_attack.py  
**Contracts:** generate sequences of simple tickets via `record_error`; keep `data/actifix.db` intact (use API/DoAF for access); reuse core ticketing flow for experimentation  
**Depends on:** core.raise_af, runtime.state  

## tooling.testing.system

**Domain:** tooling  
**Owner:** testing  
**Summary:** System-level test framework and test builder  
**Entrypoints:** src/actifix/testing/system.py  
**Contracts:** build system tests; validate dependencies; enforce architecture  
**Depends on:** infra.logging, runtime.state  

## tooling.testing.reporting

**Domain:** tooling  
**Owner:** testing  
**Summary:** Test cycle reporting and progress tracking  
**Entrypoints:** src/actifix/testing/reporting.py  
**Contracts:** test inventory; numbered progress; cycle logs  
**Depends on:** infra.logging, tooling.testing.system  

## tooling.testing

**Domain:** tooling  
**Owner:** tooling  
**Summary:** Quality assurance and testing framework  
**Entrypoints:** src/actifix/testing/__init__.py, test.py  
**Contracts:** enforce quality gates; maintain test coverage; validate architecture  
**Depends on:** bootstrap.main, infra.logging, tooling.testing.system, tooling.testing.reporting  
