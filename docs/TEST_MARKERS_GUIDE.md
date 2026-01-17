# Test Markers and Performance Optimization Guide

## Overview

This guide explains how to use pytest markers to categorize and optimize test execution in Actifix.

## Available Markers

### Performance Markers

- **`@pytest.mark.unit`** - Fast unit tests with minimal dependencies (< 100ms)
  - No database access
  - No external services
  - No file I/O
  - Example: Pure function tests, mock-based tests

- **`@pytest.mark.integration`** - Multi-component tests (100ms - 1s)
  - Tests that combine multiple modules
  - May access database
  - Example: API endpoint tests, service layer tests

- **`@pytest.mark.slow`** - Slow tests that may take > 1s
  - Database-heavy tests
  - External service calls
  - Large fixture setup
  - Can be excluded during fast CI runs

- **`@pytest.mark.very_slow`** - Tests known to take > 5 seconds
  - Stress tests
  - Full integration flows
  - Large data processing
  - Should run in separate CI pipeline

### Functional Markers

- **`@pytest.mark.db`** - Tests that perform database operations
  - Likely to be slow
  - Should be profiled for optimization
  - Example: Repository tests, persistence tests

- **`@pytest.mark.api`** - API endpoint tests
  - Example: Flask endpoint tests, HTTP tests

- **`@pytest.mark.security`** - Security-related tests
  - Authentication tests
  - Authorization tests
  - Encryption tests

- **`@pytest.mark.architecture`** - Architecture validation tests
  - Import structure tests
  - Module dependency tests
  - Design pattern compliance

- **`@pytest.mark.concurrent`** - Concurrent/threading tests
  - Threading tests
  - Race condition tests
  - Lock tests

### Operation-Specific Markers

- **`@pytest.mark.io`** - File I/O tests
- **`@pytest.mark.network`** - Network/external service tests
- **`@pytest.mark.performance`** - Performance or benchmark tests

## How to Mark Tests

### Basic Usage

```python
import pytest

@pytest.mark.unit
def test_simple_calculation():
    """Fast unit test."""
    assert 1 + 1 == 2

@pytest.mark.db
@pytest.mark.slow
def test_database_operation(db):
    """Slow database test."""
    # Database operations
    pass

@pytest.mark.integration
@pytest.mark.api
def test_api_endpoint(client):
    """API integration test."""
    response = client.get('/api/ping')
    assert response.status_code == 200
```

### Multiple Markers

```python
@pytest.mark.db
@pytest.mark.slow
@pytest.mark.integration
def test_complex_workflow():
    """Test that uses multiple aspects."""
    pass
```

## Running Tests with Markers

### Run only fast tests
```bash
pytest -m "not slow"
```

### Run only unit tests
```bash
pytest -m unit
```

### Run only database tests
```bash
pytest -m db
```

### Run everything except very slow tests
```bash
pytest -m "not very_slow"
```

### Combine markers (AND logic)
```bash
pytest -m "db and slow"
```

### Combine markers (OR logic)
```bash
pytest -m "unit or api"
```

## Performance Optimization Workflow

### 1. Identify Slow Tests
```bash
pytest --durations=30
```

Look for tests taking > 1 second.

### 2. Mark Slow Tests
Add appropriate markers to tests identified in step 1:
```python
@pytest.mark.slow
@pytest.mark.db
def test_something_slow():
    pass
```

### 3. Run Fast Tests Only
```bash
pytest -m "not slow" -v
```

### 4. Analyze Database Usage
Tests marked with `@pytest.mark.db` appear in the database profiler report.

### 5. Optimize
- Batch database operations
- Reduce fixture setup overhead
- Use in-memory databases for tests
- Reduce external service calls

## Performance Target Goals

- **Unit tests**: < 100ms each, runs in < 5 seconds total
- **Integration tests**: < 1s each, runs in < 30 seconds total
- **Slow/Database tests**: < 5s each
- **Full test suite**: < 2 minutes

## Common Patterns

### Database Tests
```python
@pytest.mark.db
@pytest.mark.slow
@pytest.mark.integration
def test_ticket_creation(clean_db):
    """Test creates ticket in database."""
    # Setup
    repo = get_ticket_repository()

    # Action
    ticket = repo.create_ticket(entry)

    # Assert
    assert ticket is not None
```

### API Tests
```python
@pytest.mark.api
@pytest.mark.integration
def test_api_endpoint(client):
    """Test API endpoint."""
    response = client.get('/api/tickets')
    assert response.status_code == 200
```

### Unit Tests
```python
@pytest.mark.unit
def test_validation():
    """Pure unit test, no fixtures needed."""
    assert validate_email("test@example.com") is True
    assert validate_email("invalid") is False
```

### Concurrent Tests
```python
@pytest.mark.concurrent
@pytest.mark.slow
def test_thread_safety():
    """Test concurrent access."""
    # Threading test
    pass
```

## Troubleshooting

### Test not running with marker
- Ensure marker is registered in `pytest.ini` or `conftest.py`
- Check spelling of marker name
- Verify test has correct syntax: `@pytest.mark.marker_name`

### Test takes longer than expected
- Check if it should be marked as `@pytest.mark.slow`
- Review database operations
- Consider reducing fixture setup

### Performance regressed
- Run `pytest --durations=30` to identify new slow tests
- Check git diff for recent changes
- Profile database operations with `database_profiler`

## Automated Marker Suggestions

Run the marker suggestion script to identify tests that should be marked:

```bash
python scripts/suggest_test_markers.py
```

This script analyzes:
- Test execution time
- Database access patterns
- External service calls
- Fixture complexity

And suggests appropriate markers.
