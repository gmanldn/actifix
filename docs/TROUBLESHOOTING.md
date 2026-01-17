# Actifix Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Issue: Import errors when using Actifix
```
ModuleNotFoundError: No module named 'actifix'
```

**Solution:**
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/actifix/src"

# Or install in development mode
pip install -e .
```

#### Issue: Permission denied when creating directories
**Solution:**
```bash
# Check directory permissions
ls -la actifix/
chmod 755 actifix/

# Ensure user has write access
sudo chown -R $USER:$USER actifix/
```

### Configuration Issues

#### Issue: Environment variables not recognized
**Solution:**
```bash
# Verify environment variables
env | grep ACTIFIX

# Set required variables
export ACTIFIX_CHANGE_ORIGIN=raise_af
export ACTIFIX_CAPTURE_ENABLED=1
```

#### Issue: Invalid configuration values
**Solution:**
```bash
# Validate configuration
python -c "from actifix.config import load_config; print(load_config())"

# Reset to defaults
python -m actifix.config --reset
```

### Runtime Issues

#### Issue: UI shows outdated version after restart
**Symptoms:**
- Dashboard shows previous version even after updating/restarting

**Solution:**
- Launcher kills stale frontend processes on startup and version changes.
- Front-end auto-detects version changes and reloads the page to show the latest version.

#### Issue: Tickets not being created
**Symptoms:**
- `record_error()` returns None
- No rows in `data/actifix.db`'s `tickets` table

**Diagnosis:**
```bash
# Check if capture is enabled
python -c "import os; print(os.environ.get('ACTIFIX_CAPTURE_ENABLED'))"

# Verify raise_af workflow
python -c "import os; print(os.environ.get('ACTIFIX_CHANGE_ORIGIN'))"
```

**Solution:**
```bash
# Enable capture
export ACTIFIX_CAPTURE_ENABLED=1
export ACTIFIX_CHANGE_ORIGIN=raise_af

# Test ticket creation
python -c "
from actifix.raise_af import record_error
entry = record_error('Test error', 'test/test_runner.py:1')
print(f'Created: {entry.entry_id if entry else None}')
"
```

#### Issue: Database connection errors
**Symptoms:**
- SQLite database locked
- Connection timeout errors

**Solution:**
```bash
# Check database file permissions
ls -la data/actifix.db

# Kill any hanging connections
pkill -f actifix

# Repair database if corrupted
python -c "
from actifix.persistence.database import DatabaseManager
db = DatabaseManager()
db.repair_database()
"
```

#### Issue: High memory usage
**Symptoms:**
- Process consuming excessive RAM
- System becoming unresponsive

**Diagnosis:**
```bash
# Monitor memory usage
ps aux | grep actifix
top -p $(pgrep -f actifix)
```

**Solution:**
```bash
# Enable memory profiling
export ACTIFIX_MEMORY_PROFILING=1

# Check for memory leaks
python -m actifix.health --check-memory

# Restart with clean state
python -m actifix.bootstrap --clean-restart
```

### Performance Issues

#### Issue: Slow startup time
**Symptoms:**
- Bootstrap takes > 5 seconds
- System feels sluggish

**Diagnosis:**
```bash
# Profile startup time
time python -m actifix.bootstrap --init

# Enable startup profiling
export ACTIFIX_STARTUP_PROFILING=1
python -m actifix.bootstrap --profile
```

**Solution:**
```bash
# Enable lazy loading
export ACTIFIX_LAZY_LOADING=1

# Optimize database
python -c "
from actifix.persistence.database import DatabaseManager
db = DatabaseManager()
db.optimize()
"
```

#### Issue: Slow error capture
**Symptoms:**
- `record_error()` takes > 100ms
- Noticeable delays in error handling

**Solution:**
```bash
# Disable context capture for performance
python -c "
from actifix.raise_af import record_error
record_error('Fast error', 'test/test_runner.py:1', capture_context=False)
"

# Optimize file operations
export ACTIFIX_ASYNC_WRITES=1
```

### File System Issues

#### Issue: Disk space full
**Symptoms:**
- Cannot create new tickets
- Log files not being written

**Diagnosis:**
```bash
# Check disk usage
df -h
du -sh actifix/ .actifix/ logs/
```

**Solution:**
```bash
# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Compress old tickets
python -m actifix.maintenance --compress-old-tickets

# Enable log rotation
export ACTIFIX_LOG_ROTATION=1
```

#### Issue: File corruption
**Symptoms:**
- JSON parsing errors
- Malformed ticket files

**Diagnosis:**
```bash
# Check file integrity
python -m actifix.quarantine --check-integrity

# Validate JSON files
find actifix/ -name "*.json" -exec python -m json.tool {} \; > /dev/null
```

**Solution:**
```bash
# Quarantine corrupted files
python -m actifix.quarantine --isolate-corrupted

# Restore from backup
python -m actifix.backup --restore-latest

# Rebuild from audit log
python -m actifix.recovery --rebuild-from-audit
```

### Testing Issues

#### Issue: Tests failing with coverage below 95%
**Solution:**
```bash
# Generate coverage report
python test/test_runner.py --coverage --html

# Identify missing coverage
coverage report --show-missing

# Add tests for uncovered lines
# See docs/TESTING.md for guidelines
```

#### Issue: Flaky tests
**Symptoms:**
- Tests pass/fail inconsistently
- Race conditions in test execution

**Solution:**
```bash
# Run tests with isolation
python -m pytest test/ --forked

# Use proper fixtures
# See test/conftest.py for examples

# Enable deterministic mode
export ACTIFIX_DETERMINISTIC_MODE=1
```

### AI Integration Issues

#### Issue: AI provider failures
**Symptoms:**
- Claude API errors
- OpenAI timeout errors

**Diagnosis:**
```bash
# Check AI provider status
python -c "
from actifix.ai_client import test_providers
test_providers()
"
```

**Solution:**
```bash
# Configure fallback providers
export ACTIFIX_AI_FALLBACK_ENABLED=1

# Use local models
export ACTIFIX_USE_OLLAMA=1

# Disable AI temporarily
export ACTIFIX_AI_ENABLED=0
```

## Diagnostic Commands

### System Health Check
```bash
# Comprehensive health check
python -m actifix.health --comprehensive

# Component-specific checks
python -m actifix.health --check-component=logging
python -m actifix.health --check-component=quarantine
python -m actifix.health --check-component=database
```

### Architecture Validation
```bash
# Validate architecture compliance
python -m actifix.testing --validate-architecture --verbose

# Check module dependencies
python -c "
from actifix.testing.system import validate_module_dependencies
violations = validate_module_dependencies()
print(f'Violations: {violations}')
"
```

### Log Analysis
```bash
# View recent errors
sqlite3 data/actifix.db "SELECT timestamp, event_type, message FROM event_log WHERE level='ERROR' ORDER BY timestamp DESC LIMIT 50;"

# Check audit trail
sqlite3 data/actifix.db "SELECT timestamp, event_type, message FROM event_log ORDER BY timestamp DESC LIMIT 100;"

# Analyze error patterns
python -m actifix.analysis --error-patterns
```

## Emergency Procedures

### Emergency Bypass
```bash
# Disable enforcement for emergency fixes
export ACTIFIX_ENFORCE_RAISE_AF=0

# Emergency restart
python -m actifix.emergency --restart

# Safe mode startup
python -m actifix.bootstrap --safe-mode
```

### Data Recovery
```bash
# Backup current state
python -m actifix.backup --create-emergency-backup

# Restore from backup
python -m actifix.backup --restore-emergency

# Rebuild from audit log
python -m actifix.recovery --rebuild-all
```

## Getting Help

### Debug Information Collection
```bash
# Collect debug information
python -m actifix.debug --collect-info > debug_info.txt

# Include in bug reports:
# - Actifix version
# - Python version
# - Operating system
# - Environment variables
# - Recent log entries
# - Error stack traces
```

### Support Channels
1. **Documentation**: Check docs/ directory
2. **Architecture**: Review docs/architecture/
3. **GitHub Issues**: Report bugs and feature requests
4. **Debug Mode**: Enable verbose logging for investigation

### Bug Report Template
```
**Actifix Version**: 2.7.0
**Python Version**: 3.10.x
**OS**: macOS/Linux/Windows
**Environment Variables**: 
- ACTIFIX_CAPTURE_ENABLED=1
- ACTIFIX_CHANGE_ORIGIN=raise_af

**Issue Description**:
[Describe the problem]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Error Messages**:
```
[Include any error messages or stack traces]
```

**Additional Context**:
[Any other relevant information]
