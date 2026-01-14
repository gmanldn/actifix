#!/usr/bin/env python3
"""Create 200 tickets outlining the plugin architecture rollout."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

from actifix.raise_af import TicketPriority, record_error

# Raise_AF gating
os.environ.setdefault("ACTIFIX_CHANGE_ORIGIN", "raise_af")
os.environ.setdefault("ACTIFIX_CAPTURE_ENABLED", "1")

BASE_DIR = Path(__file__).resolve().parents[1]
MAP_PATH = BASE_DIR / "docs" / "architecture" / "MAP.yaml"

sys.path.insert(0, str(BASE_DIR / "src"))

with MAP_PATH.open(encoding="utf-8") as fh:
    architecture = yaml.safe_load(fh)

plugin_modules = [mod for mod in architecture.get("modules", []) if mod.get("domain") == "plugins"]

tasks: list[str] = []

foundation = [
    "Define the Plugin protocol, metadata, and health contracts.",
    "Document the plugin registry and registry helpers for authors.",
    "Validate plugin metadata via semantic versioning and capability checks.",
    "Sandbox plugin registry operations and capture failures.",
    "Build the entry-point discovery loader with importlib.metadata.",
]

tasks.extend(foundation)

def add_span(title: str, count: int, template: str | None = None) -> None:
    for index in range(1, count + 1):
        if template:
            tasks.append(template.format(index))
        else:
            tasks.append(f"{title} #{index}")

add_span("Create docs for plugin registry traceability", 12)
add_span("Write unit tests for plugin loader and registry", 20)
add_span("Add integration tests for plugin onboarding workflow", 20)
add_span("Capture architecture diagrams for plugin subsystem", 15)
add_span("Create troubleshooting guide for plugin failures", 8)
add_span("Design plugin health monitoring story", 10)
add_span("Automate plugin contract validation in CI", 6)
add_span("Add type hints and docstrings for plugin helpers", 12)
add_span("Document plugin entry points in MAP/DEPGRAPH", 7)
add_span("Add release checklist for plugin ecosystem", 5)
add_span("Review plugin dependency compatibility matrix", 6)
add_span("Create self-testing plugin for loader validation", 15)
add_span("Add plugin diagnostics logging to infra logging", 10)
add_span("Verify entry point discovery works in venvs", 6)
add_span("Document plugin enable/disable flow", 5)

for component in plugin_modules:
    module_id = component["id"]
    tasks.append(f"Audit documentation for {module_id} to describe capabilities and contracts")
    tasks.append(f"Add cross-module tests that exercise {module_id} dependencies")

add_span("Plugin governance retrospective", 5)
add_span("Cross-check plugin docs with architecture map", 5)
add_span("Add plugin onboarding KPIs", 5)
add_span("Create plugin CLI helpers", 5)
add_span("Simulate plugin failure scenarios", 5)
add_span("Add plugin compliance ticket summary", 3)

while len(tasks) < 200:
    tasks.append(f"Additional plugin architecture task #{len(tasks) + 1}")

created = 0
for task in tasks[:200]:
    entry = record_error(
        message=task,
        source="start_plugin_architecture_tasks.py",
        error_type="PluginArchitecture",
        priority=TicketPriority.P2,
        run_label="plugin-architecture-200",
        skip_duplicate_check=True,
        skip_ai_notes=True,
        capture_context=False,
    )
    if entry:
        created += 1

print(f"Created {created}/{min(200, len(tasks))} plugin architecture tickets")
