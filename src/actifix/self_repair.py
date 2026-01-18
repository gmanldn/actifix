#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Self-repair blueprints describing automated recovery steps."""

from dataclasses import dataclass
from typing import Dict, Optional

from .log_utils import log_event


@dataclass(frozen=True)
class SelfRepairBlueprint:
    name: str
    category: str
    description: str
    verification_hint: str


BLUEPRINTS: Dict[str, SelfRepairBlueprint] = {
    "Auto-detect and repair database corruption": SelfRepairBlueprint(
        name="Auto-detect and repair database corruption",
        category="Self-Healing Database",
        description="Monitor the SQLite journal and WAL files, trigger recovery if corruption markers appear, and replay the last WAL checkpoint into a clean database copy.",
        verification_hint="Run the database corruption smoke test and ensure recovery artifacts are rotated through log_utils.log_event.",
    ),
    "Automatic connection pool recovery": SelfRepairBlueprint(
        name="Automatic connection pool recovery",
        category="Self-Healing Database",
        description="Refresh cached SQLite connections when abnormal lock contention is detected, forcing a reopen during maintenance windows.",
        verification_hint="Simulate connection saturation and verify the pool_reset event is emitted.",
    ),
    "Self-healing WAL checkpoint issues": SelfRepairBlueprint(
        name="Self-healing WAL checkpoint issues",
        category="Self-Healing Database",
        description="Detect stalled WAL checkpoints and trigger an immediate full checkpoint/backup to avoid log inflation.",
        verification_hint="Inspect WAL checkpoint logs after forcing a checkpoint failure in a test harness.",
    ),
    "Auto-vacuum scheduling and monitoring": SelfRepairBlueprint(
        name="Auto-vacuum scheduling and monitoring",
        category="Self-Healing Database",
        description="Schedule background vacuum passes when idle and watch free page ratios to avoid bloat.",
        verification_hint="Run the vacuum scheduler in dry-run mode and ensure the metric increments.",
    ),
    "Automatic migration rollback on failure": SelfRepairBlueprint(
        name="Automatic migration rollback on failure",
        category="Self-Healing Database",
        description="Wrap migrations in transactions so any failure automatically triggers a rollback and snapshot restoration.",
        verification_hint="Run a failing migration in CI and assert the rollback checkpoint table remains consistent.",
    ),
    "Database health monitoring with auto-repair triggers": SelfRepairBlueprint(
        name="Database health monitoring with auto-repair triggers",
        category="Self-Healing Database",
        description="Track corruption flags, file permissions, and disk usage and trigger follow-up repair flows when thresholds cross.",
        verification_hint="Use the self-repair monitor simulator to trip thresholds and verify the follow-up repair event.",
    ),
    "Connection leak detection and automatic cleanup": SelfRepairBlueprint(
        name="Connection leak detection and automatic cleanup",
        category="Self-Healing Database",
        description="Flag long-lived connections, close them gracefully, and log summaries so the reuse path can restart cleanly.",
        verification_hint="Exercise the leak detector stub in unit tests and ensure resource counters drop.",
    ),
    "Lock timeout detection with automatic retry": SelfRepairBlueprint(
        name="Lock timeout detection with automatic retry",
        category="Self-Healing Database",
        description="Detect blocking lock timeouts, back off with jitter, and retry critical operations once after resetting the lock holder.",
        verification_hint="Inject artificial locking contention and confirm the retry path is logged.",
    ),
    "Automatic index optimization when performance degrades": SelfRepairBlueprint(
        name="Automatic index optimization when performance degrades",
        category="Self-Healing Database",
        description="Track slow queries via sqlite_stat1, trigger index rebuilds for hot tables, and prune unused indexes.",
        verification_hint="Simulate slow queries and ensure the optimizer suggests indexes via log_event.",
    ),
    "Self-repairing duplicate guard collisions": SelfRepairBlueprint(
        name="Self-repairing duplicate guard collisions",
        category="Self-Healing Database",
        description="Detect duplicate guard violations, backfill deduplication logs, and resume processing without manual cleanup.",
        verification_hint="Feed duplicate entries into the duplicate guard monitor and verify cleanup entries appear in the audit log.",
    ),
}


class SelfRepairManager:
    """Provide discoverable plans for self-repair tickets."""

    def __init__(self) -> None:
        self.blueprints = BLUEPRINTS

    def find_blueprint(self, message: str) -> Optional[SelfRepairBlueprint]:
        normalized = message.strip().lower()
        for blueprint in self.blueprints.values():
            if blueprint.name.lower() in normalized:
                return blueprint
        return None

    def publish_plan(self, blueprint: SelfRepairBlueprint) -> SelfRepairBlueprint:
        log_event(
            "SELF_REPAIR_PLAN",
            f"Self-repair blueprint activated: {blueprint.name}",
            extra={
                "category": blueprint.category,
                "verification_hint": blueprint.verification_hint,
            },
        )
        return blueprint


def describe_task(message: str) -> str:
    manager = SelfRepairManager()
    blueprint = manager.find_blueprint(message)
    if blueprint is None:
        return "Self-repair blueprint not found. Refer to documentation for manual remediation."
    manager.publish_plan(blueprint)
    return (
        f"Planned {blueprint.name}: {blueprint.description}"
        f" (verify: {blueprint.verification_hint})"
    )