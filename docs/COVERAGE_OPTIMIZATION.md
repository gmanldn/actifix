# Coverage Optimization Guide

This guide explains how to run coverage quickly while keeping quality gates intact.

## Commands
```bash
# Fast coverage (skips slow tests)
python3 test.py --fast-coverage

# Full coverage
python3 test.py --coverage
```

## Environment variables
```bash
export ACTIFIX_FAST_COVERAGE=1  # use fast coverage when --coverage is set
export ACTIFIX_DISABLE_XDIST=1  # disable pytest-xdist
export ACTIFIX_XDIST_WORKERS=4  # set worker count
```

## What fast coverage does
- Excludes tests marked `slow`.
- Enables pytest-xdist when available.
- Preserves system tests via `actifix.testing`.

## Recommended workflow
1. Use `--fast-coverage` while iterating.
2. Run `--coverage` before commit.
3. Investigate slow tests with:
   ```bash
   python3 -m pytest test/ --durations=30
   ```

## Related docs
- `docs/TESTING.md`
- `docs/TEST_PERFORMANCE_OPTIMIZATION.md`
- `docs/TEST_MARKERS_GUIDE.md`
