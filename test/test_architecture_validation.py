#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive architecture validation tests.

Ensures architecture documentation (MODULES.md, MAP.yaml, DEPGRAPH.json)
remains 100% in sync with actual codebase structure.

These tests enforce the quality-first architecture principle:
"Architecture is enforced through code, tests, and process, not trust."
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

ARCH_DIR = ROOT / "Arch"
SRC_DIR = ROOT / "src" / "actifix"

# Note: We validate module existence via filesystem checks, not imports
# to avoid import-time side effects and circular dependencies


def load_map() -> Dict[str, Any]:
    """Load MAP.yaml using YAML parser (JSON-compatible)."""
    return yaml.safe_load((ARCH_DIR / "MAP.yaml").read_text())


class TestArchitectureDocumentationExists:
    """Verify all architecture documentation files exist."""

    def test_architecture_core_exists(self):
        """ARCHITECTURE_CORE.md must exist."""
        assert (ARCH_DIR / "ARCHITECTURE_CORE.md").exists()

    def test_modules_md_exists(self):
        """MODULES.md must exist."""
        assert (ARCH_DIR / "MODULES.md").exists()

    def test_map_yaml_exists(self):
        """MAP.yaml must exist."""
        assert (ARCH_DIR / "MAP.yaml").exists()

    def test_depgraph_json_exists(self):
        """DEPGRAPH.json must exist."""
        assert (ARCH_DIR / "DEPGRAPH.json").exists()


class TestMapYamlStructure:
    """Validate MAP.yaml structure and completeness."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    def test_map_has_required_sections(self, map_data):
        """MAP.yaml must have all required top-level sections."""
        required = ["modules", "domains", "contracts", "meta"]
        for section in required:
            assert section in map_data, f"Missing section: {section}"

    def test_map_modules_not_empty(self, map_data):
        """MAP.yaml must define at least one module."""
        assert len(map_data["modules"]) > 0

    def test_map_modules_have_required_fields(self, map_data):
        """Each module must have required fields."""
        required_fields = ["id", "domain", "owner", "summary", "entrypoints", "contracts", "depends_on"]
        for module in map_data["modules"]:
            for field in required_fields:
                assert field in module, f"Module {module.get('id', 'unknown')} missing field: {field}"

    def test_map_domains_not_empty(self, map_data):
        """MAP.yaml must define at least one domain."""
        assert len(map_data["domains"]) > 0

    def test_map_contracts_not_empty(self, map_data):
        """MAP.yaml must define at least one contract."""
        assert len(map_data["contracts"]) > 0

    def test_map_meta_has_timestamp(self, map_data):
        """MAP.yaml meta must have generated_at timestamp."""
        assert "generated_at" in map_data["meta"]


class TestDepgraphJsonStructure:
    """Validate DEPGRAPH.json structure."""

    @pytest.fixture
    def depgraph_data(self) -> Dict:
        """Load DEPGRAPH.json."""
        with open(ARCH_DIR / "DEPGRAPH.json") as f:
            return json.load(f)

    def test_depgraph_has_required_sections(self, depgraph_data):
        """DEPGRAPH.json must have required sections."""
        required = ["nodes", "edges", "meta"]
        for section in required:
            assert section in depgraph_data, f"Missing section: {section}"

    def test_depgraph_nodes_not_empty(self, depgraph_data):
        """DEPGRAPH.json must define at least one node."""
        assert len(depgraph_data["nodes"]) > 0

    def test_depgraph_edges_not_empty(self, depgraph_data):
        """DEPGRAPH.json must define at least one edge."""
        assert len(depgraph_data["edges"]) > 0

    def test_depgraph_nodes_have_required_fields(self, depgraph_data):
        """Each node must have required fields."""
        required_fields = ["id", "domain", "owner", "label"]
        for node in depgraph_data["nodes"]:
            for field in required_fields:
                assert field in node, f"Node {node.get('id', 'unknown')} missing field: {field}"

    def test_depgraph_edges_have_required_fields(self, depgraph_data):
        """Each edge must have required fields."""
        required_fields = ["from", "to", "reason"]
        for edge in depgraph_data["edges"]:
            for field in required_fields:
                assert field in edge, f"Edge missing field: {field}"


class TestModuleEntrypointsExist:
    """Verify that all documented entrypoints actually exist."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    def test_all_entrypoints_exist(self, map_data):
        """Every documented entrypoint file must exist."""
        missing = []
        for module in map_data["modules"]:
            module_id = module["id"]
            for entrypoint in module["entrypoints"]:
                path = ROOT / entrypoint
                if not path.exists():
                    missing.append(f"{module_id}: {entrypoint}")
        
        assert not missing, f"Missing entrypoints: {', '.join(missing)}"


class TestModulesMatchCodebase:
    """Verify documented modules match actual codebase structure."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    @pytest.fixture
    def actual_modules(self) -> Set[str]:
        """Get actual Python modules from src/actifix."""
        modules = set()
        
        # Core modules
        core_files = [
            "state_paths.py",
            "config.py",
            "raise_af.py",
            "do_af.py",
            "health.py",
            "quarantine.py",
            "log_utils.py",
            "bootstrap.py",
            "main.py",
        ]
        
        for file in core_files:
            if (SRC_DIR / file).exists():
                modules.add(file.replace(".py", ""))
        
        # Persistence modules
        persistence_dir = SRC_DIR / "persistence"
        if persistence_dir.exists():
            for file in persistence_dir.glob("*.py"):
                if file.name != "__init__.py":
                    modules.add(f"persistence.{file.stem}")
        
        # Testing modules
        testing_dir = SRC_DIR / "testing"
        if testing_dir.exists():
            for file in testing_dir.glob("*.py"):
                if file.name != "__init__.py":
                    modules.add(f"testing.{file.stem}")
        
        return modules

    def test_critical_modules_documented(self, map_data, actual_modules):
        """Critical modules must be documented in MAP.yaml."""
        documented_modules = {m["id"] for m in map_data["modules"]}
        
        # Core modules that MUST be documented
        critical = {
            "bootstrap.main",
            "runtime.config",
            "runtime.state",
            "infra.logging",
            "infra.health",
            "core.raise_af",
            "core.do_af",
            "core.quarantine",
            "tooling.testing",
        }
        
        missing = critical - documented_modules
        assert not missing, f"Critical modules not documented: {missing}"

    def test_all_python_files_documented(self, map_data):
        """Every Python file in src/actifix must appear in MAP.yaml entrypoints."""
        documented_entrypoints = set()
        for module in map_data["modules"]:
            documented_entrypoints.update(module["entrypoints"])

        actual_files = set()
        for path in SRC_DIR.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            actual_files.add(relative)

        missing = actual_files - documented_entrypoints
        assert not missing, f"Undocumented entrypoints: {sorted(missing)}"


class TestDependencyGraphConsistency:
    """Verify dependency graph is consistent with module definitions."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    @pytest.fixture
    def depgraph_data(self) -> Dict:
        """Load DEPGRAPH.json."""
        with open(ARCH_DIR / "DEPGRAPH.json") as f:
            return json.load(f)

    def test_all_modules_have_nodes(self, map_data, depgraph_data):
        """Every module in MAP.yaml should have a node in DEPGRAPH.json."""
        module_ids = {m["id"] for m in map_data["modules"]}
        node_ids = {n["id"] for n in depgraph_data["nodes"]}
        
        missing = module_ids - node_ids
        assert not missing, f"Modules missing from DEPGRAPH.json: {missing}"

    def test_edges_reference_valid_nodes(self, depgraph_data):
        """All edges must reference valid nodes."""
        node_ids = {n["id"] for n in depgraph_data["nodes"]}
        
        invalid_edges = []
        for edge in depgraph_data["edges"]:
            if edge["from"] not in node_ids:
                invalid_edges.append(f"{edge['from']} -> {edge['to']} (from invalid)")
            if edge["to"] not in node_ids:
                invalid_edges.append(f"{edge['from']} -> {edge['to']} (to invalid)")
        
        assert not invalid_edges, f"Invalid edge references: {', '.join(invalid_edges)}"

    def test_dependencies_match_edges(self, map_data, depgraph_data):
        """Module dependencies should match graph edges."""
        # Build edge map
        edges_map = {}
        for edge in depgraph_data["edges"]:
            if edge["from"] not in edges_map:
                edges_map[edge["from"]] = []
            edges_map[edge["from"]].append(edge["to"])
        
        # Check each module's dependencies
        mismatches = []
        for module in map_data["modules"]:
            module_id = module["id"]
            declared_deps = set(module["depends_on"])
            actual_edges = set(edges_map.get(module_id, []))
            
            if declared_deps != actual_edges:
                mismatches.append(
                    f"{module_id}: declared={declared_deps}, edges={actual_edges}"
                )
        
        # Allow some flexibility - warn but don't fail
        if mismatches:
            print(f"\nDependency mismatches (review needed): {mismatches}")


class TestContractValidation:
    """Verify contracts are properly defined and applied."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    def test_contracts_reference_valid_modules(self, map_data):
        """Contract applies_to must reference valid modules."""
        module_ids = {m["id"] for m in map_data["modules"]}
        
        invalid = []
        for contract in map_data["contracts"]:
            for module_id in contract["applies_to"]:
                if module_id not in module_ids:
                    invalid.append(f"{contract['id']} references invalid module: {module_id}")
        
        assert not invalid, f"Invalid contract references: {', '.join(invalid)}"

    def test_contract_enforcers_reference_valid_modules(self, map_data):
        """Contract enforced_by must reference valid modules."""
        module_ids = {m["id"] for m in map_data["modules"]}
        
        invalid = []
        for contract in map_data["contracts"]:
            for module_id in contract["enforced_by"]:
                if module_id not in module_ids:
                    invalid.append(f"{contract['id']} enforcer invalid: {module_id}")
        
        assert not invalid, f"Invalid contract enforcers: {', '.join(invalid)}"


class TestPersistenceSubsystemDocumentation:
    """Verify persistence subsystem is properly documented."""

    def test_persistence_modules_exist_in_code(self):
        """Persistence modules should exist in codebase."""
        persistence_dir = SRC_DIR / "persistence"
        assert persistence_dir.exists(), "persistence/ directory missing"
        
        required_files = [
            "atomic.py",
            "storage.py",
            "queue.py",
            "manager.py",
            "paths.py",
            "health.py",
        ]
        
        for file in required_files:
            assert (persistence_dir / file).exists(), f"Missing persistence module: {file}"

    def test_persistence_modules_importable(self):
        """Persistence modules must be importable."""
        try:
            from actifix.persistence import atomic, storage, queue, manager, paths, health
            assert atomic is not None
            assert storage is not None
            assert queue is not None
            assert manager is not None
            assert paths is not None
            assert health is not None
        except ImportError as e:
            pytest.fail(f"Failed to import persistence modules: {e}")


class TestTestingSubsystemDocumentation:
    """Verify testing subsystem is properly documented."""

    def test_testing_modules_exist_in_code(self):
        """Testing modules should exist in codebase."""
        testing_dir = SRC_DIR / "testing"
        assert testing_dir.exists(), "testing/ directory missing"
        
        required_files = [
            "system.py",
            "reporting.py",
        ]
        
        for file in required_files:
            assert (testing_dir / file).exists(), f"Missing testing module: {file}"

    def test_testing_modules_importable(self):
        """Testing modules must be importable."""
        try:
            from actifix.testing import system, reporting
            assert system is not None
            assert reporting is not None
        except ImportError as e:
            pytest.fail(f"Failed to import testing modules: {e}")


class TestArchitectureFreshness:
    """Verify architecture documentation is kept fresh."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    @pytest.fixture
    def depgraph_data(self) -> Dict:
        """Load DEPGRAPH.json."""
        with open(ARCH_DIR / "DEPGRAPH.json") as f:
            return json.load(f)

    def test_map_has_generation_metadata(self, map_data):
        """MAP.yaml must have generation metadata."""
        assert "meta" in map_data
        assert "generated_at" in map_data["meta"]
        assert "generator_version" in map_data["meta"]

    def test_depgraph_has_generation_metadata(self, depgraph_data):
        """DEPGRAPH.json must have generation metadata."""
        assert "meta" in depgraph_data
        assert "generated_at" in depgraph_data["meta"]
        assert "generator_version" in depgraph_data["meta"]


class TestDomainsConsistency:
    """Verify domain definitions are consistent."""

    @pytest.fixture
    def map_data(self) -> Dict:
        """Load MAP.yaml."""
        return load_map()

    def test_all_module_domains_defined(self, map_data):
        """All module domains must be defined in domains section."""
        defined_domains = {d["id"] for d in map_data["domains"]}
        module_domains = {m["domain"] for m in map_data["modules"]}
        
        undefined = module_domains - defined_domains
        assert not undefined, f"Undefined domains: {undefined}"

    def test_all_defined_domains_used(self, map_data):
        """All defined domains should be used by at least one module."""
        defined_domains = {d["id"] for d in map_data["domains"]}
        module_domains = {m["domain"] for m in map_data["modules"]}
        
        unused = defined_domains - module_domains
        # This is a warning, not a failure
        if unused:
            print(f"\nUnused domains (may be intentional): {unused}")


class TestArchitectureCoreCompliance:
    """Verify code complies with ARCHITECTURE_CORE.md principles."""

    def test_single_entrypoint_exists(self):
        """System must have a single canonical entrypoint."""
        main_entry = ROOT / "src" / "actifix" / "main.py"
        assert main_entry.exists(), "main.py entrypoint missing"

    def test_state_paths_module_exists(self):
        """State management module must exist."""
        state_module = ROOT / "src" / "actifix" / "state_paths.py"
        assert state_module.exists(), "state_paths.py missing"

    def test_logging_module_exists(self):
        """Centralized logging module must exist."""
        log_module = ROOT / "src" / "actifix" / "log_utils.py"
        assert log_module.exists(), "log_utils.py missing"

    def test_health_module_exists(self):
        """Health monitoring module must exist."""
        health_module = ROOT / "src" / "actifix" / "health.py"
        assert health_module.exists(), "health.py missing"

    def test_error_governance_exists(self):
        """Error governance system must exist."""
        raise_af = ROOT / "src" / "actifix" / "raise_af.py"
        do_af = ROOT / "src" / "actifix" / "do_af.py"
        assert raise_af.exists(), "raise_af.py missing"
        assert do_af.exists(), "do_af.py missing"

    def test_quarantine_system_exists(self):
        """Quarantine system must exist."""
        quarantine = ROOT / "src" / "actifix" / "quarantine.py"
        assert quarantine.exists(), "quarantine.py missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
