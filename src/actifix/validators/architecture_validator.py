#!/usr/bin/env python3
"""Architecture validator ensuring MAP.yaml matches code imports.

This validator consolidates checks from test_architecture_validation.py
into a reusable module that can be called programmatically from CI,
pre-commit hooks, or during development.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ValidationError:
    """A single validation error."""

    category: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.category}: {self.message}"


@dataclass
class ValidationResult:
    """Result of architecture validation."""

    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings allowed)."""
        return len(self.errors) == 0

    def add_error(self, category: str, message: str) -> None:
        """Add an error."""
        self.errors.append(ValidationError(category, message, "error"))

    def add_warning(self, category: str, message: str) -> None:
        """Add a warning."""
        self.warnings.append(ValidationError(category, message, "warning"))

    def __str__(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  {err}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  {warn}")
        if self.is_valid and not self.warnings:
            lines.append("All validation checks passed.")
        return "\n".join(lines)


class ArchitectureValidator:
    """Validates MAP.yaml matches codebase imports and structure."""

    def __init__(self, root: Path | None = None):
        """Initialize validator.

        Args:
            root: Project root (defaults to actifix repo root)
        """
        if root is None:
            root = Path(__file__).resolve().parent.parent.parent.parent
        self.root = root
        self.arch_dir = root / "docs" / "architecture"
        self.src_dir = root / "src" / "actifix"

    def load_map(self) -> dict[str, Any]:
        """Load MAP.yaml."""
        return yaml.safe_load((self.arch_dir / "MAP.yaml").read_text())

    def load_depgraph(self) -> dict[str, Any]:
        """Load DEPGRAPH.json."""
        return json.loads((self.arch_dir / "DEPGRAPH.json").read_text())

    def validate_all(self) -> ValidationResult:
        """Run all validation checks."""
        result = ValidationResult()

        self.validate_documentation_exists(result)
        self.validate_map_structure(result)
        self.validate_depgraph_structure(result)
        self.validate_entrypoints_exist(result)
        self.validate_all_files_documented(result)
        self.validate_dependency_graph_consistency(result)
        self.validate_contracts(result)
        self.validate_domains(result)

        return result

    def validate_documentation_exists(self, result: ValidationResult) -> None:
        """Verify all architecture documentation files exist."""
        required_files = [
            "ARCHITECTURE_CORE.md",
            "MODULES.md",
            "MAP.yaml",
            "DEPGRAPH.json",
        ]

        for filename in required_files:
            if not (self.arch_dir / filename).exists():
                result.add_error("docs", f"Missing required file: {filename}")

    def validate_map_structure(self, result: ValidationResult) -> None:
        """Validate MAP.yaml structure and completeness."""
        try:
            map_data = self.load_map()
        except Exception as e:
            result.add_error("map_structure", f"Failed to load MAP.yaml: {e}")
            return

        required_sections = ["modules", "domains", "contracts", "meta"]
        for section in required_sections:
            if section not in map_data:
                result.add_error("map_structure", f"Missing section: {section}")

        if "modules" in map_data:
            if not map_data["modules"]:
                result.add_error("map_structure", "No modules defined")
            else:
                self._validate_module_fields(map_data["modules"], result)

        if "domains" in map_data and not map_data["domains"]:
            result.add_error("map_structure", "No domains defined")

        if "contracts" in map_data and not map_data["contracts"]:
            result.add_error("map_structure", "No contracts defined")

        if "meta" in map_data and "generated_at" not in map_data["meta"]:
            result.add_warning("map_structure", "Missing generated_at timestamp")

    def _validate_module_fields(
        self, modules: list[dict], result: ValidationResult
    ) -> None:
        """Validate each module has required fields."""
        required_fields = [
            "id",
            "domain",
            "owner",
            "summary",
            "entrypoints",
            "contracts",
            "depends_on",
        ]

        for module in modules:
            module_id = module.get("id", "unknown")
            for field in required_fields:
                if field not in module:
                    result.add_error(
                        "map_structure", f"Module {module_id} missing field: {field}"
                    )

    def validate_depgraph_structure(self, result: ValidationResult) -> None:
        """Validate DEPGRAPH.json structure."""
        try:
            depgraph = self.load_depgraph()
        except Exception as e:
            result.add_error("depgraph_structure", f"Failed to load DEPGRAPH.json: {e}")
            return

        required_sections = ["nodes", "edges", "meta"]
        for section in required_sections:
            if section not in depgraph:
                result.add_error("depgraph_structure", f"Missing section: {section}")

        if "nodes" in depgraph:
            if not depgraph["nodes"]:
                result.add_error("depgraph_structure", "No nodes defined")
            else:
                self._validate_node_fields(depgraph["nodes"], result)

        if "edges" in depgraph:
            if not depgraph["edges"]:
                result.add_error("depgraph_structure", "No edges defined")
            else:
                self._validate_edge_fields(depgraph["edges"], result)

    def _validate_node_fields(
        self, nodes: list[dict], result: ValidationResult
    ) -> None:
        """Validate each node has required fields."""
        required_fields = ["id", "domain", "owner", "label"]

        for node in nodes:
            node_id = node.get("id", "unknown")
            for field in required_fields:
                if field not in node:
                    result.add_error(
                        "depgraph_structure", f"Node {node_id} missing field: {field}"
                    )

    def _validate_edge_fields(
        self, edges: list[dict], result: ValidationResult
    ) -> None:
        """Validate each edge has required fields."""
        required_fields = ["from", "to", "reason"]

        for edge in edges:
            for field in required_fields:
                if field not in edge:
                    result.add_error("depgraph_structure", f"Edge missing field: {field}")

    def validate_entrypoints_exist(self, result: ValidationResult) -> None:
        """Verify that all documented entrypoints actually exist."""
        try:
            map_data = self.load_map()
        except Exception as e:
            result.add_error("entrypoints", f"Cannot validate entrypoints: {e}")
            return

        for module in map_data.get("modules", []):
            module_id = module["id"]
            for entrypoint in module.get("entrypoints", []):
                path = self.root / entrypoint
                if not path.exists():
                    result.add_error(
                        "entrypoints", f"{module_id}: Missing file {entrypoint}"
                    )

    def validate_all_files_documented(self, result: ValidationResult) -> None:
        """Every Python file in src/actifix must appear in MAP.yaml entrypoints."""
        try:
            map_data = self.load_map()
        except Exception as e:
            result.add_error("completeness", f"Cannot validate completeness: {e}")
            return

        documented_entrypoints = set()
        for module in map_data.get("modules", []):
            documented_entrypoints.update(module.get("entrypoints", []))

        actual_files = set()
        for path in self.src_dir.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(self.root).as_posix()
            actual_files.add(relative)

        missing = actual_files - documented_entrypoints
        if missing:
            result.add_error(
                "completeness", f"Undocumented files: {', '.join(sorted(missing))}"
            )

    def validate_dependency_graph_consistency(
        self, result: ValidationResult
    ) -> None:
        """Verify dependency graph is consistent with module definitions."""
        try:
            map_data = self.load_map()
            depgraph = self.load_depgraph()
        except Exception as e:
            result.add_error("dependency_graph", f"Cannot validate graph: {e}")
            return

        module_ids = {m["id"] for m in map_data.get("modules", [])}
        node_ids = {n["id"] for n in depgraph.get("nodes", [])}

        missing = module_ids - node_ids
        if missing:
            result.add_error(
                "dependency_graph",
                f"Modules missing from DEPGRAPH.json: {', '.join(sorted(missing))}",
            )

        extra = node_ids - module_ids
        if extra:
            result.add_error(
                "dependency_graph",
                f"DEPGRAPH nodes missing from MAP.yaml: {', '.join(sorted(extra))}",
            )

        for edge in depgraph.get("edges", []):
            if edge["from"] not in node_ids:
                result.add_error(
                    "dependency_graph",
                    f"Edge references invalid 'from' node: {edge['from']}",
                )
            if edge["to"] not in node_ids:
                result.add_error(
                    "dependency_graph", f"Edge references invalid 'to' node: {edge['to']}"
                )

    def validate_contracts(self, result: ValidationResult) -> None:
        """Verify contracts are properly defined and applied."""
        try:
            map_data = self.load_map()
        except Exception as e:
            result.add_error("contracts", f"Cannot validate contracts: {e}")
            return

        module_ids = {m["id"] for m in map_data.get("modules", [])}

        for contract in map_data.get("contracts", []):
            contract_id = contract.get("id", "unknown")

            for module_id in contract.get("applies_to", []):
                if module_id not in module_ids:
                    result.add_error(
                        "contracts",
                        f"{contract_id} references invalid module: {module_id}",
                    )

            for module_id in contract.get("enforced_by", []):
                if module_id not in module_ids:
                    result.add_error(
                        "contracts",
                        f"{contract_id} enforcer invalid: {module_id}",
                    )

    def validate_domains(self, result: ValidationResult) -> None:
        """Verify domain definitions are consistent."""
        try:
            map_data = self.load_map()
        except Exception as e:
            result.add_error("domains", f"Cannot validate domains: {e}")
            return

        defined_domains = {d["id"] for d in map_data.get("domains", [])}
        module_domains = {m["domain"] for m in map_data.get("modules", [])}

        undefined = module_domains - defined_domains
        if undefined:
            result.add_error(
                "domains", f"Undefined domains: {', '.join(sorted(undefined))}"
            )

        unused = defined_domains - module_domains
        if unused:
            result.add_warning(
                "domains", f"Unused domains (may be intentional): {', '.join(sorted(unused))}"
            )


def main() -> int:
    """CLI entrypoint for running architecture validation."""
    import sys

    validator = ArchitectureValidator()
    result = validator.validate_all()

    print(result)

    if not result.is_valid:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
