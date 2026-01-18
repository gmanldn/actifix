# Test Markers Guide

Actifix uses pytest markers to keep test runs fast and intentional. Markers are defined in `pytest.ini` and enforced via `--strict-markers`.

## Marker taxonomy
Performance markers:
- `unit`: fast, isolated tests (< 100ms).
- `integration`: multi-component tests (100ms to 1s).
- `slow`: tests that exceed 1s.
- `very_slow`: tests that exceed 5s.

Functional markers:
- `db`: database access.
- `api`: API or HTTP interactions.
- `security`: auth, secrets, or security-sensitive paths.
- `architecture`: dependency or contract validation.
- `concurrent`: threading or locking.
- `io`: file IO.
- `network`: network usage.
- `performance`: benchmarks and profiling.

## How to apply markers
```python
import pytest

@pytest.mark.unit
def test_fast_logic():
    assert 1 + 1 == 2

@pytest.mark.db
@pytest.mark.slow
def test_repository_roundtrip():
    ...
```

## Running marker subsets
```bash
# Exclude slow tests
python3 -m pytest test/ -m "not slow"

# Unit tests only
python3 -m pytest test/ -m unit

# Database tests only
python3 -m pytest test/ -m db

# Combined filters
python3 -m pytest test/ -m "db and slow"
```

## Discover markers
```bash
python3 -m pytest --markers
```

## Performance hygiene
- Mark any test that regularly exceeds 1s as `slow`.
- Use `very_slow` for stress or soak tests.
- Pair functional markers (e.g., `db`, `api`) with performance markers when applicable.

## Helper scripts
Marker suggestion tooling exists in `scripts/suggest_test_markers.py` and `scripts/apply_test_markers.py`.
