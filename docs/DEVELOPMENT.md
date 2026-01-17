# Actifix Development Guide

## Overview

Actifix follows a **quality-first development methodology** emphasizing architectural compliance, comprehensive testing, and deterministic behavior. This guide outlines the development workflow, standards, and best practices.

## Development Philosophy

### Core Principles

1. **Architecture Compliance First** - All code must respect the architectural constraints defined in `arch/`
2. **Quality Gates Enforcement** - No compromises on test coverage, code quality, or deterministic behavior  
3. **Documentation-Driven Development** - Documentation is created before or alongside code
4. **Fail-Fast Philosophy** - Invalid states are rejected immediately, not handled gracefully
5. **Auditability** - Every meaningful action must leave an inspectable trail

### Quality Standards

- **Test Coverage**: 90%+ minimum, 95%+ for critical paths
- **Architecture Validation**: All components must pass architecture compliance checks
- **Error Handling**: All errors must flow through the centralized error governance system
- **Logging**: All operations must use the centralized logging system with correlation IDs

## Development Workflow

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/gmanldn/actifix.git
cd actifix

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black isort mypy

# Initialize development environment
python -m actifix.bootstrap --init --dev-mode
```

### Pre-Commit Quality Gates

Every commit MUST pass these quality gates:

```bash
# 1. Run full test suite
python -m pytest test/ --cov=src/actifix --cov-report=term-missing

# 2. Check code formatting
black --check src/ test/
isort --check-only src/ test/

# 3. Type checking
mypy src/actifix/

# 4. Architecture compliance
python -m actifix.testing --validate-architecture

# 5. Health system check
python -m actifix.health --comprehensive
```

### Branch Strategy

- **main**: Production-ready code only
- **develop**: Integration branch for features and day-to-day work
- **feature/***: Optional for large or experimental changes (not required)
- **hotfix/***: Critical fixes when coordination is needed

### Commit Standards

Use conventional commit format:

```
type(scope): description

feat(core): add error deduplication logic
fix(logging): resolve correlation ID propagation 
docs(arch): update module dependency graph
test(quarantine): add corruption isolation tests
```

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual component behavior
2. **Integration Tests**: Component interaction
3. **Architecture Tests**: Compliance with architectural rules
4. **Health Tests**: System monitoring and degradation detection
5. **Error Flow Tests**: Error capture and remediation paths

### Test Structure

```
test/
├── unit/
│   ├── test_bootstrap.py
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_logging.py
│   ├── test_raise_af.py
│   └── test_quarantine.py
├── integration/
│   ├── test_error_flow.py
│   ├── test_system_startup.py
│   └── test_state_recovery.py
├── architecture/
│   ├── test_module_contracts.py
│   ├── test_dependency_compliance.py
│   └── test_architectural_rules.py
└── fixtures/
    └── sample_configs.py
```

### Running Tests

```bash
# Full test suite
python -m pytest test/

# Quick tests (exclude slow integration tests)
python -m pytest test/ -m "not slow"

# Specific test categories
python -m pytest test/unit/
python -m pytest test/integration/
python -m pytest test/architecture/

# Coverage reporting
python -m pytest test/ --cov=src/actifix --cov-report=html
```

### Slow/Hanging Tests

The pytest run now defaults to a 10 second timeout and automatically skips known slow/hanging files (threading barriers, concurrency-heavy ticket processing, API startup flows, etc.) unless you pass `--runslow`. Skipped tests are reported at the start of the run, and the slow-test tracker prints any tests that hit the 30 second hang threshold so you can triage the culprit before rerunning with `--runslow`.

### Test Requirements

All tests must:

- Be deterministic (same input = same output)
- Clean up after themselves
- Use proper fixtures for shared state
- Include both positive and negative cases
- Test error conditions and recovery

## Code Standards

### Python Style

```python
# Use type hints
from typing import Optional, Dict, Any

def capture_error(
    error: Exception, 
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Capture error with full context.
    
    Args:
        error: The exception to capture
        context: Additional context for error analysis
        
    Returns:
        Unique error ID for tracking
        
    Raises:
        QuarantineError: If error isolation fails
    """
    pass
```

### Error Handling Pattern

```python
from actifix import raise_af, logging

def risky_operation():
    try:
        # Risky code here
        result = dangerous_function()
        logging.info("Operation completed", extra={"result_id": result.id})
        return result
    except Exception as e:
        # All errors must flow through raise_af
        error_id = raise_af.capture_error(
            e, 
            context={
                "operation": "risky_operation",
                "correlation_id": logging.get_correlation_id()
            }
        )
        logging.error(f"Operation failed: {error_id}")
        raise  # Re-raise after capture
```

### Logging Standards

```python
from actifix import logging

# Always use structured logging
logging.info("Process started", extra={
    "process_id": process.id,
    "correlation_id": correlation_id,
    "component": "bootstrap.main"
})

# Include correlation context
with logging.correlation_context(correlation_id):
    perform_operation()
```

## Architecture Compliance

### Module Contracts

Each module must:

1. **Respect Dependencies**: Only import from declared dependencies
2. **Honor Contracts**: Implement all contracted behaviors  
3. **Single Responsibility**: Focus on one domain area
4. **Fail-Fast**: Reject invalid inputs immediately

### Dependency Rules

```python
# ✓ ALLOWED: Import from declared dependencies
from actifix.log_utils import log_event
from actifix.quarantine import isolate_error

# ✗ FORBIDDEN: Import from non-declared dependencies  
from actifix.do_af import process_ticket  # Not in dependencies

# ✗ FORBIDDEN: Circular dependencies
# raise_af.py importing from do_af.py when do_af depends on raise_af
```

### Contract Validation

```python
# Every module must validate its contracts
def validate_contracts():
    """Validate this module honors its architectural contracts."""
    assert logging_is_centralized()
    assert error_isolation_works()
    assert state_is_recoverable()
```

## Debugging and Troubleshooting

### Debug Mode

```bash
# Enable comprehensive debugging
export ACTIFIX_LOG_LEVEL=DEBUG
export ACTIFIX_DEBUG_MODE=1
python -m actifix.bootstrap --debug
```

### Health Diagnostics

```bash
# System health overview
python -m actifix.health --status

# Component-specific checks
python -m actifix.health --check-component=logging
python -m actifix.health --check-component=quarantine
python -m actifix.health --check-component=state

# Architecture validation
python -m actifix.testing --validate-architecture --verbose
```

### Error Analysis

```bash
# View recent errors
python -c "from actifix.raise_af import get_recent_errors; print(get_recent_errors())"

# Analyze error patterns
python -m actifix.raise_af --analyze-patterns

# Check quarantine status
python -m actifix.quarantine --status
```

## Contributing Guidelines

### Pull Request Checklist

- [ ] All tests pass: `python -m pytest test/`
- [ ] Coverage >= 90%: Check coverage report
- [ ] Architecture compliance: `python -m actifix.testing --validate-architecture`
- [ ] Code formatted: `black src/ test/`
- [ ] Imports sorted: `isort src/ test/`
- [ ] Type checks pass: `mypy src/actifix/`
- [ ] Documentation updated for new features
- [ ] Commit messages follow conventional format

### Review Process

1. **Automated Checks**: CI must pass all quality gates
2. **Architecture Review**: Changes affecting module contracts require architecture review
3. **Security Review**: Changes to error handling or quarantine require security review
4. **Manual Testing**: Integration scenarios must be manually verified

### Release Process

1. **Version Increment**: Update version in `pyproject.toml`
2. **Release Notes**: Document changes in `docs/FRAMEWORK_OVERVIEW.md` (Release Notes & Version History section)
3. **Changelog**: Update `CHANGELOG.md` for historical reference
4. **Architecture Update**: Refresh architecture documentation if needed
5. **Quality Validation**: Full test suite + manual verification
6. **Tag Release**: Create git tag with version

### Documentation Standards

#### No New Documentation Files
**IMPORTANT**: Do not create new documentation files (e.g., `*_PLAN.md`, `ROADMAP.md`, `DESIGN.md`, or feature-specific `.md` files). Instead:

1. **Blend into existing docs**: Add content to appropriate existing documentation files
2. **Update main docs**: Use `docs/FRAMEWORK_OVERVIEW.md` for feature documentation and release notes
3. **Update INDEX.md**: Add cross-references to new sections in existing docs
4. **Follow structure**: Maintain the existing documentation hierarchy

#### Documentation Workflow
- **Features**: Document in `docs/FRAMEWORK_OVERVIEW.md` under appropriate sections
- **Release Notes**: Add to `docs/FRAMEWORK_OVERVIEW.md` "Release Notes & Version History" section
- **API Changes**: Update `src/actifix/README.md` and relevant framework docs
- **Architecture**: Update `docs/architecture/` files for structural changes
- **Cross-reference**: Always link between related documentation

#### Why This Matters
- **Single source of truth**: Avoids fragmented documentation
- **Discoverability**: Users know where to look for information
- **Maintainability**: Easier to keep documentation current
- **Consistency**: Uniform documentation structure across the project

## Performance Considerations

### Monitoring

- **Startup Time**: Bootstrap should complete in < 5 seconds
- **Error Capture Latency**: < 100ms for error capture
- **Health Check Overhead**: < 1% of system resources
- **Log Volume**: Manageable rotation and retention

### Optimization Guidelines

- Lazy loading for non-critical components
- Efficient state serialization
- Minimal memory footprint for long-running processes
- Proper resource cleanup and garbage collection

## Security Guidelines

### Error Information

- Never log sensitive data in error contexts
- Sanitize user input in error messages
- Use secure hashing for error deduplication

### State Management

- Atomic operations for critical state
- Secure quarantine isolation
- Proper file permissions for state directories

## Documentation Standards

### Required Documentation

- **Module Documentation**: Every module needs purpose, contracts, dependencies
- **API Documentation**: All public functions need docstrings
- **Architecture Documentation**: Keep `arch/` folder current
- **User Documentation**: Installation, usage, troubleshooting guides

### Documentation Workflow

1. Document interface before implementation
2. Update architecture documentation for structural changes  
3. Include examples in documentation
4. Test documentation accuracy during CI

---

This development guide ensures consistent, high-quality contributions to actifix while maintaining architectural integrity and operational excellence.
