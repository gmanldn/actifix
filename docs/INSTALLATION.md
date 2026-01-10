# Actifix Installation Guide

## Overview

Actifix is an automatic error tracking and resolution system designed for robust operation in development and production environments. This guide covers installation, setup, and initial configuration.

## Requirements

### System Requirements

- **Python**: 3.8+ (3.9+ recommended)
- **Operating System**: Unix/Linux/macOS (Windows support via WSL)
- **Memory**: 512MB minimum, 1GB+ recommended
- **Disk Space**: 100MB for base installation + space for logs and state

### Dependencies

Core dependencies are managed via `pyproject.toml`:

- Standard library components (no external dependencies for core functionality)
- Optional integrations available for enhanced features

## Installation Methods

### Option 1: Standard Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/gmanldn/actifix.git
cd actifix

# Install in development mode
pip install -e .

# Verify installation
python -m actifix --help
```

### Option 2: Production Installation

```bash
# Install from PyPI (when available)
pip install actifix

# Or install from source
pip install git+https://github.com/gmanldn/actifix.git
```

## Configuration

### Basic Configuration

Actifix follows the principle of zero-configuration operation but supports customization:

```bash
# Create configuration directory (optional)
mkdir -p ~/.actifix

# Generate default configuration
python -m actifix.config --generate-config > ~/.actifix/config.json
```

### Environment Variables

Key environment variables:

```bash
# Core settings
export ACTIFIX_LOG_LEVEL=INFO
export ACTIFIX_LOG_DIR=./logs
export ACTIFIX_STATE_DIR=./actifix_state

# Optional integrations
export ACTIFIX_HEALTH_CHECK_INTERVAL=30
export ACTIFIX_QUARANTINE_MAX_SIZE=100MB
```

### Configuration File Structure

```json
{
  "logging": {
    "level": "INFO",
    "directory": "./logs",
    "rotation": "daily",
    "retention_days": 30
  },
  "health": {
    "check_interval": 30,
    "degraded_threshold": 5,
    "critical_threshold": 10
  },
  "quarantine": {
    "max_size": "100MB",
    "auto_cleanup": true,
    "cleanup_interval": 3600
  }
}
```

## First Run

### Initialization

```bash
# Initialize actifix system
python -m actifix.bootstrap --init

# This will:
# 1. Create necessary directories
# 2. Initialize logging system
# 3. Perform health checks
# 4. Create initial state files
```

### Verification

```bash
# Check system health
python -m actifix.health --check

# View system status
python -m actifix.health --status

# Test error capture
python -m actifix.testing --test-error-capture
```

## Integration with Existing Projects

### Python Projects

Add to your main application:

```python
from actifix import bootstrap, raise_af

# Initialize actifix
bootstrap.initialize()

# Use in your error handling
try:
    risky_operation()
except Exception as e:
    raise_af.capture_error(e, context="main_operation")
    raise
```

### CI/CD Integration

Add to your build pipeline:

```yaml
# GitHub Actions example
- name: Initialize Actifix
  run: python -m actifix.bootstrap --init

- name: Run Tests with Actifix
  run: |
    python -m actifix.bootstrap
    python -m pytest
    python -m actifix.health --report
```

## Directory Structure

After installation, actifix creates:

```
actifix_state/
├── logs/
│   ├── actifix.log
│   ├── health.log
│   └── errors/
├── quarantine/
│   └── corrupted_state/
├── tickets/
│   ├── active/
│   └── resolved/
└── config/
    └── runtime.json
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Ensure proper permissions
   chmod +x $(which python)
   mkdir -p ~/.actifix && chmod 755 ~/.actifix
   ```

2. **Path Issues**
   ```bash
   # Verify Python path
   python -c "import actifix; print(actifix.__file__)"
   ```

3. **Configuration Conflicts**
   ```bash
   # Reset configuration
   python -m actifix.config --reset
   ```

### Debug Mode

```bash
# Enable debug logging
export ACTIFIX_LOG_LEVEL=DEBUG
python -m actifix.bootstrap --debug
```

### Health Checks

```bash
# Comprehensive health check
python -m actifix.health --comprehensive

# Check specific components
python -m actifix.health --check-logging
python -m actifix.health --check-quarantine
python -m actifix.health --check-state
```

## Next Steps

After successful installation:

1. Review [DEVELOPMENT.md](DEVELOPMENT.md) for development workflow
2. See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check [TESTING.md](TESTING.md) for quality assurance
4. Read [MONITORING.md](MONITORING.md) for operational guidance

## Support

- **Documentation**: Full docs in `docs/` directory
- **Issues**: Report via GitHub Issues
- **Architecture**: See `arch/` folder for technical details
