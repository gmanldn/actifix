# Actifix Quality Gate Validation Architecture

## Executive Summary

The Actifix quality gate system enforces mandatory completion evidence through **two-layer validation** at the application level:

1. **Idempotency Guard** (Application Layer - `do_af.py`)
   - Prevents re-completion of already-finished tickets
   - Provides early failure with appropriate logging

2. **Quality Gate Validation** (Repository Layer - `ticket_repo.py`)
   - Enforces minimum length requirements for all evidence fields
   - Core quality gate mechanism

**IMPORTANT**: Despite what some documentation claims, validation is **NOT enforced at the database level**. The database schema only has basic NOT NULL constraints, not length constraints. All validation is application-level (Python code).

---

## Detailed Validation Flow

### Entry Point 1: Interactive Workflow (`scripts/interactive_ticket_review.py`)

```
User Input
    ↓
[live validation in script]
    ├─ completion_notes: min 20 chars?
    ├─ test_steps: min 10 chars?
    └─ test_results: min 10 chars?
    ↓
Calls: mark_ticket_complete()
```

### Entry Point 2: mark_ticket_complete() (`src/actifix/do_af.py:217`)

```python
def mark_ticket_complete(
    ticket_id: str,
    completion_notes: str,
    test_steps: str,
    test_results: str,
    summary: str = "",
    test_documentation_url: Optional[str] = None,
    paths: Optional[ActifixPaths] = None,
    use_lock: bool = True,
) -> bool:
```

**Function Flow**:
1. Get paths (lines 243-244)
2. Enforce Raise_AF-only policy (line 246)
3. **IDEMPOTENCY CHECK (Layer 1)** (lines 249-270)
   - Get ticket from repository
   - Return False if not found → Log TICKET_NOT_FOUND
   - Return False if already completed → Log TICKET_ALREADY_COMPLETED
   - Early fail with informative logging
4. **CALL REPOSITORY METHOD** (lines 272-280)
   - Pass parameters to repo.mark_complete()
   - Repository performs its own idempotency check (Layer 2, defense-in-depth)
   - Repository validates quality gate parameters
5. **ERROR HANDLING** (lines 297-305)
   - Catch ValueError from repository validation failure
   - Log COMPLETION_VALIDATION_FAILED event
   - Return False (doesn't raise)

**Key Design**:
- **Defense-in-Depth Idempotency**: Two independent idempotency checks
  - Application layer: Early fail with logging
  - Repository layer: Silent protection for direct calls
- **Separation of Concerns**: Application layer checks "is ticket eligible?", repository checks "are parameters valid?"

### Entry Point 3: fix_highest_priority_ticket() (`src/actifix/do_af.py:308`)

```python
def fix_highest_priority_ticket(
    paths: Optional[ActifixPaths] = None,
    completion_notes: str = "",
    test_steps: str = "",
    test_results: str = "",
    summary: str = "Resolved via dashboard fix",
    test_documentation_url: Optional[str] = None,
) -> dict:
```

**Function Flow**:
1. Get highest priority open ticket
2. Lock ticket
3. **CALL mark_ticket_complete()** (lines 365-413)
   - Passes all validation to mark_ticket_complete()
   - If ValueError raised, is caught and logged
   - Releases lock
4. Return result dict with success/failure details

**Key Design**: This function does NOT duplicate validation. All validation delegated to mark_ticket_complete().

---

### Repository Layer: repo.mark_complete() (`src/actifix/persistence/ticket_repo.py:394`)

```python
def mark_complete(
    self,
    ticket_id: str,
    completion_notes: str,
    test_steps: str,
    test_results: str,
    summary: Optional[str] = None,
    test_documentation_url: Optional[str] = None,
) -> bool:
```

**Function Flow**:
1. Get ticket by ID (line 426)
2. Return False if not found (line 428)
3. **QUALITY GATE VALIDATION #1** - completion_notes (lines 433-436)
   - Check not empty and >= 20 chars
   - Raise ValueError if invalid
4. **QUALITY GATE VALIDATION #2** - test_steps (lines 438-441)
   - Check not empty and >= 10 chars
   - Raise ValueError if invalid
5. **QUALITY GATE VALIDATION #3** - test_results (lines 443-446)
   - Check not empty and >= 10 chars
   - Raise ValueError if invalid
6. **BUILD UPDATES** (lines 448-463)
   - Set status = 'Completed'
   - Set documented = 1 (justified by completion_notes)
   - Set functioning = 1 (justified by test_results)
   - Set tested = 1 (justified by test_steps)
   - Set completion_notes, test_steps, test_results
   - Clear lock fields
7. **UPDATE DATABASE** (line 467)
   - Call update_ticket() with prepared updates
   - Return True/False

**Key Design**: This is the CORE quality gate. No ticket can reach database without passing these three validations.

---

## Validation Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User Input Layer                                            │
│ (scripts/interactive_ticket_review.py)                     │
│ - Prompts for completion_notes, test_steps, test_results  │
│ - Live validation shows errors immediately                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Application Layer - Idempotency Guard                       │
│ (src/actifix/do_af.py:mark_ticket_complete)               │
│ - Check: Ticket exists?                                    │
│ - Check: Ticket not already completed?                     │
│ - Logging: TICKET_NOT_FOUND, TICKET_ALREADY_COMPLETED     │
│ - Returns False early if checks fail                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Repository Layer - Quality Gate Validation                  │
│ (src/actifix/persistence/ticket_repo.py:mark_complete)    │
│ CORE VALIDATION - These are the real quality gates:         │
│                                                              │
│ - Check: completion_notes >= 20 chars? → ValueError        │
│ - Check: test_steps >= 10 chars? → ValueError              │
│ - Check: test_results >= 10 chars? → ValueError            │
│                                                              │
│ Sets database fields:                                       │
│ - status = 'Completed'                                      │
│ - documented = 1                                            │
│ - functioning = 1                                           │
│ - tested = 1                                                │
│ - completion_notes, test_steps, test_results (validated)   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Database Layer - Storage Only                               │
│ (src/actifix/persistence/database.py)                      │
│ - SQLite ACID compliance                                    │
│ - Constraints: NOT NULL on required fields                  │
│ - Constraints: CHECK status IN ('Open', 'Completed')        │
│ - NO length constraints (validation is application-level)   │
│ - Stores completion evidence fields                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling at Each Layer

### Layer 1: User Input Validation (interactive_ticket_review.py)

**Validation Logic**:
```python
def validate_input(field_name: str, value: str, min_length: int) -> tuple[bool, str]:
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"
    if len(value.strip()) < min_length:
        return False, f"{field_name} too short (min {min_length} chars, got {len(value.strip())})"
    return True, ""
```

**User Experience**:
- Shows error immediately
- Asks "Try again? (y/n):"
- Allows retry or skip

---

### Layer 2: Idempotency Check (do_af.py:mark_ticket_complete)

**Validation Logic**:
```python
existing = repo.get_ticket(ticket_id)
if not existing:
    log_event(paths.aflog_file, "TICKET_NOT_FOUND", ...)
    return False

if existing.get("status") == "Completed" or existing.get("completed"):
    log_event(paths.aflog_file, "TICKET_ALREADY_COMPLETED", ...)
    return False
```

**Result**:
- Returns False (no exception)
- Logs events for audit trail
- Prevents re-completion

---

### Layer 3: Quality Gate Validation (ticket_repo.py:mark_complete)

**Validation Logic**:
```python
if not completion_notes or len(completion_notes.strip()) < 20:
    raise ValueError("completion_notes required: must describe what was done (min 20 chars)")

if not test_steps or len(test_steps.strip()) < 10:
    raise ValueError("test_steps required: must describe how testing was performed (min 10 chars)")

if not test_results or len(test_results.strip()) < 10:
    raise ValueError("test_results required: must provide test outcomes/evidence (min 10 chars)")
```

**Result**:
- Raises ValueError immediately on any validation failure
- Application layer catches ValueError
- Logs COMPLETION_VALIDATION_FAILED event
- Returns False
- **NO database changes made** (fails before database update)

---

## Database Layer Clarification

### What the Database DOES Enforce

```sql
-- From schema definition:
CREATE TABLE tickets (
    ...
    completion_notes TEXT NOT NULL DEFAULT '',      -- NOT NULL enforced
    test_steps TEXT NOT NULL DEFAULT '',            -- NOT NULL enforced
    test_results TEXT NOT NULL DEFAULT '',          -- NOT NULL enforced
    status TEXT DEFAULT 'Open',                     -- DEFAULT only
    ...
    CHECK (status IN ('Open', 'Completed'))         -- Status check enforced
);
```

**Actual Database Constraints**:
- ✅ NOT NULL on completion_notes
- ✅ NOT NULL on test_steps
- ✅ NOT NULL on test_results
- ✅ status must be 'Open' or 'Completed'

### What the Database DOES NOT Enforce

- ❌ completion_notes minimum 20 characters
- ❌ test_steps minimum 10 characters
- ❌ test_results minimum 10 characters

These length validations are **entirely application-level** (Python code), not database constraints.

---

## Validation Responsibility Assignment

| Check | Responsibility | Location | Enforcement |
|-------|---|---|---|
| Ticket exists? | Idempotency | do_af.py:249-257 | Return False |
| Ticket not already completed? | Idempotency | do_af.py:259-270 | Return False + Log |
| completion_notes not empty? | Quality Gate | ticket_repo.py:433-436 | ValueError |
| completion_notes >= 20 chars? | Quality Gate | ticket_repo.py:433-436 | ValueError |
| test_steps not empty? | Quality Gate | ticket_repo.py:438-441 | ValueError |
| test_steps >= 10 chars? | Quality Gate | ticket_repo.py:438-441 | ValueError |
| test_results not empty? | Quality Gate | ticket_repo.py:443-446 | ValueError |
| test_results >= 10 chars? | Quality Gate | ticket_repo.py:443-446 | ValueError |
| status in (Open, Completed)? | Database | database.py:CHECK | DB constraint |

---

## Validation Flow: Success Path

```
mark_ticket_complete() called with valid parameters
    ↓
[Idempotency check] Ticket exists? YES
    ↓
[Idempotency check] Ticket not completed? YES
    ↓
Call repo.mark_complete()
    ↓
[Quality Gate] completion_notes >= 20 chars? YES
    ↓
[Quality Gate] test_steps >= 10 chars? YES
    ↓
[Quality Gate] test_results >= 10 chars? YES
    ↓
Build update dict with validated fields
    ↓
Call update_ticket()
    ↓
Database update succeeds
    ↓
Return True
    ↓
Log: TICKET_COMPLETED
```

---

## Validation Flow: Failure Path (Example: completion_notes too short)

```
mark_ticket_complete() called with 5-char completion_notes
    ↓
[Idempotency check] Ticket exists? YES
    ↓
[Idempotency check] Ticket not completed? YES
    ↓
Call repo.mark_complete()
    ↓
[Quality Gate] completion_notes >= 20 chars? NO
    ↓
Raise ValueError("completion_notes required: must describe what was done (min 20 chars)")
    ↓
[EXCEPTION CAUGHT] by try/except in mark_ticket_complete()
    ↓
Log: COMPLETION_VALIDATION_FAILED
    ↓
Return False
    ↓
** NO DATABASE CHANGES MADE **
    ↓
Ticket remains Open
    ↓
No fields updated
```

---

## Key Safety Properties

### Property 1: All-or-Nothing Updates

If ANY validation fails, the database is NOT updated. The validation happens before the database update, preventing partial/corrupt states.

### Property 2: Consistent Logging

Every validation failure is logged with:
- Event type: `COMPLETION_VALIDATION_FAILED`
- Ticket ID: Which ticket attempted completion
- Error message: Specific validation failure reason
- Extra context: As needed

### Property 3: Idempotency

Already-completed tickets cannot be re-completed, preventing overwriting original evidence.

### Property 4: Two-Gate System

1. **First Gate** (Idempotency): Is this ticket eligible for completion?
2. **Second Gate** (Quality): Does the completion evidence meet quality thresholds?

Both must pass, or ticket remains Open.

---

## Design Rationale: Why Two Layers?

### Why Idempotency at Application Layer?

- Checked first, fails fast
- Can log that ticket is already completed (informational)
- Prevents wasted database query if ticket is already done
- Returns False immediately without checking quality fields

### Why Quality Gate at Repository Layer?

- Core business logic responsibility
- Single point of truth for quality thresholds
- Can be called from multiple entry points
- Raises ValueError to indicate validation failure (different from "not found")

### Why Not Database Constraints?

- Would require CHECK constraints like `CHECK (length(completion_notes) >= 20)`
- SQLite doesn't support this natively
- Application-level validation is more flexible
- Easier to change requirements without migration

---

## Common Questions

### Q: Why are there multiple validation layers?

**A**: Because there are multiple entry points into the system:
1. Interactive workflow → prompts with live validation
2. mark_ticket_complete() API → idempotency check + repository validation
3. fix_highest_priority_ticket() → calls mark_ticket_complete()

Each layer validates appropriately for its context.

### Q: Why doesn't the database enforce length?

**A**: Because SQLite's CHECK constraints are limited. Modern databases could use CHECK length(field) >= 20, but SQLite doesn't have this. Application-level validation is cleaner and more maintainable.

### Q: What if I bypass the application layer and go directly to the database?

**A**: The database still has NOT NULL constraints, so completion_notes cannot be NULL. But you COULD insert a 5-character completion_notes directly. However:
- This would bypass Actifix's own rules
- The system isn't designed to be bypassed
- This would be a maintenance/debugging operation outside normal usage

### Q: Can two threads race and both complete the same ticket?

**A**: Unlikely. The application layer idempotency check runs before the database update. SQLite's locking ensures the database operation is atomic. If both threads check simultaneously:
1. Both might pass idempotency check
2. Both might call repo.mark_complete()
3. First one wins (updates first)
4. Second one would fail when try to update (if row locked)

However, the interactive workflow and mark_ticket_complete() have explicit idempotency guards, so re-completion attempts fail early.

---

## Summary

The Actifix quality gate system uses **two-layer application-level validation**:

1. **Idempotency Guard** (early fail): Is this ticket eligible?
2. **Quality Gate** (core validation): Does the evidence meet standards?

The database provides basic NOT NULL and status constraints, but does NOT enforce the quality gate length requirements. All length validation is application-level (Python code), allowing flexible thresholds and clear business logic ownership.
