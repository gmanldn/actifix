#!/usr/bin/env python3
"""
Update architecture documentation to include missing persistence and testing modules.

This script ensures MODULES.md, MAP.yaml, and DEPGRAPH.json are fully synchronized
with the actual codebase structure.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
ARCH_DIR = ROOT / "Arch"


def update_modules_md():
    """Update MODULES.md with missing persistence and testing modules."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    content = f"""# Actifix Architecture Modules

Generated: {timestamp}
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
"""
    
    (ARCH_DIR / "MODULES.md").write_text(content)
    print(f"✓ Updated MODULES.md")


def update_map_yaml():
    """Update MAP.yaml with complete module definitions."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    map_data = {
        "schema_version": "arch-map.v1",
        "meta": {
            "generated_at": timestamp,
            "generator": "update_architecture_docs.py",
            "generator_version": "2.0.0",
            "source_commit": "current_development",
            "freshness_days": 7,
            "notes": [
                "Single source of truth for actifix architecture contexts",
                "Keep aligned with quality gates and architecture compliance",
                "Auto-generated - includes persistence and testing subsystems"
            ]
        },
        "domains": [
            {"id": "runtime", "summary": "Bootstrap, configuration, state management, lifecycle"},
            {"id": "infra", "summary": "Logging, health monitoring, persistence, observability"},
            {"id": "core", "summary": "Error handling, ticket management, automated remediation"},
            {"id": "tooling", "summary": "Testing, quality assurance, architecture validation"}
        ],
        "modules": [
            {
                "id": "bootstrap.main",
                "domain": "runtime",
                "owner": "runtime",
                "summary": "Main entrypoint orchestrating system initialization and process management",
                "entrypoints": ["src/actifix/main.py", "src/actifix/bootstrap.py"],
                "contracts": ["ensures environment setup", "launches core services in correct order"],
                "depends_on": ["runtime.config", "infra.logging", "infra.health"]
            },
            {
                "id": "runtime.api",
                "domain": "runtime",
                "owner": "runtime",
                "summary": "Public API surface and package exports",
                "entrypoints": ["src/actifix/__init__.py", "src/actifix/api.py"],
                "contracts": ["expose stable API", "centralize package exports"],
                "depends_on": ["core.raise_af", "bootstrap.main", "runtime.state", "infra.health"]
            },
            {
                "id": "runtime.config",
                "domain": "runtime",
                "owner": "runtime",
                "summary": "Configuration management and environment normalization",
                "entrypoints": ["src/actifix/config.py"],
                "contracts": ["centralize configuration", "validate environment state", "fail fast on invalid config"],
                "depends_on": ["infra.logging"]
            },
            {
                "id": "runtime.state",
                "domain": "runtime",
                "owner": "runtime",
                "summary": "State management and persistence paths",
                "entrypoints": ["src/actifix/state_paths.py"],
                "contracts": ["atomic state operations", "recoverable state management"],
                "depends_on": ["infra.logging"]
            },
            {
                "id": "runtime.dock_icon",
                "domain": "runtime",
                "owner": "runtime",
                "summary": "macOS dock icon helper utilities",
                "entrypoints": ["src/actifix/dock_icon.py"],
                "contracts": ["safe no-op on non-macOS", "avoid side effects on import"],
                "depends_on": []
            },
            {
                "id": "infra.logging",
                "domain": "infra",
                "owner": "infra",
                "summary": "Centralized logging system with correlation tracking",
                "entrypoints": ["src/actifix/log_utils.py"],
                "contracts": ["single logging sink", "structured error logging", "correlation IDs"],
                "depends_on": []
            },
            {
                "id": "infra.health",
                "domain": "infra",
                "owner": "infra",
                "summary": "Health monitoring and system status tracking",
                "entrypoints": ["src/actifix/health.py"],
                "contracts": ["detect degraded states", "surface system health", "continuous monitoring"],
                "depends_on": ["infra.logging"]
            },
            {
                "id": "infra.persistence.atomic",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Atomic file operations for durability and safety",
                "entrypoints": ["src/actifix/persistence/atomic.py"],
                "contracts": ["atomic writes", "append with size limits", "idempotent operations"],
                "depends_on": ["infra.logging"]
            },
            {
                "id": "infra.persistence.api",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Persistence package public API and exports",
                "entrypoints": ["src/actifix/persistence/__init__.py"],
                "contracts": ["re-export persistence interfaces", "keep API stable"],
                "depends_on": [
                    "infra.persistence.atomic",
                    "infra.persistence.storage",
                    "infra.persistence.queue",
                    "infra.persistence.manager",
                    "infra.persistence.health",
                    "infra.persistence.paths"
                ]
            },
            {
                "id": "infra.persistence.storage",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Storage backend abstraction (file, memory, JSON)",
                "entrypoints": ["src/actifix/persistence/storage.py"],
                "contracts": ["pluggable storage backends", "consistent interface", "error handling"],
                "depends_on": ["infra.logging", "infra.persistence.atomic"]
            },
            {
                "id": "infra.persistence.queue",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Persistence queue for asynchronous operations",
                "entrypoints": ["src/actifix/persistence/queue.py"],
                "contracts": ["durable operation queue", "replay capability", "entry pruning"],
                "depends_on": ["infra.logging", "infra.persistence.storage"]
            },
            {
                "id": "infra.persistence.manager",
                "domain": "infra",
                "owner": "persistence",
                "summary": "High-level persistence management with transactions",
                "entrypoints": ["src/actifix/persistence/manager.py"],
                "contracts": ["transactional operations", "document management", "queue integration"],
                "depends_on": ["infra.logging", "infra.persistence.storage", "infra.persistence.queue"]
            },
            {
                "id": "infra.persistence.health",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Storage health checks and corruption detection",
                "entrypoints": ["src/actifix/persistence/health.py"],
                "contracts": ["storage validation", "integrity verification", "corruption detection"],
                "depends_on": ["infra.logging", "infra.persistence.storage"]
            },
            {
                "id": "infra.persistence.paths",
                "domain": "infra",
                "owner": "persistence",
                "summary": "Storage path configuration and management",
                "entrypoints": ["src/actifix/persistence/paths.py"],
                "contracts": ["centralized path configuration", "directory helpers"],
                "depends_on": ["infra.logging"]
            },
            {
                "id": "core.raise_af",
                "domain": "core",
                "owner": "core",
                "summary": "Error capture and ticket creation system",
                "entrypoints": ["src/actifix/raise_af.py"],
                "contracts": ["capture all errors", "create structured tickets", "prevent duplication"],
                "depends_on": ["infra.logging", "core.quarantine"]
            },
            {
                "id": "core.do_af",
                "domain": "core",
                "owner": "core",
                "summary": "Ticket processing and automated remediation",
                "entrypoints": ["src/actifix/do_af.py"],
                "contracts": ["process tickets systematically", "integrate with AI systems", "validate fixes"],
                "depends_on": ["infra.logging", "core.raise_af"]
            },
            {
                "id": "core.quarantine",
                "domain": "core",
                "owner": "core",
                "summary": "Error isolation and safe failure handling",
                "entrypoints": ["src/actifix/quarantine.py"],
                "contracts": ["isolate corrupted state", "prevent system-wide failures"],
                "depends_on": ["infra.logging", "runtime.state"]
            },
            {
                "id": "tooling.testing.system",
                "domain": "tooling",
                "owner": "testing",
                "summary": "System-level test framework and test builder",
                "entrypoints": ["src/actifix/testing/system.py"],
                "contracts": ["build system tests", "validate dependencies", "enforce architecture"],
                "depends_on": ["infra.logging", "runtime.state"]
            },
            {
                "id": "tooling.testing.reporting",
                "domain": "tooling",
                "owner": "testing",
                "summary": "Test cycle reporting and progress tracking",
                "entrypoints": ["src/actifix/testing/reporting.py"],
                "contracts": ["test inventory", "numbered progress", "cycle logs"],
                "depends_on": ["infra.logging", "tooling.testing.system"]
            },
            {
                "id": "tooling.testing",
                "domain": "tooling",
                "owner": "tooling",
                "summary": "Quality assurance and testing framework",
                "entrypoints": ["src/actifix/testing/__init__.py", "test.py"],
                "contracts": ["enforce quality gates", "maintain test coverage", "validate architecture"],
                "depends_on": ["bootstrap.main", "infra.logging", "tooling.testing.system", "tooling.testing.reporting"]
            }
        ],
        "contracts": [
            {
                "id": "contract.logging",
                "summary": "All modules must log via centralized logging system with correlation IDs",
                "applies_to": [
                    "bootstrap.main", "runtime.config", "core.raise_af", "core.do_af",
                    "infra.health", "infra.persistence.atomic", "infra.persistence.storage",
                    "infra.persistence.queue", "infra.persistence.manager", "tooling.testing"
                ],
                "enforced_by": ["infra.logging"]
            },
            {
                "id": "contract.error_isolation",
                "summary": "Error handling must isolate failures and prevent system-wide corruption",
                "applies_to": ["core.raise_af", "core.do_af"],
                "enforced_by": ["core.quarantine"]
            },
            {
                "id": "contract.quality_gates",
                "summary": "All components must pass quality gates and maintain architecture compliance",
                "applies_to": [
                    "bootstrap.main", "runtime.config", "runtime.state", "core.raise_af",
                    "core.do_af", "infra.persistence.manager"
                ],
                "enforced_by": ["tooling.testing", "infra.health"]
            },
            {
                "id": "contract.durability",
                "summary": "All persistence operations must be atomic and recoverable",
                "applies_to": [
                    "infra.persistence.atomic", "infra.persistence.storage",
                    "infra.persistence.queue", "infra.persistence.manager"
                ],
                "enforced_by": ["infra.persistence.atomic", "infra.persistence.health"]
            }
        ]
    }
    
    with open(ARCH_DIR / "MAP.yaml", 'w') as f:
        yaml.dump(map_data, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"✓ Updated MAP.yaml")


def update_depgraph_json():
    """Update DEPGRAPH.json with all modules as nodes."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Load current MAP to get module list
    with open(ARCH_DIR / "MAP.yaml") as f:
        map_data = yaml.safe_load(f)
    
    # Build nodes from modules
    nodes = []
    for module in map_data["modules"]:
        node = {
            "id": module["id"],
            "domain": module["domain"],
            "owner": module["owner"],
            "label": module["id"].split(".")[-1]  # Last part of ID
        }
        nodes.append(node)
    
    # Build edges from dependencies
    edges = []
    for module in map_data["modules"]:
        module_id = module["id"]
        for dep in module["depends_on"]:
            edge = {
                "from": module_id,
                "to": dep,
                "reason": f"{module_id} depends on {dep}"
            }
            edges.append(edge)
    
    depgraph_data = {
        "schema_version": "arch-depgraph.v1",
        "meta": {
            "generated_at": timestamp,
            "generator": "update_architecture_docs.py",
            "generator_version": "2.0.0",
            "source_commit": "current_development"
        },
        "nodes": nodes,
        "edges": edges
    }
    
    with open(ARCH_DIR / "DEPGRAPH.json", 'w') as f:
        json.dump(depgraph_data, f, indent=2)
    
    print(f"✓ Updated DEPGRAPH.json")


def main():
    """Update all architecture documentation files."""
    print("Updating architecture documentation...")
    print()
    
    update_modules_md()
    update_map_yaml()
    update_depgraph_json()
    
    print()
    print("✓ Architecture documentation updated successfully!")
    print()
    print("Next steps:")
    print("  1. Run: python3 test.py to validate changes")
    print("  2. Review: Arch/MODULES.md, Arch/MAP.yaml, and Arch/DEPGRAPH.json")
    print("  3. Commit and push changes")


if __name__ == "__main__":
    main()
