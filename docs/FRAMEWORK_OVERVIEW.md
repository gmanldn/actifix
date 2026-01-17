# Actifix Framework - Self-Improving Error Management System

## Overview

Actifix is a **self-improving error tracking and management framework** that can track its own development, improvements, and bugs. It's designed to be the central error management system for any project, with sophisticated AI integration, context capture, and production-grade reliability features.

## Key Features

### Core Capabilities
- **Comprehensive Error Capture**: Captures errors with full context including stack traces, file snippets, and system state
- **Auto-Priority Classification**: Automatically classifies errors as P0-P4 based on characteristics
- **Duplicate Prevention**: Smart deduplication prevents redundant error tickets using normalized "duplicate guards"
- **Secret Redaction**: Automatically redacts API keys, passwords, and PII from error captures
- **AI Integration Ready**: Generates comprehensive remediation notes for AI assistants (Claude, GPT, etc.)
- **Fallback Queuing**: Reliable error capture even when primary storage is unavailable
- **Context Window Management**: Efficient 200k token context management for AI processing

### Self-Improvement Features
- **Self-Development Mode**: Actifix can track its own development errors and improvements
- **Development Milestones**: Track development progress as tickets
- **Exception Handler Integration**: Global exception handler captures development bugs automatically
- **Bootstrap System**: Easy setup for self-improving development workflow

## Architecture

### Core Components

#### 1. RaiseAF (Error Capture Engine)
- Location: `src/actifix/raise_af.py`
- Captures errors with detailed context
- Classifies priority automatically
- Prevents duplicate tickets
- Generates AI remediation notes

#### 2. State Management
- Location: `src/actifix/state_paths.py`
- Manages state directories and file paths
- Configurable via environment variables
- Ensures consistent storage locations

#### 3. Bootstrap System
- Location: `src/actifix/bootstrap.py`
- Enables self-development mode
- Installs exception handlers
- Creates initial project structure

## Installation

### Basic Setup

```bash
# Clone the repository
git clone https://github.com/gmanldn/actifix.git
cd actifix

# The framework is ready to use! No installation needed.
```

### Enable Self-Development Mode

```python
import sys
sys.path.insert(0, 'src')
import actifix

# Bootstrap actifix to track its own development
actifix.bootstrap_actifix_development()

# Create initial ticket
actifix.create_initial_ticket()

# Track development progress
actifix.track_development_progress(
    "Framework initialized",
    "Actifix is now tracking its own development!"
)
```

## Usage

### Basic Error Recording

```python
import actifix

# Enable error capture
actifix.enable_actifix_capture()

# Record an error
try:
    # Your code here
    result = risky_operation()
except Exception as e:
    actifix.record_error(
        message=str(e),
        source='my_module.py:42',
        run_label='my-application',
        error_type=type(e).__name__
    )
```

### Advanced Usage with Full Context

```python
import actifix

# Enable capture
actifix.enable_actifix_capture()

# Record error with full context capture
try:
    dangerous_operation()
except Exception as e:
    entry = actifix.record_error(
        message=str(e),
        source=f'{__file__}:{sys._getframe().f_lineno}',
        run_label='production-system',
        error_type=type(e).__name__,
        priority=actifix.TicketPriority.P1,  # Override priority
        capture_context=True  # Capture file context and system state
    )
    
    if entry:
        print(f"Error captured as ticket {entry.entry_id}")
```

### Self-Development Mode

```python
import actifix

# Enable self-development mode
actifix.bootstrap_actifix_development()

# Now actifix will automatically track its own development errors!

# Track development milestones
actifix.track_development_progress(
    "New feature implemented",
    "Added support for custom AI integration"
)
```

## Configuration

### Environment Variables

- `ACTIFIX_CAPTURE_ENABLED`: Enable/disable error capture (`1`, `true`, `yes`, `on`, `debug`)
- `ACTIFIX_DATA_DIR`: Override default data directory (default: `./actifix`)
- `ACTIFIX_STATE_DIR`: Override default state directory (default: `./.actifix`)
- `ACTIFIX_FILE_CONTEXT_MAX_CHARS`: Max chars for file context (default: `2000`)
- `ACTIFIX_SYSTEM_STATE_MAX_CHARS`: Max chars for system state (default: `1500`)

### Priority Levels

- **P0 (Critical)**: System down, data loss, crashes
- **P1 (High)**: Core functionality broken, security issues
- **P2 (Medium)**: Important but workaround exists (default)
- **P3 (Low)**: Minor issues, cosmetic problems
- **P4 (Trivial)**: Nice to have, low impact

## File Structure

### Generated Records

Actifix stores artifacts in the database:

- **data/actifix.db**: SQLite ticket database (priority, status, AI notes, context); this is the canonical, writable task store.
- **v_recent_tickets**: Read-only rollup of the last 20 errors for quick auditing.
- **v_ticket_history**: Chronological completion history derived from the tickets table.
- **event_log**: Lifecycle audit trail of system activity.

> Legacy Markdown task files such as `TASK_LIST.md` or `Actifix-list.md` were retired when the database-first model was adopted—only the `tickets` table in `data/actifix.db` is actively managed.

### Ticket Format

Each ticket includes:
- Unique ID (e.g., `ACT-20261001-ABC123`)
- Priority level (P0-P4)
- Error type and message
- Source location
- Creation timestamp
- Duplicate guard for deduplication
- Status tracking (Open, In-Progress, Completed, Blocked)
- Checklist (Documented, Functioning, Tested, Completed)
- Stack trace preview
- AI remediation notes

## Self-Improvement Workflow

Actifix is designed to improve itself! Here's how:

1. **Bootstrap**: Enable self-development mode
2. **Development**: As you develop, actifix captures errors in its own code
3. **Review**: Query `data/actifix.db` (or use the DoAF API) to inspect ticket status
4. **Fix**: Implement fixes for the captured issues
5. **Track**: Mark tickets as completed when fixed
6. **Iterate**: Continue developing, actifix keeps tracking!

### Example: Actifix Improving Itself

```python
# Step 1: Bootstrap self-development
import actifix
actifix.bootstrap_actifix_development()

# Step 2: Develop a new feature
# If there's a bug, actifix captures it automatically!

# Step 3: Track your progress
actifix.track_development_progress(
    "DoAF implementation started",
    "Beginning ticket processing engine development"
)

# Step 4: If you encounter an error during development,
# actifix's exception handler will capture it automatically!
```

## Testing

### Run Basic Tests

```bash
# Run the basic test suite
cd /Users/georgeridout/Repos/actifix
ACTIFIX_CAPTURE_ENABLED=1 python3 -m pytest test/test_actifix_basic.py -v
```

### Self-Improvement Demo

```bash
# Run the self-improvement demonstration
cd /Users/georgeridout/Repos/actifix
python3 test/test_actifix_basic.py
```

## Roadmap

### Phase 1: Core Framework ✅
- [x] Error capture system (RaiseAF)
- [x] State management
- [x] Bootstrap system
- [x] Basic test suite

### Phase 2: Ticket Processing (In Progress)
- [ ] DoAF ticket processing engine
- [ ] Validation framework
- [ ] Context building for AI integration
- [ ] Ticket state management

### Phase 3: Advanced Features (Planned)
- [ ] Health monitoring system
- [ ] Circuit breaker patterns
- [ ] Retry mechanisms
- [ ] Notification system
- [ ] Telemetry collection

### Phase 4: AI Integration (Planned)
- [ ] Claude integration
- [ ] OpenAI integration
- [ ] Custom AI client interface
- [ ] Automatic fix suggestions

## Contributing

Actifix tracks its own development! To contribute:

1. Enable self-development mode
2. Actifix will create tickets for any issues you encounter
3. Query `data/actifix.db` or the DoAF endpoint to review tickets
4. Implement fixes
5. Submit PR with completed tickets

## License

[Your License Here]

## Credits

Originally inspired by the sophisticated actifix system from pokertool.
Generalized and enhanced for universal use.

---

**Actifix: The framework that improves itself!** 🚀
