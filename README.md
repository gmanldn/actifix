# Actifix

**Automatic Error Tracking and Resolution System**

Actifix is a quality-first automatic error tracking and resolution system designed to capture, isolate, and resolve errors systematically while maintaining architectural integrity and operational excellence. Built with a focus on deterministic behavior, comprehensive auditability, and enforcement-driven quality gates.

---

## CRITICAL: Quality-First Development Requirements

> **Every change MUST pass all quality gates. No exceptions.**

### Mandatory Workflow

```bash
# 1. Run full test suite (REQUIRED before every commit)
python -m pytest test/ --cov=src/actifix --cov-report=term-missing

# 2. Verify architecture compliance
python -m actifix.testing --validate-architecture

# 3. Check system health
python -m actifix.health --comprehensive

# 4. Commit with proper format
git add -A
git commit -m "type(scope): description"
git push origin develop
```

### Quality Gates

| Requirement | Target | Command |
|-------------|--------|---------| 
| All tests pass | 0 failures | `python -m pytest test/` |
| Test coverage | 90%+ | `pytest --cov=src/actifix` |
| Architecture compliance | 100% | `python -m actifix.testing --validate-architecture` |
| Health checks | All pass | `python -m actifix.health --comprehensive` |
| Branch | `develop` | `git push origin develop` |

**See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete development guidelines.**

---

## Features

- **Automatic Error Capture** - Systematic capture of all errors with full context and correlation tracking
- **Error Quarantine System** - Intelligent isolation of corrupted state to prevent system-wide failures  
- **Centralized Logging** - Structured logging with correlation IDs and distributed tracing
- **Health Monitoring** - Continuous system health tracking with degradation detection
- **Architectural Enforcement** - Built-in validation of architectural contracts and dependencies
- **Quality Gates** - Comprehensive testing and compliance validation
- **Deterministic Behavior** - No silent failures, no hidden state, no "probably fine" outcomes
- **Audit Trail** - Complete traceability of all meaningful system actions

## Quick Start

### Installation

**Unix/Linux/macOS:**
```bash
git clone https://github.com/gmanldn/actifix.git
cd actifix
pip install -e .
```

**Verification:**
```bash
# Verify installation
python -m actifix --help

# Initialize system
python -m actifix.bootstrap --init

# Run health check
python -m actifix.health --status
```

For detailed installation instructions, see **[Installation Guide](docs/INSTALLATION.md)**.

### Running Actifix

```bash
# Initialize and start monitoring
python -m actifix.bootstrap

# Check system health
python -m actifix.health --status

# View recent errors
python -m actifix.raise_af --list-recent

# Check quarantine status
python -m actifix.quarantine --status
```

### Integration Example

```python
from actifix import bootstrap, raise_af

# Initialize actifix in your application
bootstrap.initialize()

# Use in error handling
try:
    risky_operation()
except Exception as e:
    error_id = raise_af.capture_error(e, context={"operation": "critical_task"})
    # Error is now tracked and ready for automated resolution
    raise
```

## Documentation

### Core Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation and setup instructions
- **[Development Guide](docs/DEVELOPMENT.md)** - Development workflow, standards, and best practices  
- **[Architecture Overview](Arch/ARCHITECTURE_CORE.md)** - Core architectural principles and constraints

### Architecture Documentation

The `arch/` folder contains our sophisticated architecture mapping system:

- **[Module Catalog](arch/MODULES.md)** - Human-readable breakdown of system modules
- **[Architecture Map](arch/MAP.yaml)** - Machine-readable module definitions and contracts
- **[Dependency Graph](arch/DEPGRAPH.json)** - Visual dependency relationships with rationale

## System Architecture

Actifix is built around a domain-driven architecture with four key domains:

### Runtime Domain
- **bootstrap.main**: System initialization and process orchestration
- **runtime.config**: Configuration management and environment normalization  
- **runtime.state**: State management and persistence

### Infrastructure Domain  
- **infra.logging**: Centralized logging with correlation tracking
- **infra.health**: Health monitoring and system status tracking

### Core Domain
- **core.raise_af**: Error capture and ticket creation
- **core.do_af**: Ticket processing and automated remediation
- **core.quarantine**: Error isolation and safe failure handling

### Tooling Domain
- **tooling.testing**: Quality assurance and architecture validation

See **[Architecture Overview](Arch/ARCHITECTURE_CORE.md)** for detailed architectural principles.

## Development Methodology

Actifix follows a **quality-first development methodology** with these core principles:

### Architectural Philosophy

1. **Determinism** - No silent skips, no hidden state, no "probably fine" outcomes
2. **Auditability** - Every meaningful action leaves a durable, inspectable trail  
3. **Enforcement Over Convention** - Rules are executable and verified, not advisory
4. **Durability and Safety** - Crashes and restarts are first-class design concerns
5. **Continuity Over Time** - Decisions persist across sessions and contributors

### Quality Standards

- ✅ **90%+ Test Coverage** - Comprehensive test suite with architecture validation
- ✅ **Architecture Compliance** - All components must respect module contracts
- ✅ **Centralized Error Handling** - All errors flow through the governance system
- ✅ **Documentation-First** - Documentation created before or alongside code
- ✅ **Fail-Fast Philosophy** - Invalid states rejected immediately

See **[Development Guide](docs/DEVELOPMENT.md)** for complete methodology details.

## Testing

```bash
# Full test suite with coverage
python -m pytest test/ --cov=src/actifix --cov-report=term-missing

# Architecture compliance tests
python -m actifix.testing --validate-architecture

# Quick tests (exclude slow integration tests)
python -m pytest test/ -m "not slow"

# Health system validation
python -m actifix.health --comprehensive
```

**Test Coverage:**
- 90%+ automated test coverage across all modules
- Architecture compliance validation
- Health monitoring tests
- Error flow and recovery tests

## Error Handling System

Actifix implements a sophisticated error governance system:

### How It Works

```
Error Occurs → RaiseAF Captures → Quarantine Isolates → DoAF Processes → Resolution
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `raise_af.py` | Capture errors with full context | `src/actifix/raise_af.py` |
| `do_af.py` | Process and resolve error tickets | `src/actifix/do_af.py` |
| `quarantine.py` | Isolate corrupted state safely | `src/actifix/quarantine.py` |
| `health.py` | Monitor system health continuously | `src/actifix/health.py` |

### Features

- **Automatic Error Capture** - Errors flow automatically into the governance system
- **Smart Deduplication** - Hash-based duplicate detection prevents noise
- **Context Preservation** - Full error context captured with correlation IDs
- **Safe Isolation** - Corrupted state quarantined to prevent spread
- **Audit Trail** - Complete lifecycle tracking from detection to resolution

### Usage

```python
from actifix import raise_af, quarantine

try:
    dangerous_operation()
except Exception as e:
    # Automatic capture with context
    error_id = raise_af.capture_error(
        e,
        context={"component": "data_processor", "operation": "transform"}
    )
    
    # Quarantine any corrupted state
    quarantine.isolate_error_state(error_id)
```

## Health Monitoring

Actifix includes comprehensive health monitoring:

```bash
# System overview
python -m actifix.health --status

# Detailed component checks
python -m actifix.health --check-component=logging
python -m actifix.health --check-component=quarantine  

# Continuous monitoring
python -m actifix.health --monitor --interval=30
```

**Health Indicators:**
- System startup and initialization status
- Component health and degradation detection
- Error capture rate and quarantine status
- Architecture compliance validation
- Resource utilization monitoring

## Configuration

Actifix follows zero-configuration principles but supports customization:

### Environment Variables

```bash
# Core settings
export ACTIFIX_LOG_LEVEL=INFO
export ACTIFIX_LOG_DIR=./logs
export ACTIFIX_STATE_DIR=./actifix_state

# Health monitoring
export ACTIFIX_HEALTH_CHECK_INTERVAL=30
export ACTIFIX_QUARANTINE_MAX_SIZE=100MB
```

### Configuration File

```json
{
  "logging": {
    "level": "INFO", 
    "directory": "./logs",
    "correlation_tracking": true
  },
  "health": {
    "check_interval": 30,
    "degraded_threshold": 5
  },
  "quarantine": {
    "max_size": "100MB",
    "auto_cleanup": true
  }
}
```

## Contributing

Contributions must follow strict quality requirements:

### Required Before Every Commit

1. **All tests pass:** `python -m pytest test/`
2. **Architecture compliance:** `python -m actifix.testing --validate-architecture`  
3. **Health checks pass:** `python -m actifix.health --comprehensive`
4. **Coverage >= 90%:** Check coverage report
5. **Code formatted:** `black src/ test/`

### Pull Request Checklist

- [ ] All quality gates pass
- [ ] Architecture compliance validated
- [ ] Tests cover new functionality
- [ ] Documentation updated
- [ ] Commit messages follow conventional format

See **[Development Guide](docs/DEVELOPMENT.md)** for detailed contribution workflow.

## Project Structure

```
actifix/
├── arch/                    # Architecture documentation
│   ├── MODULES.md          # Module catalog
│   ├── MAP.yaml           # Architecture map
│   └── DEPGRAPH.json      # Dependency graph
├── docs/                   # User documentation  
│   ├── INSTALLATION.md    # Installation guide
│   └── DEVELOPMENT.md     # Development workflow
├── src/actifix/           # Source code
│   ├── bootstrap.py       # System initialization
│   ├── config.py          # Configuration management
│   ├── health.py          # Health monitoring
│   ├── log_utils.py       # Centralized logging
│   ├── raise_af.py        # Error capture
│   ├── do_af.py           # Error processing  
│   ├── quarantine.py      # Error isolation
│   └── testing.py         # Quality assurance
├── test/                   # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── architecture/      # Architecture tests
├── Arch/                  # Legacy architecture docs
│   └── ARCHITECTURE_CORE.md
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Support

- **Documentation**: Full documentation in `docs/` directory
- **GitHub Issues**: [Report bugs or request features](https://github.com/gmanldn/actifix/issues)  
- **Architecture**: Technical details in `arch/` folder
- **Development**: See `docs/DEVELOPMENT.md` for workflow

## License

Actifix is released under the MIT License. See [LICENSE](LICENSE) for details.

---

**Core Philosophy:** Quality over convenience. Enforcement over convention. Auditability over optimization.

**Quality Commitment:** Every component respects architectural contracts. Every error is captured and tracked. Every action is auditable. No exceptions.
