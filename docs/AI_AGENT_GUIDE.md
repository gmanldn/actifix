# AI Agent Guide for Actifix

This guide explains the tools and APIs available specifically for AI agents working with Actifix.

## Essential Tools for AI Agents

### 1. Codebase Explorer (`codebase.py`)

**Purpose**: Navigate and inspect the Actifix codebase efficiently.

**Location**: `codebase.py` (symlink in root) → `scripts/codebase.py`

**Key Features**:
- List all files with sizes and modification dates
- Read file contents with optional line limits
- Search for text across the entire codebase
- Generate codebase statistics

**Common Usage Patterns**:

```bash
# List all Python files
python3 codebase.py --list --pattern "*.py"

# Find files in a specific directory
python3 codebase.py --list --path src/actifix/modules

# Read a specific file
python3 codebase.py --read src/actifix/raise_af.py

# Search for function calls
python3 codebase.py --search "record_error"

# Get codebase overview
python3 codebase.py --stats

# Get recently modified files (shows in stats output)
python3 codebase.py --stats
```

**When to Use**:
- **Before making changes**: Understand the current codebase structure
- **During investigation**: Find relevant files and code
- **For context**: See which files were recently modified
- **When debugging**: Search for specific functions or patterns

**JSON Output** (for programmatic use):
```bash
python3 codebase.py --list --json > files.json
python3 codebase.py --stats --json > stats.json
```

### 2. Ticket Management API

**Purpose**: Create and manage tickets programmatically via REST API.

**Base URL**: `http://localhost:8030/api` (default)

#### Create a Ticket (POST /api/raise-ticket)

```bash
curl -X POST http://localhost:8030/api/raise-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Error description",
    "source": "file.py:42",
    "error_type": "BugFix",
    "priority": "P2",
    "run_label": "automation-run"
  }'
```

**Required Fields**:
- `message`: Detailed error description
- `source`: Source location (file:line or module name)

**Optional Fields**:
- `error_type`: Type of issue (default: "APITicket")
- `priority`: P0-P4 (default: "P2")
- `run_label`: Label for tracking (default: "api-created")
- `capture_context`: Boolean, capture stack traces (default: false)

**Response**:
```json
{
  "success": true,
  "ticket_id": "ACT-20260129-XXXXX",
  "message": "Ticket created successfully",
  "priority": "P2"
}
```

#### Complete a Ticket (POST /api/complete-ticket)

```bash
curl -X POST http://localhost:8030/api/complete-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "ACT-20260129-XXXXX",
    "completion_notes": "Implementation: Fixed issue.\n\nFiles:\n- src/file.py",
    "test_steps": "1. Run tests",
    "test_results": "All tests pass",
    "summary": "Fixed critical bug"
  }'
```

**Required Fields**:
- `ticket_id`: The ticket to complete
- `completion_notes`: Must include "Implementation:" and "Files:" sections
- `test_steps`: Steps taken to test the fix
- `test_results`: Test results and verification

**Response**:
```json
{
  "success": true,
  "ticket_id": "ACT-20260129-XXXXX",
  "message": "Ticket marked complete"
}
```

#### List Tickets (GET /api/tickets)

```bash
curl http://localhost:8030/api/tickets
```

Returns both open and completed tickets with counts.

#### Get Single Ticket (GET /api/ticket/<id>)

```bash
curl http://localhost:8030/api/ticket/ACT-20260129-XXXXX
```

Returns full ticket details including stack traces, file context, and completion notes.

## Workflow Patterns for AI Agents

### Pattern 1: Understanding the Codebase

```bash
# Step 1: Get overview
python3 codebase.py --stats

# Step 2: Find relevant files
python3 codebase.py --list --pattern "raise_af*"

# Step 3: Read specific files
python3 codebase.py --read src/actifix/raise_af.py

# Step 4: Search for specific functionality
python3 codebase.py --search "mark_ticket_complete"
```

### Pattern 2: Investigating an Issue

```bash
# Step 1: Check recent changes
python3 codebase.py --stats | grep "Recently modified"

# Step 2: Search for error-related code
python3 codebase.py --search "exception"

# Step 3: Read error handling modules
python3 codebase.py --read src/actifix/quarantine.py
```

### Pattern 3: Creating and Processing Tickets via API

```python
import requests

# Create a ticket
response = requests.post(
    'http://localhost:8030/api/raise-ticket',
    json={
        'message': 'Implement new feature X',
        'source': 'feature_request.py:1',
        'error_type': 'Feature',
        'priority': 'P2',
    }
)
ticket_id = response.json()['ticket_id']

# Do the work...
# implement_feature()
# run_tests()

# Mark it complete
requests.post(
    'http://localhost:8030/api/complete-ticket',
    json={
        'ticket_id': ticket_id,
        'completion_notes': '''Implementation: Added feature X.

Files:
- src/actifix/feature_x.py
- test/test_feature_x.py
''',
        'test_steps': '1. Run pytest on test_feature_x.py',
        'test_results': 'All 5 tests pass',
    }
)
```

## Best Practices for AI Agents

### 1. Always Start with Codebase Understanding
Before making any changes, use `codebase.py` to:
- Understand the structure
- Find related files
- Check recent modifications
- Search for existing implementations

### 2. Use the API for Automation
- Create tickets programmatically for tracking work
- Mark tickets complete with proper evidence
- List tickets to understand what's being worked on

### 3. Follow Actifix Conventions
- Always set `ACTIFIX_CHANGE_ORIGIN=raise_af` before running
- Include proper completion evidence (Implementation + Files sections)
- Run tests before marking tickets complete
- Bump version after each commit

### 4. Leverage Search Capabilities
Use `codebase.py --search` to:
- Find where functions are called
- Locate error handling patterns
- Discover existing tests
- Understand module dependencies

### 5. Read Before Writing
Always use `codebase.py --read` before modifying files:
- Understand current implementation
- Maintain coding style
- Avoid duplicating functionality
- Preserve important patterns

## Example: Complete AI Agent Workflow

```bash
#!/bin/bash
# Example: AI agent fixing a bug

# 1. Understand the issue
python3 codebase.py --search "DatabaseError"

# 2. Find relevant files
python3 codebase.py --list --path src/actifix/persistence

# 3. Read the implementation
python3 codebase.py --read src/actifix/persistence/database.py

# 4. Create a ticket via API
TICKET_ID=$(curl -s -X POST http://localhost:8030/api/raise-ticket \
  -H "Content-Type: application/json" \
  -d '{"message":"Fix DatabaseError in connection pooling","source":"database.py:42","priority":"P1"}' \
  | jq -r .ticket_id)

# 5. Make the fix (modify files, add tests, etc.)
# ... editing code ...

# 6. Run tests
pytest test/test_database.py

# 7. Mark ticket complete
curl -X POST http://localhost:8030/api/complete-ticket \
  -H "Content-Type: application/json" \
  -d "{
    \"ticket_id\": \"$TICKET_ID\",
    \"completion_notes\": \"Implementation: Fixed connection leak.\n\nFiles:\n- src/actifix/persistence/database.py\n- test/test_database.py\",
    \"test_steps\": \"1. Run pytest test/test_database.py\",
    \"test_results\": \"All tests pass\"
  }"

# 8. Commit following Actifix workflow
git add ...
git commit -m "fix(persistence): fix connection leak ($TICKET_ID)"
```

## Quick Reference

| Task | Command |
|------|---------|
| List all files | `python3 codebase.py --list` |
| List Python files | `python3 codebase.py --list --pattern "*.py"` |
| Read a file | `python3 codebase.py --read path/to/file.py` |
| Search codebase | `python3 codebase.py --search "pattern"` |
| Get statistics | `python3 codebase.py --stats` |
| Create ticket | `POST /api/raise-ticket` |
| Complete ticket | `POST /api/complete-ticket` |
| List tickets | `GET /api/tickets` |
| Get ticket details | `GET /api/ticket/<id>` |

## Integration with Other Tools

### With Architecture Validator
```bash
# Before committing
python3 -m actifix.validators.architecture_validator
```

### With Test Runner
```bash
# Run specific tests
pytest test/test_specific.py -v

# Run all tests
pytest
```

### With Do_AF
```bash
# Process tickets locally
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.do_af process --max-tickets 5
```

## Troubleshooting

### Codebase.py Not Found
```bash
# Create symlink if missing
ln -s scripts/codebase.py codebase.py
```

### API Not Responding
```bash
# Check if API server is running
curl http://localhost:8030/api/health

# Start API if needed
python3 scripts/start.py
```

### Permission Denied on codebase.py
```bash
chmod +x scripts/codebase.py
chmod +x codebase.py
```

## Summary

The codebase explorer and ticket management API provide AI agents with powerful tools for autonomous operation within Actifix. Use `codebase.py` for exploration and understanding, and the API endpoints for creating tickets and tracking work programmatically.

**Key Principle**: Always explore before acting. Use these tools to understand the codebase deeply before making changes.
