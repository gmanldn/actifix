# Actifix Ticket Completion Workflow

## Overview

This document describes the **quality-gated ticket completion system** that ensures NO ticket can be marked complete without proper evidence of implementation and testing.

## Quality Gate Requirements

To mark any ticket as **Completed**, you MUST provide:

### 1. **Completion Notes** (Minimum 20 characters)
**Purpose**: Describe what work was done to fix the ticket.

**Examples**:
- ❌ "Fixed bug" (too short - 9 chars)
- ❌ "Implemented the feature" (too short - 22 chars, barely acceptable)
- ✅ "Fixed null pointer exception in database query by adding null checks at lines 42-45 in db.py. Applied defensive validation pattern throughout module."
- ✅ "Refactored ticket processing logic to eliminate race condition. Changed from pessimistic locking to optimistic locking with version checks."

**What to include**:
- Specific file paths and line numbers
- Description of the fix or feature
- Any architectural changes made
- Dependencies modified
- Backward compatibility considerations

---

### 2. **Test Steps** (Minimum 10 characters)
**Purpose**: Describe HOW the fix was tested.

**Examples**:
- ❌ "Tested" (too short - 6 chars)
- ❌ "Ran tests" (too short - 9 chars)
- ✅ "Ran pytest test_database_query.py with -v flag. Executed manual integration test by creating 100 concurrent database connections."
- ✅ "Added 15 new unit tests. Ran full test suite with coverage analysis. Performed manual regression testing across 3 production scenarios."

**What to include**:
- Specific test commands run
- Test files executed
- Manual testing steps
- Edge cases tested
- Concurrent/stress testing (if applicable)
- Tools used (pytest, coverage, debugger, etc.)

---

### 3. **Test Results** (Minimum 10 characters)
**Purpose**: Provide evidence that the fix works.

**Examples**:
- ❌ "Works fine" (too short - 10 chars, borderline - too vague)
- ❌ "All tests pass" (too short - 14 chars, minimal)
- ✅ "All 47 tests passed with 98% code coverage. No null pointer exceptions. Regression tests verified fix doesn't break existing functionality."
- ✅ "100% test success rate. Database queries execute 40% faster after optimization. Memory usage reduced by 25%. Zero data loss in 1000-record test."

**What to include**:
- Test pass/fail status
- Number of tests run
- Code coverage metrics
- Performance improvements (if applicable)
- Any edge cases that now work
- Comparison to previous behavior
- Resource usage changes

---

## System Architecture

### Database Layer (`src/actifix/persistence/database.py`)

The tickets table includes these required fields:

```sql
completion_notes TEXT NOT NULL DEFAULT '',      -- What was done
test_steps TEXT NOT NULL DEFAULT '',            -- How it was tested
test_results TEXT NOT NULL DEFAULT '',          -- Test evidence
test_documentation_url TEXT,                    -- Optional: Link to test artifacts
completion_verified_by TEXT,                    -- Optional: Verifier
completion_verified_at TIMESTAMP                -- Optional: Verification time
```

The schema enforces:
```sql
CHECK (status IN ('Open', 'In Progress', 'Completed'))
```

Only two status values allowed. You CANNOT use intermediate states like "Testing" or "ReviewPending". Tickets are either **Open** or **Completed**.

---

### Repository Layer (`src/actifix/persistence/ticket_repo.py`)

The `mark_complete()` method enforces validation:

```python
def mark_complete(
    self,
    ticket_id: str,
    completion_notes: str,      # REQUIRED: min 20 chars
    test_steps: str,            # REQUIRED: min 10 chars
    test_results: str,          # REQUIRED: min 10 chars
    summary: Optional[str] = None,
    test_documentation_url: Optional[str] = None,
) -> bool:
```

**Validation Logic**:
```python
# Checks completion_notes
if not completion_notes or len(completion_notes.strip()) < 20:
    raise ValueError("completion_notes required: must describe what was done (min 20 chars)")

# Checks test_steps
if not test_steps or len(test_steps.strip()) < 10:
    raise ValueError("test_steps required: must describe how testing was performed (min 10 chars)")

# Checks test_results
if not test_results or len(test_results.strip()) < 10:
    raise ValueError("test_results required: must provide test outcomes/evidence (min 10 chars)")
```

**If validation FAILS**:
- `ValueError` is raised
- Ticket remains **Open**
- No changes are made
- Full error message logged

---

### Application Layer (`src/actifix/do_af.py`)

The `mark_ticket_complete()` function handles the API:

```python
def mark_ticket_complete(
    ticket_id: str,
    completion_notes: str,              # REQUIRED
    test_steps: str,                    # REQUIRED
    test_results: str,                  # REQUIRED
    summary: str = "",
    test_documentation_url: Optional[str] = None,
    paths: Optional[ActifixPaths] = None,
    use_lock: bool = True,
) -> bool:
```

**Error Handling**:
- Catches `ValueError` from validation failures
- Logs `COMPLETION_VALIDATION_FAILED` event
- Returns `False` (doesn't raise)
- Ticket remains **Open**

---

## How to Complete Tickets Properly

### Method 1: Interactive Review Workflow (Recommended)

```bash
cd /Users/georgeridout/Repos/actifix

ACTIFIX_CHANGE_ORIGIN=raise_af python3 scripts/interactive_ticket_review.py
```

**Workflow**:
1. Script displays an open ticket
2. Prompts for completion notes (with live validation)
3. Prompts for test steps (with live validation)
4. Prompts for test results (with live validation)
5. Shows summary for review
6. Asks for confirmation before marking complete
7. If validation fails, shows specific error and allows retry

**Features**:
- ✅ Validates each field before allowing submission
- ✅ Shows minimum length requirements
- ✅ Provides examples for each field
- ✅ Requires explicit "yes" confirmation
- ✅ Prevents accidental completions
- ✅ Logs all completions with evidence

---

### Method 2: Programmatic Completion

```python
from actifix.do_af import mark_ticket_complete

success = mark_ticket_complete(
    ticket_id="ACT-20260114-ABC12",
    completion_notes="Fixed null pointer in database connection pool. Added defensive null checks at lines 156-172. Pool now safely handles connection failures.",
    test_steps="Ran pytest test_database_pool.py. Added 12 new tests for edge cases. Stress tested with 1000 concurrent connections.",
    test_results="All 47 tests passing. 99% code coverage. No memory leaks detected. Connections handled gracefully under stress.",
    summary="Database connection pool hardening"
)

if success:
    print("✓ Ticket marked complete with validation")
else:
    print("✗ Ticket not completed - validation failed")
```

---

### Method 3: Direct API Call

```bash
curl -X POST http://localhost:5000/api/complete-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "ACT-20260114-ABC12",
    "completion_notes": "Fixed null pointer in database connection pool...",
    "test_steps": "Ran pytest test_database_pool.py...",
    "test_results": "All 47 tests passing, 99% coverage...",
    "summary": "Database connection pool hardening"
  }'
```

**Response (Success)**:
```json
{
  "success": true,
  "ticket_id": "ACT-20260114-ABC12",
  "status": "Completed",
  "message": "Ticket marked complete with validation"
}
```

**Response (Validation Failure)**:
```json
{
  "error": "completion_notes required: must describe what was done (min 20 chars)",
  "field": "completion_notes",
  "provided_length": 15,
  "required_length": 20
}
```

---

## What Happens When Validation Fails

### Scenario: Empty completion_notes

```python
mark_ticket_complete(
    ticket_id="ACT-20260114-ABC12",
    completion_notes="",  # ❌ EMPTY - FAILS
    test_steps="Ran tests with pytest",
    test_results="All tests passed"
)
```

**Result**:
- ❌ `ValueError` raised
- ❌ Ticket remains **Open**
- ❌ No changes made to database
- ❌ Event logged: `COMPLETION_VALIDATION_FAILED`

```
ValueError: completion_notes required: must describe what was done (min 20 chars)
```

---

### Scenario: Test steps too short

```python
mark_ticket_complete(
    ticket_id="ACT-20260114-ABC12",
    completion_notes="Fixed null pointer exception by adding validation checks throughout the module.",
    test_steps="Tested",  # ❌ TOO SHORT (6 chars, need 10) - FAILS
    test_results="All tests passing with 98% coverage"
)
```

**Result**:
- ❌ `ValueError` raised
- ❌ Ticket remains **Open**
- ❌ Event logged: `COMPLETION_VALIDATION_FAILED`

```
ValueError: test_steps required: must describe how testing was performed (min 10 chars)
```

---

### Scenario: All validations pass ✅

```python
mark_ticket_complete(
    ticket_id="ACT-20260114-ABC12",
    completion_notes="Fixed null pointer exception in database layer. Added null checks at lines 156-172. Defensive validation pattern applied throughout connection pool.",
    test_steps="Ran pytest test_db_pool.py with -v flag. Created 12 new unit tests. Stress tested with 1000 concurrent connections.",
    test_results="All 47 tests passing. 99% code coverage. Zero memory leaks detected. Graceful handling verified under stress."
)
```

**Result**:
- ✅ Returns `True`
- ✅ Ticket marked **Completed**
- ✅ Evidence stored in database
- ✅ Event logged: `TICKET_COMPLETED`

```
✓ Ticket ACT-20260114-ABC12 marked complete with validation
```

---

## Database State After Completion

When a ticket is successfully marked complete:

```sql
SELECT id, status, completed, completion_notes, test_steps, test_results
FROM tickets
WHERE id = 'ACT-20260114-ABC12';
```

**Result**:
```
id                    | status    | completed | completion_notes               | test_steps              | test_results
ACT-20260114-ABC12    | Completed | 1         | Fixed null pointer exception..  | Ran pytest test_db...   | All 47 tests passing...
```

---

## Length Requirements Summary

| Field | Min Chars | Typical Range | Purpose |
|-------|-----------|---------------|---------|
| `completion_notes` | 20 | 50-500 | Describe implementation |
| `test_steps` | 10 | 30-300 | Describe testing method |
| `test_results` | 10 | 30-200 | Provide evidence |

---

## Common Mistakes and Fixes

### ❌ Mistake 1: Generic completion notes

```python
completion_notes="Fixed the bug"  # ❌ Only 12 chars
```

**Fix**:
```python
completion_notes="Fixed the bug by adding null checks in database layer at lines 42-48. Used defensive programming pattern to prevent NPE."  # ✅ 130 chars
```

---

### ❌ Mistake 2: Vague test steps

```python
test_steps="Tested it"  # ❌ Too vague, only 9 chars
```

**Fix**:
```python
test_steps="Ran pytest test_suite.py with -v. Manual regression testing on 5 scenarios. Verified with gdb debugger for memory access."  # ✅ 120 chars
```

---

### ❌ Mistake 3: No evidence in test results

```python
test_results="Works"  # ❌ Only 5 chars, no evidence
```

**Fix**:
```python
test_results="All 47 unit tests passing. 98% code coverage. Zero memory leaks detected. Performance improved 35% vs baseline. Regression tests green."  # ✅ 140 chars
```

---

## Auditing Completed Tickets

View completion evidence for a ticket:

```bash
sqlite3 data/actifix.db << 'EOF'
SELECT
    id,
    status,
    completion_notes,
    test_steps,
    test_results,
    completion_verified_by,
    completion_verified_at
FROM tickets
WHERE id = 'ACT-20260114-ABC12';
EOF
```

---

## Enforcement Summary

| Component | Rule | Consequence |
|-----------|------|------------|
| **Database** | completion_notes required | Cannot insert empty |
| **Repository** | completion_notes min 20 chars | ValueError raised |
| **Repository** | test_steps min 10 chars | ValueError raised |
| **Repository** | test_results min 10 chars | ValueError raised |
| **Application** | Catches ValueError | Returns False, logs error |
| **API** | Request validation | 400 Bad Request |

---

## Getting Started

1. **Review an open ticket**:
   ```bash
   python3 scripts/interactive_ticket_review.py
   ```

2. **Follow the workflow** - provide implementation and test evidence

3. **Submit with confidence** - validation ensures quality

4. **Verify completion** - check database for stored evidence

---

## Questions?

- ✓ Completion notes too short? Make them more descriptive
- ✓ Test results missing evidence? Add specific metrics/outcomes
- ✓ Can't complete a ticket? That's the point - ensure work is actually done first

The system is designed to prevent "fake" ticket completions and ensure every completion has real evidence.
