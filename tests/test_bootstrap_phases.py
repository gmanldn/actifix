"""Tests for bootstrap phase lifecycle system (consolidates 27 bootstrap phase tickets)."""

import pytest
import time
import threading
from typing import List

from actifix.bootstrap_phases import (
    Phase,
    PhaseRegistry,
    PhaseStatus,
    PhaseResult,
    register_phase,
    bootstrap,
    get_bootstrap_status,
    get_bootstrap_events,
)


class TestPhaseDefinition:
    """Test Phase dataclass and validation."""

    def test_phase_creation(self):
        """Test creating a phase."""
        def handler():
            pass

        phase = Phase(
            phase_id="test_phase",
            name="Test Phase",
            handler=handler,
        )
        assert phase.phase_id == "test_phase"
        assert phase.name == "Test Phase"
        assert phase.handler == handler
        assert phase.dependencies == []
        assert phase.timeout_seconds == 30.0
        assert not phase.critical

    def test_phase_missing_id(self):
        """Test that phase ID is required."""
        with pytest.raises(ValueError, match="phase_id is required"):
            Phase(
                phase_id="",
                name="Test",
                handler=lambda: None,
            )

    def test_phase_missing_handler(self):
        """Test that handler is required."""
        with pytest.raises(ValueError, match="handler is required"):
            Phase(
                phase_id="test",
                name="Test",
                handler=None,
            )

    def test_phase_with_dependencies(self):
        """Test phase with dependencies."""
        phase = Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: None,
            dependencies=["phase_1"],
        )
        assert phase.dependencies == ["phase_1"]

    def test_phase_critical_flag(self):
        """Test critical phase flag."""
        phase = Phase(
            phase_id="critical_phase",
            name="Critical",
            handler=lambda: None,
            critical=True,
        )
        assert phase.critical


class TestPhaseRegistry:
    """Test PhaseRegistry functionality."""

    def test_registry_creation(self):
        """Test creating a registry."""
        registry = PhaseRegistry()
        assert registry.phases == {}
        assert registry.results == {}

    def test_register_phase(self):
        """Test registering a phase."""
        registry = PhaseRegistry()
        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: None,
        )
        registry.register(phase)
        assert "test" in registry.phases
        assert registry.phases["test"] == phase

    def test_register_duplicate_phase(self):
        """Test that duplicate phase registration fails."""
        registry = PhaseRegistry()
        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: None,
        )
        registry.register(phase)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(phase)

    def test_chaining_registration(self):
        """Test that register returns self for chaining."""
        registry = PhaseRegistry()
        result = registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: None,
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: None,
            dependencies=["phase_1"],
        ))
        assert result == registry
        assert len(registry.phases) == 2

    def test_run_phase_success(self):
        """Test running a phase successfully."""
        registry = PhaseRegistry()
        executed = []

        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: executed.append(True),
        )
        registry.register(phase)

        result = registry.run_phase("test")

        assert result.phase_id == "test"
        assert result.status == PhaseStatus.COMPLETED
        assert executed == [True]

    def test_run_phase_failure(self):
        """Test running a phase that fails."""
        registry = PhaseRegistry()

        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: (_ for _ in ()).throw(RuntimeError("Test error")),
        )
        registry.register(phase)

        result = registry.run_phase("test")

        assert result.status == PhaseStatus.FAILED
        assert "Test error" in result.error

    def test_run_phase_timeout(self):
        """Test phase timeout enforcement."""
        registry = PhaseRegistry()

        def slow_handler():
            time.sleep(2)

        phase = Phase(
            phase_id="slow",
            name="Slow",
            handler=slow_handler,
            timeout_seconds=0.1,
        )
        registry.register(phase)

        result = registry.run_phase("slow")

        assert result.status == PhaseStatus.FAILED
        assert "timeout" in result.error.lower()

    def test_phase_duration_measured(self):
        """Test that phase duration is measured."""
        registry = PhaseRegistry()

        def handler():
            time.sleep(0.1)

        phase = Phase(
            phase_id="test",
            name="Test",
            handler=handler,
        )
        registry.register(phase)

        result = registry.run_phase("test")

        assert result.duration_ms >= 100  # At least 100ms

    def test_rollback_on_phase_failure(self):
        """Test rollback when a phase fails."""
        registry = PhaseRegistry()
        executed = []
        rolled_back = []

        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: executed.append(1),
            rollback_handler=lambda: rolled_back.append(1),
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: (_ for _ in ()).throw(RuntimeError("Fail")),
            rollback_handler=lambda: rolled_back.append(2),
        ))

        registry.run_all()

        # Phase 1 executed
        assert 1 in executed
        # Phase 1 should be rolled back
        assert 1 in rolled_back

    def test_topological_sort(self):
        """Test topological sorting of phases."""
        registry = PhaseRegistry()

        # Create chain: phase_1 -> phase_2 -> phase_3
        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: None,
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: None,
            dependencies=["phase_1"],
        )).register(Phase(
            phase_id="phase_3",
            name="Phase 3",
            handler=lambda: None,
            dependencies=["phase_2"],
        ))

        order = registry._topological_sort()

        # phase_1 should come before phase_2, phase_2 before phase_3
        assert order.index("phase_1") < order.index("phase_2")
        assert order.index("phase_2") < order.index("phase_3")

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        registry = PhaseRegistry()

        # Create circular: phase_1 -> phase_2 -> phase_1
        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: None,
            dependencies=["phase_2"],
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: None,
            dependencies=["phase_1"],
        ))

        order = registry._topological_sort()

        # Should return empty list on circular dependency
        assert order == []

    def test_event_log(self):
        """Test that events are logged."""
        registry = PhaseRegistry()

        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: None,
        )
        registry.register(phase)
        registry.run_phase("test")

        events = registry.get_event_log()

        # Should have phase_start and phase_complete events
        event_types = [e["event_type"] for e in events]
        assert "phase_start" in event_types
        assert "phase_complete" in event_types

    def test_correlation_id_tracking(self):
        """Test that correlation IDs are tracked across phases."""
        registry = PhaseRegistry()

        phase = Phase(
            phase_id="test",
            name="Test",
            handler=lambda: None,
        )
        registry.register(phase)

        test_correlation_id = "test-correlation-123"
        registry.run_phase("test", correlation_id=test_correlation_id)

        assert registry.correlation_id == test_correlation_id

        events = registry.get_event_log()
        for event in events:
            assert event["correlation_id"] == test_correlation_id


class TestBootstrapExecution:
    """Test full bootstrap execution."""

    def test_bootstrap_all_phases_success(self):
        """Test running all phases successfully."""
        registry = PhaseRegistry()
        execution_order = []

        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: execution_order.append(1),
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: execution_order.append(2),
            dependencies=["phase_1"],
        )).register(Phase(
            phase_id="phase_3",
            name="Phase 3",
            handler=lambda: execution_order.append(3),
            dependencies=["phase_2"],
        ))

        success, results = registry.run_all()

        assert success
        assert len(results) == 3
        assert execution_order == [1, 2, 3]

    def test_bootstrap_stop_on_critical_failure(self):
        """Test that critical failure stops bootstrap."""
        registry = PhaseRegistry()
        executed = []

        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: executed.append(1),
            critical=True,
        )).register(Phase(
            phase_id="phase_2",
            name="Phase 2",
            handler=lambda: (_ for _ in ()).throw(RuntimeError("Fail")),
            critical=True,
        )).register(Phase(
            phase_id="phase_3",
            name="Phase 3",
            handler=lambda: executed.append(3),
            critical=False,
        ))

        success, results = registry.run_all(stop_on_critical_failure=True)

        assert not success
        # Phase 3 should not execute if critical phase 2 fails
        assert 3 not in executed

    def test_bootstrap_status(self):
        """Test getting bootstrap status."""
        registry = PhaseRegistry()

        registry.register(Phase(
            phase_id="phase_1",
            name="Phase 1",
            handler=lambda: None,
        ))

        registry.run_all()

        status = registry.get_status()

        assert status["registered_phases"] == 1
        assert status["completed_phases"] == 1
        assert "phases" in status
        assert "phase_1" in status["phases"]

    def test_phase_register_helper(self):
        """Test the register_phase helper function."""
        from actifix.bootstrap_phases import get_registry

        registry = get_registry()
        initial_count = len(registry.phases)

        executed = []

        def handler():
            executed.append(True)

        def rollback():
            executed.append("rollback")

        register_phase(
            phase_id="helper_test",
            name="Helper Test",
            handler=handler,
            rollback_handler=rollback,
            dependencies=[],
            timeout_seconds=10.0,
            critical=False,
        )

        # Phase should be registered
        assert "helper_test" in registry.phases

    def test_bootstrap_helper(self):
        """Test the bootstrap helper function."""
        from actifix.bootstrap_phases import get_registry

        registry = get_registry()
        registry.phases.clear()
        registry.results.clear()

        executed = []

        register_phase(
            phase_id="bootstrap_test",
            name="Bootstrap Test",
            handler=lambda: executed.append(True),
        )

        success = bootstrap()

        assert success
        assert executed == [True]


class TestPhaseIntegration:
    """Integration tests for realistic phase scenarios."""

    def test_multi_phase_system_initialization(self):
        """Test realistic multi-phase system initialization."""
        registry = PhaseRegistry()
        init_log = []

        # Simulate realistic phases
        registry.register(Phase(
            phase_id="config",
            name="Load Configuration",
            handler=lambda: init_log.append("config"),
        )).register(Phase(
            phase_id="database",
            name="Initialize Database",
            handler=lambda: init_log.append("database"),
            dependencies=["config"],
        )).register(Phase(
            phase_id="cache",
            name="Warm Cache",
            handler=lambda: init_log.append("cache"),
            dependencies=["database"],
        )).register(Phase(
            phase_id="health",
            name="Health Check",
            handler=lambda: init_log.append("health"),
            dependencies=["database", "cache"],
        ))

        success, results = registry.run_all()

        assert success
        assert init_log == ["config", "database", "cache", "health"]
        assert len(results) == 4

    def test_rollback_cascade(self):
        """Test that rollback cascades through dependencies."""
        registry = PhaseRegistry()
        rollback_order = []

        def make_rollback(phase_name):
            def rollback():
                rollback_order.append(phase_name)
            return rollback

        registry.register(Phase(
            phase_id="phase_a",
            name="A",
            handler=lambda: None,
            rollback_handler=make_rollback("a"),
        )).register(Phase(
            phase_id="phase_b",
            name="B",
            handler=lambda: None,
            rollback_handler=make_rollback("b"),
            dependencies=["phase_a"],
        )).register(Phase(
            phase_id="phase_c",
            name="C",
            handler=lambda: (_ for _ in ()).throw(RuntimeError("Fail")),
            dependencies=["phase_b"],
        ))

        success, results = registry.run_all()

        assert not success
        # Rollback should happen in reverse order
        assert rollback_order == ["b", "a"]

    def test_event_log_structure(self):
        """Test that event log has proper structure."""
        registry = PhaseRegistry()

        registry.register(Phase(
            phase_id="test",
            name="Test",
            handler=lambda: None,
        ))

        registry.run_all()

        events = registry.get_event_log()

        # Check event structure
        assert len(events) > 0
        for event in events:
            assert "timestamp" in event
            assert "event_type" in event
            assert "source" in event
            assert "correlation_id" in event


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
