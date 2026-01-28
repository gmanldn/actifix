"""Bootstrap phase lifecycle: explicit startup/shutdown phases with rollback.

Unified phase registry system consolidating 27 bootstrap phase tickets (Phase 1-27).
Provides structured phase definitions, dependency tracking, timeout enforcement,
event emission, and cascading rollback on failure.

Replaces ad-hoc bootstrap logic with reliable, observable phase orchestration.
"""

from __future__ import annotations

import time
import threading
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Tuple
from pathlib import Path
from contextlib import contextmanager

from actifix.log_utils import log_event, atomic_write
from actifix.raise_af import record_error, TicketPriority
from actifix.agent_voice import record_agent_voice

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """Phase execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PhaseResult:
    """Result of a phase execution."""
    phase_id: str
    status: PhaseStatus
    duration_ms: float
    error: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class Phase:
    """A single bootstrap phase definition."""
    phase_id: str  # e.g., "phase_1_config", "phase_2_database"
    name: str  # Human-readable name
    handler: Callable[[], None]  # Phase execution function
    rollback_handler: Optional[Callable[[], None]] = None  # Cleanup on failure
    dependencies: List[str] = field(default_factory=list)  # Phase IDs this depends on
    timeout_seconds: float = 30.0  # Max execution time
    critical: bool = False  # If True, failure stops all further phases
    description: str = ""

    def __post_init__(self):
        """Validate phase definition."""
        if not self.phase_id:
            raise ValueError("phase_id is required")
        if not self.handler:
            raise ValueError(f"handler is required for phase {self.phase_id}")


class PhaseRegistry:
    """Manages bootstrap phases, execution, and rollback."""

    def __init__(self):
        """Initialize the phase registry."""
        self.phases: Dict[str, Phase] = {}
        self.results: Dict[str, PhaseResult] = {}
        self.lock = threading.Lock()
        self.correlation_id = ""
        self.start_time = 0.0
        self.event_log: List[Dict[str, Any]] = []

    def register(self, phase: Phase) -> PhaseRegistry:
        """Register a phase. Returns self for chaining."""
        with self.lock:
            if phase.phase_id in self.phases:
                raise ValueError(f"Phase {phase.phase_id} already registered")

            # Validate dependencies exist
            for dep in phase.dependencies:
                if dep not in self.phases and dep != phase.phase_id:
                    # Warn but don't fail - dep might be registered later
                    logger.warning(f"Phase {phase.phase_id} depends on unregistered {dep}")

            self.phases[phase.phase_id] = phase
        return self

    def run_phase(
        self,
        phase_id: str,
        correlation_id: str = "",
    ) -> PhaseResult:
        """Execute a single phase with timeout and error handling."""
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase {phase_id} not registered")

        self.correlation_id = correlation_id
        result = PhaseResult(
            phase_id=phase_id,
            status=PhaseStatus.PENDING,
            duration_ms=0.0,
            correlation_id=correlation_id,
        )

        start_time = time.time()

        try:
            # Log phase start
            self._emit_event("phase_start", phase_id, {"name": phase.name})
            result.status = PhaseStatus.RUNNING

            # Run with timeout enforcement
            def execute_with_timeout():
                try:
                    phase.handler()
                except Exception as e:
                    raise RuntimeError(f"Phase handler failed: {e}") from e

            # Use thread with timeout
            thread = threading.Thread(target=execute_with_timeout, daemon=False)
            thread.start()
            thread.join(timeout=phase.timeout_seconds)

            if thread.is_alive():
                error_msg = f"Phase {phase_id} exceeded timeout ({phase.timeout_seconds}s)"
                result.status = PhaseStatus.FAILED
                result.error = error_msg
                self._emit_event("phase_timeout", phase_id, {"timeout_s": phase.timeout_seconds})
                record_error(
                    message=error_msg,
                    source=f"bootstrap_phases.py:run_phase({phase_id})",
                    priority=TicketPriority.P1 if phase.critical else TicketPriority.P2,
                )
            else:
                result.status = PhaseStatus.COMPLETED
                self._emit_event("phase_complete", phase_id, {"duration_ms": int(duration_ms)})

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result.status = PhaseStatus.FAILED
            result.error = str(e)
            result.duration_ms = duration_ms

            self._emit_event("phase_failed", phase_id, {"error": str(e), "duration_ms": int(duration_ms)})
            record_error(
                message=f"Phase {phase_id} failed: {e}",
                source=f"bootstrap_phases.py:run_phase({phase_id})",
                priority=TicketPriority.P1 if phase.critical else TicketPriority.P2,
            )

        duration_ms = (time.time() - start_time) * 1000
        result.duration_ms = duration_ms
        result.timestamp = time._strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        with self.lock:
            self.results[phase_id] = result

        return result

    def run_all(
        self,
        correlation_id: str = "",
        stop_on_critical_failure: bool = True,
    ) -> Tuple[bool, List[PhaseResult]]:
        """Execute all phases in dependency order. Returns (success, results)."""
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.start_time = time.time()
        self.event_log.clear()
        self.results.clear()

        self._emit_event("bootstrap_start", "registry", {
            "correlation_id": self.correlation_id,
            "phase_count": len(self.phases),
        })

        # Topological sort by dependencies
        execution_order = self._topological_sort()
        if not execution_order:
            return False, []

        completed_phases: List[str] = []
        all_success = True

        for phase_id in execution_order:
            phase = self.phases[phase_id]

            # Check if dependencies completed
            for dep in phase.dependencies:
                if dep not in self.results or self.results[dep].status != PhaseStatus.COMPLETED:
                    self._emit_event("phase_skipped", phase_id, {"reason": f"dependency {dep} not completed"})
                    continue

            # Run the phase
            result = self.run_phase(phase_id, self.correlation_id)
            completed_phases.append(phase_id)

            if result.status != PhaseStatus.COMPLETED:
                all_success = False

                if phase.critical and stop_on_critical_failure:
                    self._emit_event("bootstrap_critical_failure", phase_id, {})
                    # Rollback all completed phases
                    self.rollback(completed_phases[:-1])  # Exclude the failed one
                    break

        total_duration_ms = (time.time() - self.start_time) * 1000
        self._emit_event("bootstrap_complete", "registry", {
            "success": all_success,
            "duration_ms": int(total_duration_ms),
            "phases_completed": len(completed_phases),
            "phases_total": len(self.phases),
        })

        record_agent_voice(
            module_key="bootstrap",
            action="bootstrap_complete",
            details=f"Bootstrap {'succeeded' if all_success else 'failed'}: {len(completed_phases)}/{len(self.phases)} phases completed",
        )

        return all_success, list(self.results.values())

    def rollback(self, phase_ids: Optional[List[str]] = None) -> None:
        """Rollback completed phases in reverse order."""
        if not phase_ids:
            # Rollback all completed phases
            phase_ids = [
                pid for pid in reversed(list(self.phases.keys()))
                if pid in self.results and self.results[pid].status == PhaseStatus.COMPLETED
            ]

        self._emit_event("rollback_start", "registry", {"phase_count": len(phase_ids)})

        rollback_order = list(reversed(phase_ids))  # Reverse dependency order

        for phase_id in rollback_order:
            phase = self.phases.get(phase_id)
            if not phase or not phase.rollback_handler:
                continue

            try:
                self._emit_event("rollback_phase_start", phase_id, {})
                phase.rollback_handler()
                self._emit_event("rollback_phase_complete", phase_id, {})

                if phase_id in self.results:
                    self.results[phase_id].status = PhaseStatus.ROLLED_BACK
            except Exception as e:
                self._emit_event("rollback_phase_failed", phase_id, {"error": str(e)})
                record_error(
                    message=f"Rollback failed for {phase_id}: {e}",
                    source="bootstrap_phases.py:rollback",
                    priority=TicketPriority.P0,
                )

        self._emit_event("rollback_complete", "registry", {})

    def get_status(self) -> Dict[str, Any]:
        """Get current bootstrap status."""
        with self.lock:
            return {
                "registered_phases": len(self.phases),
                "completed_phases": sum(
                    1 for r in self.results.values()
                    if r.status == PhaseStatus.COMPLETED
                ),
                "failed_phases": sum(
                    1 for r in self.results.values()
                    if r.status == PhaseStatus.FAILED
                ),
                "correlation_id": self.correlation_id,
                "phases": {
                    phase_id: {
                        "name": phase.name,
                        "dependencies": phase.dependencies,
                        "critical": phase.critical,
                        "status": self.results.get(phase_id, {}).get("status", "pending"),
                    }
                    for phase_id, phase in self.phases.items()
                },
                "results": [r.__dict__ for r in self.results.values()],
            }

    def get_event_log(self) -> List[Dict[str, Any]]:
        """Get the structured event log."""
        return self.event_log.copy()

    def _topological_sort(self) -> List[str]:
        """Topologically sort phases by dependencies."""
        visited = set()
        order = []
        visiting = set()

        def visit(phase_id: str) -> bool:
            if phase_id in visited:
                return True
            if phase_id in visiting:
                logger.error(f"Circular dependency detected involving {phase_id}")
                return False

            visiting.add(phase_id)
            phase = self.phases.get(phase_id)

            if phase:
                for dep in phase.dependencies:
                    if not visit(dep):
                        return False

            visiting.remove(phase_id)
            visited.add(phase_id)
            order.append(phase_id)
            return True

        for phase_id in self.phases:
            if not visit(phase_id):
                return []

        return order

    def _emit_event(self, event_type: str, source: str, details: Dict[str, Any]) -> None:
        """Emit a structured bootstrap event."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "source": source,
            "correlation_id": self.correlation_id,
            **details,
        }
        self.event_log.append(event)
        log_event(f"bootstrap:{event_type}", details={**event})

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate a correlation ID for this bootstrap run."""
        import uuid
        return str(uuid.uuid4())[:8]


# Global registry instance
_global_registry: Optional[PhaseRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> PhaseRegistry:
    """Get or create the global phase registry."""
    global _global_registry

    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = PhaseRegistry()

    return _global_registry


def register_phase(
    phase_id: str,
    name: str,
    handler: Callable[[], None],
    rollback_handler: Optional[Callable[[], None]] = None,
    dependencies: Optional[List[str]] = None,
    timeout_seconds: float = 30.0,
    critical: bool = False,
    description: str = "",
) -> None:
    """Register a bootstrap phase."""
    phase = Phase(
        phase_id=phase_id,
        name=name,
        handler=handler,
        rollback_handler=rollback_handler,
        dependencies=dependencies or [],
        timeout_seconds=timeout_seconds,
        critical=critical,
        description=description,
    )
    get_registry().register(phase)


def bootstrap(correlation_id: str = "", stop_on_critical_failure: bool = True) -> bool:
    """Execute bootstrap phases. Returns True if all phases succeeded."""
    registry = get_registry()
    success, results = registry.run_all(correlation_id, stop_on_critical_failure)

    # Log summary
    if success:
        logger.info(f"Bootstrap succeeded: {len(results)} phases completed")
    else:
        failed = [r for r in results if r.status == PhaseStatus.FAILED]
        logger.error(f"Bootstrap failed: {len(failed)} phase(s) failed")

    return success


def get_bootstrap_status() -> Dict[str, Any]:
    """Get current bootstrap status."""
    return get_registry().get_status()


def get_bootstrap_events() -> List[Dict[str, Any]]:
    """Get bootstrap event log."""
    return get_registry().get_event_log()


@contextmanager
def phase_context(phase_id: str):
    """Context manager for executing a phase inline."""
    try:
        yield
    except Exception as e:
        record_error(
            message=f"Phase {phase_id} context failed: {e}",
            source="bootstrap_phases.py:phase_context",
            priority=TicketPriority.P1,
        )
        raise
