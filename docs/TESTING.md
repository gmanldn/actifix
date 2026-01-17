# Actifix Testing Guide

## Overview

Actifix follows a comprehensive testing strategy emphasizing quality-first development, deterministic behavior, and architectural compliance. This guide outlines testing standards, practices, and requirements.

## Testing Philosophy

### Core Principles

1. **Quality Gates Enforcement** - 95%+ test coverage mandatory
2. **Deterministic Execution** - No flaky tests, consistent results
3. **Architecture Compliance** - Tests validate architectural constraints
4. **Fail-Fast Philosophy** - Tests catch issues early in development
5. **Comprehensive Coverage** - Unit, integration, architecture, and health tests

### Quality Standards

- **Test Coverage**: 95%+ minimum for all code
- **Test Execution**: Deterministic, numbered progress tracking
- **Test Reporting**: Yellow inventory, green/red results
- **Test Logs**: Stage summaries in `test_logs/` directory
- **Architecture Validation**: All components pass compliance checks

## Test Categories

### 1. Unit Tests
**Location**: `test/unit/`  
**Purpose**: Test individual component behavior in isolation

```python
# Example unit test
def test_record_error_creates_ticket():
    """Test that record_error creates a valid ticket."""
    entry = record_error(
        message="Test error",
        source="test/test_runner.py:10",
        priority=TicketPriority.P2
    )
    assert entry is not None
    assert entry.message == "Test error"
    assert entry.priority == TicketPriority.P2
```

### 2. Integration Tests
**Location**: `test/integration/`  
**Purpose**: Test component interactions and workflows

```python
# Example integration test
def test_error_flow_end_to_end():
    """Test complete error capture and processing flow."""
    # Capture error
    entry = record_error(message="Integration test", source="test/test_runner.py:20")
    
    # Process ticket
    tickets = get_open_tickets()
    assert len(tickets) > 0
    
    # Mark complete
    mark_ticket_complete(entry.entry_id, "Test completion")
    
    # Verify completion
    completed = get_completed_tickets()
    assert entry.entry_id in [t.entry_id for t in completed]
```

### 3. Architecture Tests
**Location**: `test/architecture/`  
**Purpose**: Validate architectural compliance and constraints

```python
# Example architecture test
def test_module_dependencies():
    """Test that modules respect dependency constraints."""
    violations = validate_module_dependencies()
    assert len(violations) == 0, f"Dependency violations: {violations}"

def test_circular_dependencies():
    """Test that no circular dependencies exist."""
    cycles = detect_circular_dependencies()
    assert len(cycles) == 0, f"Circular dependencies found: {cycles}"
```

### 4. Health Tests
**Location**: `test/health/`  
**Purpose**: Test system monitoring and degradation detection

```python
# Example health test
def test_health_monitoring():
    """Test that health monitoring detects issues."""
    health = get_health()
    assert health.status in ["OK", "WARNING", "ERROR"]
    assert isinstance(health.open_tickets, int)
```

### 5. Performance Tests
**Location**: `test/performance/`  
**Purpose**: Validate performance requirements and benchmarks

```python
# Example performance test
def test_startup_time():
    """Test that system startup completes within 5 seconds."""
    start_time = time.time()
    bootstrap_system()
    startup_time = time.time() - start_time
    assert startup_time < 5.0, f"Startup took {startup_time:.2f}s"
```

## Test Execution

### Running Tests

```bash
# Full test suite with coverage
python test/test_runner.py --coverage

# Quick tests (exclude slow integration tests)
python -m pytest test/ -m "not slow"

# Specific test categories
python -m pytest test/unit/
python -m pytest test/integration/
python -m pytest test/architecture/

# Coverage reporting
python -m pytest test/ --cov=src/actifix --cov-report=html
```

### Test Configuration

```python
# pytest.ini configuration
[tool.pytest.ini_options]
testpaths = ["test"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "architecture: marks tests as architecture validation",
    "performance: marks tests as performance benchmarks"
]
```

### Coverage Requirements

```bash
# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["src/actifix"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/conftest.py"
]

[tool.coverage.report]
fail_under = 95
show_missing = true
skip_covered = false
```

## Test Structure

### Directory Layout

```
test/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests
│   ├── test_bootstrap.py
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_logging.py
│   ├── test_raise_af.py
│   └── test_quarantine.py
├── integration/                # Integration tests
│   ├── test_error_flow.py
│   ├── test_system_startup.py
│   └── test_state_recovery.py
├── architecture/               # Architecture compliance tests
│   ├── test_module_contracts.py
│   ├── test_dependency_compliance.py
│   └── test_architectural_rules.py
├── health/                     # Health monitoring tests
│   ├── test_health_checks.py
│   └── test_degradation_detection.py
├── performance/                # Performance benchmarks
│   ├── test_startup_performance.py
│   └── test_throughput_benchmarks.py
└── fixtures/                   # Test data and fixtures
    ├── sample_configs.py
    ├── mock_data.py
    └── test_helpers.py
```

### Test Fixtures

```python
# conftest.py - Shared fixtures
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_actifix_dir():
    """Provide a temporary directory for actifix state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        "capture_enabled": True,
        "data_dir": "./test_actifix",
        "log_level": "DEBUG"
    }

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    import os
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
```

## Test Requirements

### All Tests Must

1. **Be Deterministic**: Same input produces same output
2. **Clean Up**: Restore state after execution
3. **Use Fixtures**: Proper setup and teardown
4. **Test Edge Cases**: Both positive and negative scenarios
5. **Include Documentation**: Clear docstrings explaining purpose

### Test Naming Convention

```python
# Good test names
def test_record_error_with_valid_input_creates_ticket():
    """Test that record_error creates ticket with valid input."""
    pass

def test_record_error_with_invalid_priority_raises_error():
    """Test that record_error raises error with invalid priority."""
    pass

def test_get_open_tickets_returns_sorted_by_priority():
    """Test that get_open_tickets returns tickets sorted by priority."""
    pass
```

## Test Cycle Reporting

### Yellow Inventory System

The test system implements a "yellow inventory" approach:

1. **Test Discovery**: Enumerate all tests before execution
2. **Progress Tracking**: Numbered execution with real-time updates
3. **Result Reporting**: Green (pass) / Red (fail) with clear indicators
4. **Stage Summaries**: Detailed logs in `test_logs/` directory

### Test Logs Structure

```
test_logs/
├── test_cycle_YYYYMMDD_HHMMSS.log    # Complete test cycle log
├── test_inventory.json               # Test discovery results
├── test_progress.log                 # Real-time progress updates
├── coverage_report.html              # Coverage analysis
└── stage_summaries/                  # Per-stage detailed logs
    ├── unit_tests.log
    ├── integration_tests.log
    ├── architecture_tests.log
    └── performance_tests.log
```

### Example Test Output

```
🔍 Test Discovery: Found 247 tests
📋 Test Inventory: 
   - Unit Tests: 156 tests
   - Integration Tests: 45 tests  
   - Architecture Tests: 28 tests
   - Health Tests: 12 tests
   - Performance Tests: 6 tests

🚀 Starting Test Execution...

✅ [001/247] test_bootstrap_initialization_success
✅ [002/247] test_config_validation_with_valid_input
❌ [003/247] test_error_capture_with_invalid_source
✅ [004/247] test_health_check_returns_status
...

📊 Test Results Summary:
   - Passed: 245/247 (99.2%)
   - Failed: 2/247 (0.8%)
   - Coverage: 96.3% (Target: 95%+)
   - Duration: 45.2 seconds

🎯 Coverage Analysis:
   - src/actifix/bootstrap.py: 98.5%
   - src/actifix/raise_af.py: 97.2%
   - src/actifix/health.py: 94.8%
   - Overall: 96.3% ✅
```

## Continuous Integration

### Pre-Commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests
python test/test_runner.py --coverage
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi

# Check coverage
coverage report --fail-under=95
if [ $? -ne 0 ]; then
    echo "❌ Coverage below 95%. Commit aborted."
    exit 1
fi

# Architecture validation
python -m actifix.testing --validate-architecture
if [ $? -ne 0 ]; then
    echo "❌ Architecture validation failed. Commit aborted."
    exit 1
fi

echo "✅ All quality gates passed. Proceeding with commit."
```

### CI Pipeline

```yaml
# GitHub Actions example
name: Quality Gates
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install -e ".[dev]"
    
    - name: Run tests with coverage
      run: python test/test_runner.py --coverage
    
    - name: Validate architecture
      run: python -m actifix.testing --validate-architecture
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

## Debugging Tests

### Debug Mode

```bash
# Enable debug logging
export ACTIFIX_LOG_LEVEL=DEBUG
python -m pytest test/ -v -s

# Run specific test with debugging
python -m pytest test/unit/test_raise_af.py::test_record_error -v -s --pdb
```

### Test Isolation

```python
# Isolate tests with temporary directories
def test_with_isolation(tmp_path):
    """Test with isolated filesystem."""
    test_dir = tmp_path / "actifix_test"
    test_dir.mkdir()
    
    # Set environment for test
    os.environ["ACTIFIX_DATA_DIR"] = str(test_dir)
    
    # Run test logic
    result = some_function()
    
    # Verify results
    assert result is not None
```

## Best Practices

### Writing Good Tests

1. **Arrange-Act-Assert**: Clear test structure
2. **Single Responsibility**: One concept per test
3. **Descriptive Names**: Clear test purpose
4. **Independent Tests**: No test dependencies
5. **Fast Execution**: Optimize for speed

### Test Data Management

```python
# Use factories for test data
class TicketFactory:
    @staticmethod
    def create_ticket(**kwargs):
        defaults = {
            "message": "Test error",
            "source": "test/test_runner.py:10",
            "priority": TicketPriority.P2
        }
        defaults.update(kwargs)
        return record_error(**defaults)

# Use in tests
def test_ticket_processing():
    ticket = TicketFactory.create_ticket(priority=TicketPriority.P1)
    # Test logic here
```

### Mock Usage

```python
# Mock external dependencies
@patch('actifix.ai_client.call_claude_api')
def test_ai_integration(mock_claude):
    mock_claude.return_value = {"status": "success", "fix": "solution"}
    
    result = process_ticket_with_ai(ticket)
    
    assert result.status == "completed"
    mock_claude.assert_called_once()
```

## Troubleshooting

### Common Issues

1. **Flaky Tests**: Use proper fixtures and cleanup
2. **Slow Tests**: Mark with `@pytest.mark.slow`
3. **Environment Issues**: Use isolated test environments
4. **Coverage Gaps**: Add tests for uncovered code paths

### Test Debugging

```bash
# Run tests with verbose output
python -m pytest test/ -v

# Run specific test file
python -m pytest test/unit/test_raise_af.py -v

# Run tests matching pattern
python -m pytest test/ -k "test_error" -v

# Run tests with debugger
python -m pytest test/ --pdb
```

---

This testing guide ensures comprehensive quality assurance for the Actifix framework while maintaining the high standards required for production-grade error management systems.
