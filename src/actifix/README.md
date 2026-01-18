# Actifix - Automated Error Tracking and Remediation

A generic, project-agnostic system for automated error tracking, ticket management, and AI-powered remediation.

## Overview

Actifix provides a complete workflow for:

1. **RaiseAF** - Recording errors and creating tickets
2. **DoAF** - Dispatching tickets to AI for automated fixes
3. **Health Monitoring** - SLA tracking and system diagnostics

## Quick Start

```python
from actifix import record_error, process_tickets, get_health

# Record an error
entry = record_error(
    error_type="RuntimeError",
    message="Database connection failed",
    source="db/connection.py:42",
    priority="P1"
)

# Process pending tickets
processed = process_tickets(max_tickets=5)

# Check system health
health = get_health()
print(f"Status: {health.status}, Open: {health.open_tickets}")
```

## Installation

```bash
# Install from source
pip install -e .

# Or copy the actifix package to your project
cp -r src/actifix /your/project/
```

## Architecture

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| RaiseAF | `raise_af.py` | Error recording, ticket creation |
| DoAF | `do_af.py` | Ticket dispatch, AI integration |
| Health | `health.py` | SLA monitoring, diagnostics |
| State Paths | `state_paths.py` | Path configuration |
| Log Utils | `log_utils.py` | Atomic writes, safe file operations |

### File Structure

```
your-project/
├── data/                       # Runtime storage
│   └── actifix.db              # Tickets table (canonical source of truth)
├── actifix/                    # Data directory for derived artifacts
├── .actifix/                   # State directory (fallback queue, quarantine)
├── logs/                       # Optional runtime logs
└── src/
    └── actifix/               # Python package
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACTIFIX_DATA_DIR` | Base directory for files | `./actifix/` |
| `ACTIFIX_PROJECT_ROOT` | Project root path | Current directory |
| `ACTIFIX_CAPTURE_ENABLED` | Enable/disable capture | `1` (enabled) |

### Custom Paths

```python
from actifix import get_actifix_paths
from pathlib import Path

paths = get_actifix_paths(
    base_dir=Path("/custom/path"),
    project_root=Path("/my/project")
)
```

## API Reference

### record_error()

Record an error and create a ticket.

```python
entry = record_error(
    error_type="ValueError",      # Error type/category
    message="Invalid input",      # Error message
    source="module.py:10",        # Source location
    priority="P2",                # P0-P3 (P0 = critical)
    run_name="daily-job",         # Run/job identifier
    stack_trace="...",            # Optional stack trace
    correlation_id="abc123",      # Optional correlation ID
)
```

### record_exception()

Record an exception directly.

```python
try:
    risky_operation()
except Exception as e:
    entry = record_exception(e, priority="P1")
```

### process_tickets()

Process open tickets with optional AI handler.

```python
def my_ai_handler(ticket):
    # Implement fix logic
    return True  # Return True if fixed

processed = process_tickets(
    max_tickets=5,
    ai_handler=my_ai_handler
)
```

### get_health()

Get system health status.

```python
health = get_health()

print(f"Status: {health.status}")
print(f"Open tickets: {health.open_tickets}")
print(f"SLA breaches: {health.sla_breaches}")
print(f"Warnings: {health.warnings}")
```

## Priority Levels

| Priority | SLA | Description |
|----------|-----|-------------|
| P0 | 1 hour | Critical - system down |
| P1 | 4 hours | High - major functionality broken |
| P2 | 24 hours | Medium - standard bugs |
| P3 | 72 hours | Low - minor issues |

## Ticket Lifecycle

```
1. Error Detected
       ↓
2. RaiseAF creates tickets in `data/actifix.db` for structured logging
       ↓
3. Ticket marked as:
   - [ ] Documented
   - [ ] Functioning  
   - [ ] Tested
   - [ ] Completed
       ↓
4. DoAF dispatches to AI agent
       ↓
5. AI implements fix
       ↓
6. Ticket marked complete, moved to Completed Items
```

## Integration Examples

### Exception Handler Decorator

```python
from functools import wraps
from actifix import record_exception

def actifix_handler(priority="P2"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                record_exception(e, priority=priority)
                raise
        return wrapper
    return decorator

@actifix_handler(priority="P1")
def critical_function():
    ...
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Check Actifix Health
  run: |
    python -c "
    from actifix import get_health
    health = get_health()
    if not health.healthy:
        print(f'Actifix unhealthy: {health.status}')
        exit(1)
    "
```

### Custom AI Handler

```python
from actifix import process_tickets

def claude_handler(ticket):
    """Dispatch ticket to Claude for fixing."""
    prompt = f"""
    Fix this error:
    - Type: {ticket.error_type}
    - Message: {ticket.message}
    - Source: {ticket.source}
    """
    # Call Claude API here
    # Return True if fix was successful
    return False

process_tickets(ai_handler=claude_handler)
```

## Best Practices

1. **Use meaningful source locations** - Include file:line format
2. **Set appropriate priorities** - P0 for critical, P3 for nice-to-have
3. **Include stack traces** - Helps AI understand context
4. **Monitor SLA breaches** - Run health checks regularly
5. **Review completed tickets** - Verify AI fixes are correct

## Troubleshooting

### Duplicate tickets not being created

Actifix uses duplicate guards based on source+message hash. Same error won't create multiple tickets.

### Files not being created

Check `ACTIFIX_DATA_DIR` and ensure directory is writable.

### SLA breaches showing incorrectly

Verify system timezone. Actifix uses UTC internally.

## License

MIT License - See LICENSE file for details.
