# Test Performance Optimization

This guide explains how to keep Actifix test cycles fast without sacrificing coverage or quality gates.

## Quick wins
- Use `python3 test.py --fast-coverage` for rapid feedback.
- Mark slow tests with `@pytest.mark.slow`.
- Install `pytest-xdist` for parallel runs.

## Fast coverage mode
`test.py --fast-coverage`:
- Runs system tests and pytest.
- Skips tests marked `slow`.
- Uses pytest-xdist automatically if available.

```bash
python3 test.py --fast-coverage
```

## Full coverage mode
```bash
python3 test.py --coverage
```

## Parallel execution
```bash
python3 -m pip install pytest-xdist
```

Control workers:
```bash
export ACTIFIX_XDIST_WORKERS=4
export ACTIFIX_DISABLE_XDIST=1  # disable
```

## Identify slow tests
```bash
python3 -m pytest test/ --durations=30
```

## Suggested workflow
1. Run `python3 test.py --fast-coverage` while iterating.
2. Run `python3 test.py --coverage` before commit.
3. Profile slow tests weekly with `pytest --durations=30`.

## Optimization tips
- Reduce database setup overhead in fixtures.
- Use smaller fixtures for `unit` tests.
- Mark expensive tests as `slow` or `very_slow`.
- Avoid repeated initialization in tight loops.
