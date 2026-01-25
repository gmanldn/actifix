# Actifix Monitoring Guide

This guide covers health checks, operational visibility, and recommended monitoring queries for Actifix deployments.

## Health checks
```bash
python3 -m actifix.main health
```

Health checks summarize:
- Ticket backlog
- SLA breaches
- Storage state and quarantine
- Recent errors in the event log
- DoAF agent heartbeat (last updated timestamp)

## Key metrics to monitor
- Startup time (target: < 5s)
- Error capture latency (target: < 100ms)
- Open tickets by priority
- SLA breach count
- DoAF processing throughput
- Database file size and WAL growth

## Query the database
Actifix stores operational signals in `data/actifix.db`.

```bash
# Recent tickets
sqlite3 data/actifix.db "SELECT id, priority, status, message FROM tickets ORDER BY created_at DESC LIMIT 20;"

# SLA breaches (Open tickets past SLA)
sqlite3 data/actifix.db "SELECT id, priority, created_at FROM tickets WHERE status != 'Completed' ORDER BY created_at DESC LIMIT 50;"

# Recent events
sqlite3 data/actifix.db "SELECT timestamp, level, event_type, message FROM event_log ORDER BY timestamp DESC LIMIT 50;"
```

## Log locations
- Event log: `data/actifix.db` (`event_log` table)
- Optional runtime logs: `logs/` (if configured)
- Actifix state: `.actifix/`

## Alerting guidance
Critical alerts (P0):
- Database corruption or inaccessible `data/actifix.db`
- Health checks failing consistently
- DoAF processing stuck with growing backlog

Warning alerts (P1-P2):
- Rapid growth of open tickets
- Repeated throttling events for P2/P3/P4
- Slow capture latency or startup time regressions

## Performance monitoring
```bash
# Measure startup time
(time python3 -m actifix.main health) 2>/dev/null

# Check disk usage
du -sh data/ .actifix/ logs/
```

## Operational checks
```bash
# Quarantined entries
python3 -m actifix.main quarantine list

# Ticket stats summary
python3 -m actifix.main stats
```
