# Actifix Architecture Modules

Generated: 2026-01-10T10:07:22.862795+00:00
Source Commit: Current Development

This file catalogs the architectural modules of the Actifix system. It provides a domain-driven breakdown of functionality, ownership, and dependencies.

## bootstrap.main

**Domain:** runtime  
**Owner:** runtime  
**Summary:** Main entrypoint orchestrating system initialization and process management  
**Entrypoints:** src/actifix/main.py, src/actifix/bootstrap.py  
**Contracts:** ensures environment setup; launches core services in correct order  
**Depends on:** runtime.config, infra.logging, infra.health  

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

## core.quarantine

**Domain:** core  
**Owner:** core  
**Summary:** Error isolation and safe failure handling  
**Entrypoints:** src/actifix/quarantine.py  
**Contracts:** isolate corrupted state; prevent system-wide failures  
**Depends on:** infra.logging, runtime.state  

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
