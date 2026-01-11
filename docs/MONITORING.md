# Actifix Monitoring Guide

## Overview

This guide covers operational monitoring, health checks, and observability for Actifix in production environments.

## Health Monitoring

### Health Check Endpoint
```bash
# Check system health
python -m actifix.health --check

# Comprehensive health report
python -m actifix.health --comprehensive
```

### Health Status Levels
- **OK**: All systems operational
- **WARNING**: Minor issues detected
- **ERROR**: Significant problems
- **SLA_BREACH**: Critical SLA violations

## Key Metrics

### System Metrics
- Startup time (target: < 5 seconds)
- Memory usage
- Error capture latency (target: < 100ms)
- Ticket processing throughput

### Business Metrics
- Open tickets by priority
- SLA breach count
- Error classification accuracy
- AI remediation success rate

## Alerting

### Critical Alerts (P0)
- System startup failures
- Database corruption
- Health check failures
- SLA breaches

### Warning Alerts (P1-P2)
- High error rates
- Performance degradation
- Storage capacity issues
- AI provider failures

## Log Monitoring

### Log Locations
- Application logs: `logs/actifix.log`
- Health logs: `logs/health.log`
- Error logs: `logs/errors/`
- Audit logs: `actifix/AFLog.txt`

### Log Patterns to Monitor
```bash
# Critical errors
grep "CRITICAL\|FATAL" logs/actifix.log

# SLA breaches
grep "SLA_BREACH" logs/health.log

# Database issues
grep "database\|sqlite" logs/actifix.log | grep -i error
```

## Performance Monitoring

### Startup Performance
```bash
# Monitor startup time
time python -m actifix.bootstrap --init
```

### Memory Monitoring
```bash
# Check memory usage
ps aux | grep actifix
```

### Disk Usage
```bash
# Monitor storage usage
du -sh actifix/ .actifix/ logs/
```

## Troubleshooting

### Common Issues
1. **High memory usage**: Check for memory leaks
2. **Slow startup**: Review initialization sequence
3. **Database locks**: Check for concurrent access
4. **Storage full**: Implement log rotation

### Debug Commands
```bash
# Enable debug logging
export ACTIFIX_LOG_LEVEL=DEBUG

# Check quarantine status
python -m actifix.quarantine --status

# Validate architecture
python -m actifix.testing --validate-architecture
