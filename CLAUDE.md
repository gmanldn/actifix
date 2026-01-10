# Coding Agent Instructions (AGENTS/CLAUDE/GPT)

This file provides essential context and rules for all coding agents working with the Actifix codebase.
It is synchronized across `AGENTS.md`, `CLAUDE.md`, and `GPT.md`.

---

## MANDATORY REQUIREMENTS

### 1. Every Completed Task MUST Be Committed and Pushed

**CRITICAL: Always make a branch, do the work in the ticket, commit, merge to develop, then delete the branch at all times**

**CRITICAL: All work must be committed to the `develop` branch and pushed before a task is considered complete.**

```bash
# Standard commit workflow (REQUIRED after every task completion)
git status
git add -A
git commit -m "type(scope): description"
git push origin develop
```

**Commit message convention:**

- `feat(scope):` - New features
- `fix(scope):` - Bug fixes
- `refactor(scope):` - Code refactoring
- `test(scope):` - Test additions/changes
- `docs(scope):` - Documentation changes
- `chore(scope):` - Maintenance tasks
- `perf(scope):` - Performance improvements

### 2. Full Regression and Function Tests Required

**CRITICAL: Every task must include running and passing the full test suite.**

```bash
# REQUIRED before committing any changes
python test.py                    # Full test suite with architecture validation
python test.py --coverage         # Must maintain 95%+ coverage
```

**Test requirements:**

- All 2,550+ tests must pass (0 failures allowed)
- Coverage must remain at or above 95%
- No regressions in existing functionality
- New code must have comprehensive test coverage
- **EVERYTHING must be tested** - No exceptions. Every new function, class, or feature requires tests.
- **Full-cycle visibility is mandatory:** `test.py` must print the yellow inventory of total tests (with counts per type) before running anything, then show numbered green/red results with overall progress for every test via `pokertool.testing.test_cycle_reporter`. Stage summaries land in `test_logs/test_cycle_*.json` and every failure is logged to the master logger (`LogCategory.TESTING`). If the executed count ever differs from the collected plan, the run must fail.

**Quick validation (for minor changes):**
```bash
python test.py --quick           # Fast subset for rapid feedback
```

### 3. NO Implementation Plan Documents - Use TODO.md Only

**CRITICAL: NEVER create standalone planning documents like `IMPLEMENTATION_PLAN.md`, `PLAN.md`, `ROADMAP.md`, or similar files.**

All planning work MUST go into `docs/TODO.md` with full details:

- Use `python new_task.py` to add tasks programmatically
- Include detailed subtasks and acceptance criteria in TODO.md
- Keep all planning centralized in one location

**FORBIDDEN files:**

- `IMPLEMENTATION_PLAN.md`
- `PLAN.md`
- `ROADMAP.md`
- `DESIGN.md`
- Any `*_PLAN.md` or `*_ROADMAP.md` files

### 4. Version Increment, Branch, Commit, and Push After EVERY Change

**CRITICAL: After EVERY commit, you MUST complete the full workflow:**

1. **Increment version** in the appropriate version file
2. **Create/use a feature branch** for the work
3. **Commit with a descriptive message** following conventions
4. **Push immediately** - no local-only commits

```bash
# MANDATORY workflow after every change
# 1. Increment version (check pyproject.toml or version file)
# 2. Create branch if needed
git checkout -b feature/your-feature-name

# 3. Stage and commit
git add -A
git commit -m "type(scope): description"

# 4. Push IMMEDIATELY
git push origin <branch-name>
```

**No exceptions. Every commit must be pushed. Full stop.**

### 5. ACTIFIX Error Tracking System (MANDATORY)

**CRITICAL: All errors MUST flow through the ACTIFIX system. Manual error handling without ACTIFIX integration is prohibited.**

#### What is ACTIFIX?

ACTIFIX (Automatic Code Issue Tracking and Fixing) automatically:

1. Captures errors with full context (stack traces, file context, system state)
2. Creates prioritized tickets (P0-P4)
3. Prevents duplicate tickets via hash-based deduplication
4. Dispatches fixes to Claude with 200k context window
5. Validates fixes (tests pass, version incremented, committed, pushed)

#### ACTIFIX Workflow

```
Error → RaiseAF.py → ACTIFIX-LIST.md → DoAF.py → Claude Fix → Validation → Commit
```

#### ACTIFIX Rules

1. **NEVER bypass ACTIFIX** - All errors must create tickets
2. **NEVER manually create error handling** without ACTIFIX integration
3. **NEVER process tickets without validation** - tests must pass
4. **NEVER skip commit protection** - version, commit, push all required
5. **NEVER recreate past fixes** - duplicate guards prevent loops

#### ACTIFIX Files

| File | Purpose |
|------|---------|
| `Actifix/RaiseAF.py` | Records errors as tickets |
| `Actifix/DoAF.py` | Processes tickets, dispatches to Claude |
| `Actifix/ACTIFIX-LIST.md` | Active/completed tickets |
| `Actifix/ACTIFIX.md` | Last 20 errors rollup |
| `Actifix/AFLog.txt` | Detailed audit log |

#### ACTIFIX Commands

```bash
# Check ACTIFIX health
python -c "from Actifix.RaiseAF import ensure_scaffold; ensure_scaffold('.')"

# Record an error manually (rare - usually automatic)
python -c "from Actifix.RaiseAF import record_error; record_error('msg', 'src.py', 'run-1')"

# Process pending tickets
python -c "from Actifix.DoAF import run_doaf; run_doaf('Fix applied')"
```

#### Loop Prevention

ACTIFIX prevents loops and duplicate work through:

- **Duplicate Guard**: Hash-based ID prevents same error creating multiple tickets
- **Completed Tracking**: Processed tickets moved to "Completed Items" section
- **Audit Log**: AFLog.txt tracks all ticket lifecycle events
- **Pre-commit Check**: Validates no orphaned or stale tickets

**See:** [ADR-026](docs/decisions/ADR-026-automatic-error-tracking-actifix.md) for complete architecture.

---

### 6. Agent Instruction Files Must Stay in Sync

**CRITICAL: `AGENTS.md`, `CLAUDE.md`, and `GPT.md` must always have identical content.**

- Update all three files together.
- Tests will fail if any differences are detected.
- Do not make one-off edits to a single file.

## Application Startup

**THE APP MUST ALWAYS BE STARTED FROM THE PROJECT ROOT USING `start.py`**

```bash
# CORRECT - From project root
python3 start.py

# WRONG - Do not use these methods
cd scripts && python start.py
python scripts/start.py
```

**Why this matters:**

- Sets up correct PYTHONPATH
- Ensures all imports resolve correctly
- Initializes logging and configuration properly
- Cleans up old processes before starting

**After startup:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:5001
- Backend Status: http://localhost:3000/backend

---

## Project Structure

```
pokertool/
├── start.py                    # MAIN ENTRY POINT - Always use this!
├── test.py                     # Test runner with architecture validation
├── src/pokertool/              # Python source code (core engine)
├── pokertool-frontend/         # React TypeScript frontend
├── tests/                      # Pytest test suite (2,550+ tests)
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
│   ├── DEVELOPMENT.md          # Development methodology
│   ├── TESTING.md              # Testing guide
│   ├── MONITORING.md           # Health checks and logging
│   ├── DATABASE.md             # Database configuration
│   └── INSTALLATION.md         # Installation guide
└── logs/                       # ALL logs go here (centralized)
```

---

## Development Workflow

### Before Making Changes

1. **Read existing code** - Never modify code you haven't read
2. **Check TODO.md** - Use `python new_task.py` to create tasks (no manual edits)
3. **Review ADRs** - Check `docs/decisions/` for architectural context
4. **Understand patterns** - Follow existing code conventions

### Making Changes

1. **Write tests first** when adding new functionality
2. **Maintain 95%+ coverage** - Use `python test.py --coverage` to verify
3. **Follow existing patterns** - Don't introduce new conventions without ADRs
4. **Document decisions** - Create ADRs for significant architectural changes

### After Making Changes

1. **Run full test suite:**

   ```bash
   ```bash
   python test.py
   ```

2. **Verify coverage:**

   ```bash
   ```bash
   python test.py --coverage
   ```

3. **Commit and push:**

   ```bash
   ```bash
   git add -A
   git commit -m "type(scope): description"
   git push origin develop
   ```

---

## Testing Guidelines

### Test Commands

```bash
# Full pipeline (REQUIRED before every commit)
python test.py

# Quick mode (skip slow tests)
python test.py --quick

# With coverage report
python test.py --coverage

# Specific pattern
pytest tests/ -k <pattern>

# Skip scraper tests (if no live Betfair table)
pytest -m "not scraper"
```

### Test Requirements

- **Unit tests:** Every function with meaningful logic
- **Integration tests:** Component interactions
- **Coverage target:** 95%+ on all code
- **Zero regressions:** All existing tests must pass

### Test File Conventions

- All test files MUST be proper pytest files (no standalone scripts)
- Use `test_*.py` naming convention
- Never use `sys.exit()` in test files
- Mark external dependency tests with `@pytest.mark.xfail` or `@pytest.skip`

---

## Error Checking and Monitoring

### Quick Error Check

```bash
./scripts/check-errors
```

### Primary Log Files

- `logs/errors-and-warnings.log` - **Check this first!** (consolidated errors)
- `logs/pokertool_master.log` - Main backend log
- `logs/pokertool_errors.log` - Error-only log
- `logs/backend_startup.log` - Startup timing metrics
- `logs/frontend_compile_errors.log` - Frontend build errors
- `logs/trouble_feed.txt` - AI-optimized error aggregation

### Real-Time Monitoring

```bash
tail -f logs/errors-and-warnings.log
tail -f logs/trouble_feed.txt
```

---

## Logging System

**ALL logging uses the centralized master_logging.py system**

```python
from pokertool.master_logging import get_logger

logger = get_logger(__name__)
logger.info("Your message here")
```

**Rules:**

- Never create standalone log files
- All logs write to `logs/` directory
- Use `master_logging.py` for all logging configuration

---

## Git Workflow

### Branch Strategy

1. **Work on `develop` branch** (primary development)
2. **PRs merge to `master`** (stable releases)
3. **Feature branches** - `feature/your-feature-name`

### Commit Workflow (MANDATORY)

```bash
# 1. Check status
git status

# 2. Stage changes
git add -A

# 3. Commit with conventional message
git commit -m "type(scope): description"

# 4. Push to develop
git push origin develop
```

### Pre-Commit Checklist

- [ ] All tests pass: `python test.py`
- [ ] Coverage is 95%+: `python test.py --coverage`
- [ ] No linting errors
- [ ] Documentation updated if needed
- [ ] Commit message follows convention

---

## Common Commands Reference

```bash
# Start application
python3 start.py

# Run tests (REQUIRED before every commit)
python test.py
python test.py --coverage
python test.py --quick

# Check for errors
./scripts/check-errors

# Build frontend
cd pokertool-frontend && npm run build

# TypeScript check
cd pokertool-frontend && npx tsc --noEmit

# Monitor logs
tail -f logs/errors-and-warnings.log
```

---

## Quality Gates

**Every change must satisfy ALL of these:**

1. **Tests pass:** `python test.py` shows 0 failures
2. **Coverage maintained:** 95%+ coverage verified
3. **No regressions:** All existing functionality works
4. **Committed:** Changes are committed with proper message
5. **Pushed:** Changes are pushed to `develop` branch

---

## Ultrathink Methodology

PokerTool uses [Ultrathink methodology](https://www.ultrathink.engineer/) for AI-optimized development:

1. **AI Cognitive Expansion** - 90% architecting, 10% coding
2. **Strategic Investment** - Deep thinking prevents rewrites
3. **Constructive AI Conflict** - Challenge first responses
4. **Continuous Experimentation** - Document everything in ADRs

**See:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete methodology.

---

## Important Reminders

- **ALWAYS** start from root with `start.py`
- **ALWAYS** run `python test.py` before committing
- **ALWAYS** push after EVERY commit - no exceptions
- **ALWAYS** increment version before committing
- **ALWAYS** test EVERYTHING - every function, class, and feature needs tests
- **ALWAYS** check `logs/errors-and-warnings.log` first for errors
- **ALWAYS** put planning work in `docs/TODO.md` with details
- **NEVER** create `IMPLEMENTATION_PLAN.md` or similar planning documents
- **NEVER** create legacy log files outside `logs/` directory
- **NEVER** use standalone test scripts (must be pytest format)
- **NEVER** manually edit `docs/TODO.md` (use `python new_task.py`)
- **NEVER** leave commits unpushed - push immediately after every commit
- **All Changes Must Start via Raise_AF** (record the issue with `actifix.raise_af.record_error` so the ticket lands in `actifix/ACTIFIX-LIST.md`)
