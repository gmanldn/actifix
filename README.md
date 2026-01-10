# Actifix - Self-Improving Error Management Framework

> **The framework that tracks and improves itself!** 🚀

Always read AGENTS.md

Actifix is a sophisticated error tracking and management system with AI integration, designed to capture errors with comprehensive context and enable self-improvement workflows.

## ✨ Key Features

- 🎯 **Auto-Priority Classification** - Automatically classifies errors as P0-P4
- 🔒 **Secret Redaction** - Automatically redacts API keys, passwords, and PII
- 🤖 **AI Integration Ready** - Built-in support for Claude, GPT, and other AI assistants
- 🔄 **Self-Improvement Mode** - Actifix tracks its own development and bugs
- 📊 **Rich Context Capture** - Stack traces, file snippets, system state
- 🛡️ **Production-Grade Reliability** - Fallback queues, atomic writes, health checks
- 🚫 **Smart Deduplication** - Prevents redundant error tickets

## 🚀 Quick Start

### 1. Enable Error Tracking

```python
import sys
sys.path.insert(0, 'src')
import actifix

# Enable error capture
actifix.enable_actifix_capture()

# Record an error
try:
    risky_operation()
except Exception as e:
    actifix.record_error(
        message=str(e),
        source='my_module.py:42',
        run_label='my-application',
        error_type=type(e).__name__
    )
```

### 2. Enable Self-Development Mode

```python
import actifix

# Bootstrap actifix to track its own development!
actifix.bootstrap_actifix_development()

# Track development milestones
actifix.track_development_progress(
    "New feature completed",
    "Implemented advanced error tracking"
)
```

### 3. Check Generated Tickets

```bash
# View generated tickets
cat actifix/ACTIFIX-LIST.md

# View error rollup (last 20 errors)
cat actifix/ACTIFIX.md
```

## 📖 Documentation

- **[Quickstart](QUICKSTART.md)** - Fast setup and first ticket
- **[Framework Overview](docs/FRAMEWORK_OVERVIEW.md)** - Comprehensive guide
- **[Installation Guide](docs/INSTALLATION.md)** - Setup instructions
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing guidelines
- **[Architecture](Arch/ARCHITECTURE_CORE.md)** - System architecture

## 🎯 Use Cases

### 1. Production Error Tracking
Monitor production systems and automatically create tickets for errors with full context.

### 2. Development Error Management
Track bugs during development with automatic duplicate prevention.

### 3. Self-Improving Systems
Enable actifix to track its own development and create improvement tickets.

### 4. AI-Assisted Debugging
Generate comprehensive context for AI assistants to suggest fixes.

## 🏗️ Architecture

```
actifix/
├── src/actifix/          # Core framework
│   ├── raise_af.py       # Error capture engine
│   ├── bootstrap.py      # Self-development system
│   ├── state_paths.py    # State management
│   └── __init__.py       # Main API
├── test/                 # Test suite
│   └── test_actifix_basic.py
├── actifix/              # Generated tickets (created on first run)
│   ├── ACTIFIX.md        # Error rollup (last 20)
│   ├── ACTIFIX-LIST.md   # Detailed ticket list
│   ├── ACTIFIX-LOG.md    # Completion log
│   └── AFLog.txt         # Lifecycle log
└── docs/                 # Documentation
```

## 🧪 Testing

```bash
# Run basic tests
ACTIFIX_CAPTURE_ENABLED=1 python3 -m pytest test/test_actifix_basic.py -v

# Run self-improvement demo
python3 test/test_actifix_basic.py
```

## 🔧 Configuration

Set environment variables to customize behavior:

```bash
export ACTIFIX_CAPTURE_ENABLED=1    # Enable error capture
export ACTIFIX_DATA_DIR=./actifix   # Data directory
export ACTIFIX_STATE_DIR=./.actifix # State directory
```

## 📊 Ticket Priority Levels

- **P0 (Critical)** 🔴 - System down, data loss
- **P1 (High)** 🟠 - Core functionality broken  
- **P2 (Medium)** 🟡 - Important but workaround exists
- **P3 (Low)** 🟢 - Minor issues, cosmetic
- **P4 (Trivial)** ⚪ - Nice to have

## 🛠️ Development Status

### ✅ Completed
- Core error capture system (RaiseAF)
- State management and configuration
- Bootstrap and self-development mode
- Basic test suite
- Comprehensive documentation

### 🚧 In Progress
- Ticket processing engine (DoAF)
- Validation framework
- AI integration

### 📋 Planned
- Health monitoring system
- Advanced features (circuit breaker, retry, notifications)
- Enhanced AI integration
- Web dashboard

## 🤝 Contributing

Actifix uses itself for development! To contribute:

1. **Bootstrap self-development mode**
   ```python
   import actifix
   actifix.bootstrap_actifix_development()
   ```

2. **Develop your feature** - Actifix will track any issues automatically

3. **Review tickets** - Check `actifix/ACTIFIX-LIST.md` for captured issues

4. **Submit PR** - Include completed ticket references

## 💡 Example: Actifix Tracking Itself

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import actifix

# Enable self-development mode
print("Bootstrapping actifix self-development...")
actifix.bootstrap_actifix_development()

# Create initial ticket
actifix.create_initial_ticket()

# Track development progress
actifix.track_development_progress(
    "Framework initialized",
    "Actifix is now tracking its own development!"
)

print("\nCheck actifix/ACTIFIX-LIST.md to see the tickets!")
```

## 🌟 What Makes Actifix Special?

1. **Self-Improving** - Actifix can track and manage its own development
2. **AI-Native** - Designed from the ground up for AI-assisted debugging
3. **Production-Ready** - Includes fallback queues, atomic writes, health checks
4. **Context-Rich** - Captures everything needed to understand and fix errors
5. **Zero Dependencies** - Core framework uses only Python stdlib

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🙏 Credits

Originally inspired by the sophisticated actifix system from pokertool.
Generalized and enhanced for universal use across any project.

---

**Built with ❤️ by the Actifix community**

*The framework that improves itself!* 🚀
