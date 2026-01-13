#!/usr/bin/env python3
"""
Start 200 module system documentation and testing tasks implementation by recording tickets via raise_af.
This follows the mandatory rule that all changes must start via Raise_AF.
"""

import sys
import os
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set required environment variables for Raise_AF workflow
os.environ["ACTIFIX_CHANGE_ORIGIN"] = "raise_af"
os.environ["ACTIFIX_CAPTURE_ENABLED"] = "1"

from actifix.raise_af import record_error, TicketPriority

# Parse module IDs from the architecture map
modules = []
map_path = Path(__file__).parent / "docs" / "architecture" / "MAP.yaml"
with open(map_path) as f:
    for line in f:
        match = re.match(r"\s*-\s+id:\s+(.+)", line)
        if match:
            modules.append(match.group(1))

# Filter out contract entries and duplicates
modules = list(dict.fromkeys([m for m in modules if not m.startswith("contract.")]))

# Define target task counts
TARGET_DOC_TASKS = 80
TARGET_TEST_TASKS = 80
TARGET_QUALITY_TASKS = 30
TARGET_ARCH_TASKS = 10

tasks = []

# Documentation tasks
for m in modules:
    tasks.append(f"Create module-level README for {m}")
for m in modules:
    tasks.append(f"Add API documentation with examples for {m}")
for d in ["runtime", "infra", "core", "tooling"]:
    tasks.append(f"Troubleshooting guide for {d} domain")
tasks.extend([
    "Migration guide: v2 to latest architecture updates",
    "Upgrade guide: persistence subsystem schema changes",
    "Upgrade guide: testing framework enhancements"
])
# Add integration guides to reach TARGET_DOC_TASKS
while len(tasks) < TARGET_DOC_TASKS:
    idx = sum(1 for t in tasks if t.startswith("Integration guide")) + 1
    tasks.append(f"Integration guide #{idx} for module interactions")

# Testing tasks
test_tasks = []
for m in modules:
    test_tasks.append(f"Increase unit test coverage to 95%+ for {m}")
for i in range(1, 21):
    test_tasks.append(f"Integration test suite #{i} for cross-module functionality")
for i in range(1, 16):
    test_tasks.append(f"Contract validation test #{i} for module contracts")
for i in range(1, 11):
    test_tasks.append(f"Error handling and edge case test #{i}")
for i in range(1, 7):
    test_tasks.append(f"Performance benchmark #{i} across critical modules")
# Add additional tests to reach TARGET_TEST_TASKS
while len(test_tasks) < TARGET_TEST_TASKS:
    idx = len(test_tasks) + 1
    test_tasks.append(f"Additional module system test task #{idx}")
# Trim to exact count
if len(test_tasks) > TARGET_TEST_TASKS:
    test_tasks = test_tasks[:TARGET_TEST_TASKS]
tasks.extend(test_tasks)

# Quality tasks
quality_tasks = []
for m in modules:
    quality_tasks.append(f"Add complete type hints for {m}")
quality_tasks.append("Implement automated docstring format validation check")
# Add additional quality tasks to reach TARGET_QUALITY_TASKS
while len(quality_tasks) < TARGET_QUALITY_TASKS:
    idx = len(quality_tasks) + 1
    quality_tasks.append(f"Supplemental code quality task #{idx}")
# Trim to exact count
if len(quality_tasks) > TARGET_QUALITY_TASKS:
    quality_tasks = quality_tasks[:TARGET_QUALITY_TASKS]
tasks.extend(quality_tasks)

# Architecture validation tasks
arch_tasks = [
    "Automated circular dependency detection",
    "Contract compliance CI check",
    "API stability monitoring",
    "Breaking change detection",
    "Layering enforcement tests",
    "Module interface consistency checks",
    "Dependency graph validation",
    "Cross-module error flow validation",
    "Health check integration per module",
    "Documentation-code synchronization check"
]
tasks.extend(arch_tasks)

# Record tickets
created = 0
for msg in tasks:
    entry = record_error(
        message=msg,
        source="start_200_module_quality_tasks.py",
        run_label="module-quality-200-tasks",
        error_type="ModuleQualityTask",
        priority=TicketPriority.P2,
        skip_duplicate_check=True,
        skip_ai_notes=True,
        capture_context=False
    )
    if entry:
        created += 1

print(f"Created {created}/{len(tasks)} module system quality tickets")
