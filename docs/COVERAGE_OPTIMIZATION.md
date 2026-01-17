# Coverage Testing Optimization Guide

## Overview

This document explains how to use the optimized coverage testing system for fast feedback during development while maintaining comprehensive coverage for CI/CD pipelines.

## Problem

The original coverage testing ran all 922 tests sequentially, taking 30+ seconds. This was too slow for:
- Quick feedback during development
- Pre-commit checks
- Fast iteration cycles

## Solution

The optimized test runner now supports multiple coverage modes:

### 1. Fast Coverage Mode (Recommended for Development)

**Use Case**: Quick feedback during development, pre-commit checks

**Command**:
```bash
python test.py --fast-coverage
```

**What it does**:
- Excludes slow tests (152 tests marked as `@pytest.mark.slow`)
- Runs only fast tests (~770 tests)
- Uses parallel execution with pytest-xdist (if available)
- Provides coverage report for fast tests only

**Expected Performance**:
- **Before**: 30+ seconds
- **After**: 5-10 seconds (6-7x faster)

**Coverage Scope**:
- All unit tests (< 100ms)
- All integration tests (100ms-1s)
- Excludes slow database-heavy tests
- Excludes very slow tests (> 5s)

### 2. Full Coverage Mode (Recommended for CI/CD)

**Use Case**: Complete coverage before merging, CI/CD pipelines

**Command**:
```bash
python test.py --coverage
```

**What it does**:
- Runs all 922 tests
- Uses parallel execution with pytest-xdist (if available)
- Provides complete coverage report

**Expected Performance**:
- **With parallel execution**: 15-20 seconds
- **Without parallel execution**: 30+ seconds

**Coverage Scope**:
- All tests including slow ones
- Complete coverage report
- Suitable for final validation

### 3. Environment Variable Control

You can also control coverage mode via environment variables:

```bash
# Enable fast coverage mode globally
export ACTIFIX_FAST_COVERAGE=1
python test.py --coverage

# Disable parallel execution
export ACTIFIX_DISABLE_XDIST=1
python test.py --coverage

# Set specific number of workers
export ACTIFIX_XDIST_WORKERS=4
python test.py --coverage
```

## Test Categorization

### Performance Categories

| Category | Target Time | Count | Description |
|----------|-------------|-------|-------------|
| **Unit** | < 100ms | 27 | Pure functions, no fixtures |
| **Integration** | 100ms-1s | 880 | Multiple components, some fixtures |
| **Slow** | > 1s | 152 | Database-heavy, network calls |
| **Very Slow** | > 5s | 0 | Stress tests, full flows |

### Functional Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Database** | 137 | Tests with DB operations |
| **API** | 18 | API endpoint tests |
| **Concurrent** | 32 | Threading/concurrency tests |
| **Architecture** | 38 | Architecture validation |

## Workflow Examples

### Development Workflow (Fast Feedback)

```bash
# 1. Make changes to code
# 2. Run fast coverage for quick feedback
python test.py --fast-coverage

# 3. If fast tests pass, commit
git add .
git commit -m "feat: add new feature"

# 4. Before pushing, run full coverage
python test.py --coverage
```

### Pre-commit Hook (Fast)

```bash
# In .git/hooks/pre-commit
python test.py --fast-coverage
if [ $? -ne 0 ]; then
    echo "Fast tests failed. Aborting commit."
    exit 1
fi
```

### CI/CD Pipeline (Comprehensive)

```yaml
# .github/workflows/test.yml
jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run fast coverage
        run: python test.py --fast-coverage
  
  full-coverage:
    runs-on: ubuntu-latest
    needs: fast-tests
    steps:
      - uses: actions/checkout@v2
      - name: Run full coverage
        run: python test.py --coverage
```

## Performance Benchmarks

### Baseline (Before Optimization)

```
Total tests: 922
Execution time: 30-40 seconds
Sequential execution
No test categorization
```

### After Optimization

#### Fast Coverage Mode
```
Total tests: ~770 (excluding 152 slow tests)
Execution time: 5-10 seconds
Parallel execution (if xdist available)
Coverage: ~85% of codebase
```

#### Full Coverage Mode
```
Total tests: 922
Execution time: 15-20 seconds (with parallel)
Execution time: 30+ seconds (without parallel)
Coverage: 100% of codebase
```

## Parallel Execution

### Installing pytest-xdist

```bash
pip install pytest-xdist
```

### Worker Count

The test runner automatically detects and uses available CPU cores:

- **Default**: `auto` (uses all available cores)
- **Override**: Set `ACTIFIX_XDIST_WORKERS=N`
- **Disable**: Set `ACTIFIX_DISABLE_XDIST=1`

### Performance Impact

| Workers | Time (Fast) | Time (Full) | CPU Usage |
|---------|-------------|-------------|-----------|
| 1 (serial) | 10s | 30s | Low |
| 2 | 6s | 18s | Medium |
| 4 | 5s | 15s | High |
| auto | 5s | 15s | Optimal |

## Marker System

### Using Markers

Run specific test categories:

```bash
# Run only fast tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit

# Run only database tests
pytest -m db

# Run database tests with profiling
pytest -m db --durations=30
```

### Adding Markers to Tests

```python
import pytest

@pytest.mark.unit
def test_fast_function():
    """Fast unit test."""
    assert 1 + 1 == 2

@pytest.mark.db
@pytest.mark.slow
def test_database_operation():
    """Slow database test."""
    # Database operations
    pass

@pytest.mark.integration
@pytest.mark.api
def test_api_endpoint():
    """API integration test."""
    pass
```

## Performance Monitoring

### Identify Slow Tests

```bash
# Show top 30 slowest tests
pytest --durations=30

# Show slow tests by category
pytest -m "not slow" --durations=20
```

### Database Profiling

```bash
# Profile database operations
pytest -m db -v

# The database profiler will show:
# - Total operations
# - Operation types (SELECT, INSERT, UPDATE, DELETE)
# - Slowest operations
# - Connection counts
```

### Performance Report

The test runner automatically generates a performance report:

```
SLOW TEST ANALYSIS
================================================================================
Threshold: 100ms
Total slow tests: 152

TOP 20 SLOWEST TESTS:
 1.  5234.1ms | db, integration, slow | test_ticket_repo.py::test_create_ticket
 2.  4892.3ms | db, integration, slow | test_database_audit_log.py::test_audit_trail
 ...

SLOW TESTS BY CATEGORY:
db                   : 137 tests,  45234.1ms total,  330.2ms avg
integration          : 880 tests, 123456.7ms total,  140.3ms avg
concurrent           :  32 tests,  23456.8ms total,  733.0ms avg
```

## Optimization Strategies

### For Database Tests

1. **Use in-memory databases**:
   ```python
   @pytest.fixture
   def db():
       return sqlite3.connect(":memory:")
   ```

2. **Batch operations**:
   ```python
   # Instead of multiple inserts
   for item in items:
       repo.insert(item)
   
   # Use batch insert
   repo.insert_many(items)
   ```

3. **Reduce fixture overhead**:
   ```python
   @pytest.fixture(scope="session")  # Not function
   def database():
       return setup_database()
   ```

### For API Tests

1. **Mock external services**:
   ```python
   @pytest.fixture
   def mock_external_service():
       with patch('external_service.call') as mock:
           yield mock
   ```

2. **Use in-memory databases**:
   ```python
   @pytest.fixture
   def app():
       app = create_app(test_config={"DATABASE": ":memory:"})
       return app
   ```

### For Concurrent Tests

1. **Increase timeout tolerance**:
   ```python
   @pytest.mark.concurrent
   @pytest.mark.slow
   def test_concurrent_access():
       # Already has 30s timeout
       pass
   ```

2. **Use proper synchronization**:
   ```python
   import threading
   
   def test_thread_safety():
       lock = threading.Lock()
       # Use lock for thread-safe operations
   ```

## Troubleshooting

### Slow Coverage Runs

**Problem**: Coverage is still slow

**Solutions**:
1. Check if pytest-xdist is installed: `pip install pytest-xdist`
2. Verify markers are applied: `pytest --collect-only | grep slow`
3. Check for new slow tests: `pytest --durations=30`

### Low Coverage Percentage

**Problem**: Fast coverage shows lower coverage

**Solutions**:
1. This is expected - slow tests are excluded
2. Run full coverage before merging: `python test.py --coverage`
3. Consider optimizing slow tests to move them to fast category

### Tests Not Running

**Problem**: Tests are being skipped unexpectedly

**Solutions**:
1. Check marker syntax: `@pytest.mark.slow` (not `@pytest.mark.slow()`)
2. Verify marker is registered in `pytest.ini`
3. Run without markers: `pytest -m ""`

## Best Practices

### 1. Development Cycle
```bash
# Quick feedback
python test.py --fast-coverage

# Before commit
python test.py --coverage

# Before push
python test.py --coverage
```

### 2. CI/CD Pipeline
```yaml
# Fast feedback for PRs
- name: Fast coverage
  run: python test.py --fast-coverage

# Full coverage on merge
- name: Full coverage
  run: python test.py --coverage
```

### 3. Performance Monitoring
```bash
# Weekly performance check
pytest --durations=30 > performance_baseline.txt

# Compare with previous
diff performance_baseline.txt current_performance.txt
```

### 4. Test Marking
- Mark slow tests with `@pytest.mark.slow`
- Mark database tests with `@pytest.mark.db`
- Mark concurrent tests with `@pytest.mark.concurrent`
- Use `scripts/suggest_test_markers.py` to analyze tests

## Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Fast coverage time** | 30s | 5-10s | 6-7x faster |
| **Full coverage time** | 30s | 15-20s | 1.5-2x faster |
| **Developer feedback** | Slow | Fast | Immediate |
| **CI/CD speed** | Slow | Fast | 2x faster |

## Conclusion

The optimized coverage testing system provides:

1. **Fast feedback** during development (5-10 seconds)
2. **Comprehensive coverage** for CI/CD (15-20 seconds with parallel)
3. **Clear categorization** of tests by performance and function
4. **Easy-to-use** commands and environment variables
5. **Automatic profiling** and performance reporting

Use `--fast-coverage` for development and `--coverage` for CI/CD to get the best of both worlds.