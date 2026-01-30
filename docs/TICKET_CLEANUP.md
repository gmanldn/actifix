# Ticket Cleanup and Retention Policies

This document describes the automatic ticket cleanup and retention policy features that prevent ticket accumulation over time.

## Overview

Actifix now includes automatic cleanup mechanisms to prevent tickets from accumulating indefinitely. The system provides:

1. **Enhanced Deduplication** - Prevents duplicate tickets even after completion
2. **Retention Policies** - Automatically removes old completed tickets
3. **Test Ticket Cleanup** - Auto-completes or removes test/automation tickets
4. **Manual Cleanup Tools** - Scripts for manual cleanup operations
5. **API Endpoints** - Web API for triggering cleanup from the dashboard

## Features

### 1. Enhanced Deduplication

**What changed:**
- Previously, the duplicate check only prevented duplicates for `Open` or `In Progress` tickets
- Now, ALL tickets (including `Completed`) are checked for duplicates
- This prevents the same issue from creating new tickets after being fixed

**Location:** `src/actifix/raise_af.py:881-891`

**Impact:**
- Once an issue is recorded and fixed, it won't create new tickets if it occurs again
- Reduces ticket noise from recurring test failures or automation scripts

### 2. Retention Policies

Automatically soft-deletes old completed tickets based on configurable retention periods.

**Default Settings:**
- Regular completed tickets: **90 days** retention
- Test/automation tickets: **7 days** retention

**Test Ticket Detection:**

The system identifies test tickets by:
- **Source patterns**: `start_weakness_analysis_300.py`, `simple_ticket_attack.py`, etc.
- **Error types**: `WeaknessAnalysis`, `CodeElegance`, `TestError`, `TestPerformance`, etc.
- **Test markers**: Sources containing `test.`, `test/`, or `pytest`

### 3. Automatic Cleanup Mechanism

The cleanup system:
1. Identifies expired tickets based on retention policy
2. Soft-deletes them (marks as deleted, preserves data)
3. Removes them from normal queries and stats
4. Allows recovery if needed via `recover_ticket()`

## Configuration

### Environment Variables

```bash
# Enable/disable automatic cleanup
export ACTIFIX_CLEANUP_ENABLED=true

# Days to keep regular completed tickets
export ACTIFIX_RETENTION_DAYS=90

# Days to keep test/automation tickets
export ACTIFIX_TEST_RETENTION_DAYS=7

# Auto-complete test tickets instead of deleting
export ACTIFIX_AUTO_COMPLETE_TESTS=true

# Run cleanup during health checks (not recommended for production)
export ACTIFIX_CLEANUP_ON_HEALTH=false

# Minimum hours between automatic cleanup runs
export ACTIFIX_CLEANUP_MIN_HOURS=24
```

### Programmatic Configuration

```python
from actifix import CleanupConfig, set_cleanup_config

# Create custom config
config = CleanupConfig(
    enabled=True,
    retention_days=30,  # Keep tickets for 30 days
    test_ticket_retention_days=1,  # Keep test tickets for 1 day
    auto_complete_test_tickets=True,
    run_on_health_check=False,
    min_hours_between_runs=24
)

# Set as global config
set_cleanup_config(config)
```

## Usage

### Manual Cleanup Script

Run cleanup from the command line:

```bash
# Dry run - preview what would be cleaned
cd scripts
python3 run_cleanup.py

# Execute cleanup
python3 run_cleanup.py --execute

# Custom retention periods
python3 run_cleanup.py --execute --retention-days 30 --test-retention-days 3

# Delete test tickets instead of auto-completing
python3 run_cleanup.py --execute --no-auto-complete

# Keep all completed tickets, only clean test tickets
python3 run_cleanup.py --execute --retention-days 999999 --test-retention-days 1
```

### Programmatic API

```python
from actifix import run_automatic_cleanup

# Run with defaults (dry run)
results = run_automatic_cleanup(dry_run=True)

# Execute cleanup with custom settings
results = run_automatic_cleanup(
    retention_days=60,
    test_ticket_retention_days=3,
    auto_complete_test_tickets=True,
    dry_run=False  # Actually apply changes
)

# Check results
print(f"Deleted: {results['retention_policy']['total_deleted']}")
print(f"Test tickets cleaned: {results['test_cleanup']['test_tickets_cleaned']}")
```

### REST API Endpoints

#### Run Cleanup

```bash
# Dry run (preview only)
curl -X POST http://localhost:5050/api/cleanup \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# Execute cleanup with defaults
curl -X POST http://localhost:5050/api/cleanup \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# Execute with custom settings
curl -X POST http://localhost:5050/api/cleanup \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false,
    "retention_days": 30,
    "test_retention_days": 1,
    "auto_complete_test_tickets": true
  }'
```

#### Get Cleanup Configuration

```bash
curl http://localhost:5050/api/cleanup/config
```

## Cleanup Report

When you run cleanup, you'll get a detailed report:

```
================================================================================
AUTOMATIC TICKET CLEANUP REPORT
================================================================================

Timestamp: 2026-01-18T06:45:38.804634+00:00
Mode: DRY RUN (no changes made)

--------------------------------------------------------------------------------
RETENTION POLICY CLEANUP:
--------------------------------------------------------------------------------
  Regular completed tickets expired: 150
  Test tickets expired: 500
  Total deleted: 650

--------------------------------------------------------------------------------
TEST TICKET CLEANUP:
--------------------------------------------------------------------------------
  Open test tickets found: 300
  Test tickets cleaned: 300

================================================================================
To apply these changes, run with dry_run=False
================================================================================
```

## Scheduled Cleanup

To run cleanup automatically on a schedule, use a cron job:

```bash
# Run cleanup daily at 2 AM
0 2 * * * cd /path/to/actifix/scripts && python3 run_cleanup.py --execute

# Run ticket consolidation daily at 4 AM
0 4 * * * cd /path/to/actifix/scripts && python3 consolidate_ticket_buckets.py --execute

# Run cleanup weekly on Sunday at 3 AM
0 3 * * 0 cd /path/to/actifix/scripts && python3 run_cleanup.py --execute
```

Or use a systemd timer:

```ini
# /etc/systemd/system/actifix-cleanup.timer
[Unit]
Description=Actifix Daily Cleanup Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/actifix-cleanup.service
[Unit]
Description=Actifix Ticket Cleanup

[Service]
Type=oneshot
WorkingDirectory=/path/to/actifix/scripts
ExecStart=/usr/bin/python3 run_cleanup.py --execute
User=your-user
```

```ini
# /etc/systemd/system/actifix-ticket-consolidation.service
[Unit]
Description=Actifix Ticket Consolidation

[Service]
Type=oneshot
WorkingDirectory=/path/to/actifix/scripts
ExecStart=/usr/bin/python3 consolidate_ticket_buckets.py --execute
User=your-user
```

```ini
# /etc/systemd/system/actifix-ticket-consolidation.timer
[Unit]
Description=Actifix Daily Ticket Consolidation

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Then enable and start:

```bash
sudo systemctl enable actifix-cleanup.timer
sudo systemctl start actifix-cleanup.timer
```

## Soft Delete vs Hard Delete

By default, tickets are **soft-deleted**:
- Marked as `deleted=1` in database
- Excluded from stats and normal queries
- Data preserved for auditing
- Can be recovered using `repo.recover_ticket(ticket_id)`

To hard-delete (permanent removal):

```python
from actifix.persistence.ticket_repo import get_ticket_repository

repo = get_ticket_repository()
repo.delete_ticket('ACT-20260118-xxx', soft_delete=False)
```

## Monitoring

Check cleanup statistics in logs or via API:

```python
from actifix.persistence.ticket_repo import get_ticket_repository

repo = get_ticket_repository()
stats = repo.get_stats()

print(f"Total tickets: {stats['total']}")
print(f"Deleted tickets: {stats['deleted']}")
```

Verify scheduled consolidation runs:

```bash
# Cron: confirm entries exist and review recent output/logs
crontab -l | grep consolidate_ticket_buckets

# systemd: confirm timer status and last/next run
systemctl status actifix-ticket-consolidation.timer
systemctl list-timers --all | grep ticket-consolidation
```

If consolidation reports missing or stale runs, trigger a manual dry run followed by execution:

```bash
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 scripts/consolidate_ticket_buckets.py --limit 25
python3 scripts/consolidate_ticket_buckets.py --execute
```

## Daily Verification Steps

To ensure ticket consolidation and cleanup are running correctly, perform these daily verification steps:

### 1. Verify Scheduled Jobs Are Running

**For Cron:**
```bash
# Check if consolidation cron job exists
crontab -l | grep consolidate_ticket_buckets

# View recent cron execution logs (location varies by system)
grep consolidate_ticket_buckets /var/log/syslog  # Debian/Ubuntu
grep consolidate_ticket_buckets /var/log/cron    # CentOS/RHEL
```

**For Systemd:**
```bash
# Check timer status and next run time
systemctl status actifix-ticket-consolidation.timer

# View recent execution history
systemctl list-timers --all | grep ticket-consolidation

# Check last run logs
journalctl -u actifix-ticket-consolidation.service --since "24 hours ago"
```

### 2. Check Consolidation Output

```bash
# Review consolidation script output logs
tail -n 50 /var/log/actifix/consolidation.log

# Look for completion timestamp and ticket counts
grep "Consolidation complete" /var/log/actifix/consolidation.log | tail -5
```

### 3. Verify Ticket Statistics

```python
from actifix.persistence.ticket_repo import get_ticket_repository

repo = get_ticket_repository()
stats = repo.get_stats()

# Check for expected ranges
print(f"Total active tickets: {stats['total']}")
print(f"Open tickets: {stats['open']}")
print(f"Completed tickets: {stats['completed']}")
print(f"Deleted (cleaned up): {stats['deleted']}")

# Alert if numbers seem abnormal (adjust thresholds for your environment)
if stats['open'] > 1000:
    print("⚠️  Warning: High open ticket count - review for duplicates")
if stats['deleted'] > stats['total'] * 0.5:
    print("⚠️  Warning: High deletion rate - verify retention policy is correct")
```

### 4. Check for Stuck/Old Open Tickets

```bash
# Use the Actifix CLI to find old open tickets
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.main stats --old-only

# Or query directly
python3 << 'EOF'
from actifix.persistence.ticket_repo import get_ticket_repository
from datetime import datetime, timedelta, timezone

repo = get_ticket_repository()
cutoff = datetime.now(timezone.utc) - timedelta(days=30)

# Get tickets older than 30 days that are still open
old_tickets = [t for t in repo.get_open_tickets()
               if t.get('created_at') < cutoff]

if old_tickets:
    print(f"Found {len(old_tickets)} open tickets older than 30 days:")
    for t in old_tickets[:10]:
        print(f"  {t['id']}: {t['message'][:60]}...")
else:
    print("✓ No stale open tickets found")
EOF
```

### 5. Verify Recent Consolidation Activity

```bash
# Check if consolidation ran in last 24 hours
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 << 'EOF'
from pathlib import Path
from datetime import datetime, timedelta

consolidation_log = Path("logs/consolidation.log")  # Adjust path as needed
if consolidation_log.exists():
    mtime = datetime.fromtimestamp(consolidation_log.stat().st_mtime)
    age = datetime.now() - mtime
    if age < timedelta(hours=26):  # 24h + 2h buffer
        print(f"✓ Consolidation ran {age.total_seconds() / 3600:.1f} hours ago")
    else:
        print(f"⚠️  Warning: Last consolidation was {age.total_seconds() / 3600:.1f} hours ago")
else:
    print("⚠️  Warning: No consolidation log found")
EOF
```

### 6. Quick Health Check

```bash
# Run Actifix health check to ensure cleanup didn't break anything
export ACTIFIX_CHANGE_ORIGIN=raise_af
python3 -m actifix.main health

# Expected output should show OK status and no errors
```

### 7. Spot Check Recent Deletions

```python
from actifix.persistence.ticket_repo import get_ticket_repository

repo = get_ticket_repository()

# Review recently deleted tickets to ensure retention policy is working correctly
deleted = repo.get_deleted_tickets()[:20]  # Get last 20 deleted

print(f"Recently deleted tickets: {len(deleted)}")
for t in deleted[:5]:
    print(f"  {t['id']}: deleted={t.get('deleted_at')} | {t['message'][:50]}...")

# Verify they match expected patterns (test tickets, old completed tickets)
```

### Automated Daily Verification Script

Create a daily verification script:

```bash
#!/bin/bash
# /path/to/actifix/scripts/daily_verification.sh

echo "=== Actifix Daily Verification $(date) ==="

export ACTIFIX_CHANGE_ORIGIN=raise_af

# 1. Check ticket stats
echo -e "\n1. Ticket Statistics:"
python3 -m actifix.main stats | head -20

# 2. Verify consolidation ran
echo -e "\n2. Recent Consolidation:"
if systemctl is-active --quiet actifix-ticket-consolidation.timer; then
    systemctl status actifix-ticket-consolidation.timer | grep -A2 "Trigger:"
else
    echo "Checking cron logs..."
    grep consolidate_ticket_buckets /var/log/syslog | tail -3
fi

# 3. Check for anomalies
echo -e "\n3. Health Check:"
python3 -m actifix.main health | grep -E "(status|tickets|errors)"

echo -e "\n=== Verification Complete ==="
```

Make it executable and run daily:

```bash
chmod +x scripts/daily_verification.sh

# Add to cron
echo "30 8 * * * /path/to/actifix/scripts/daily_verification.sh >> /var/log/actifix/daily_verification.log 2>&1" | crontab -
```

## Best Practices

1. **Always dry-run first** - Preview changes before executing
2. **Start conservative** - Use longer retention periods initially
3. **Monitor after cleanup** - Check stats to ensure expected behavior
4. **Schedule during off-hours** - Run cleanup when system usage is low
5. **Keep audit logs** - Soft-delete allows recovery if needed
6. **Test ticket hygiene** - Disable test ticket creation in production
7. **Daily verification** - Run verification checks daily to catch issues early
8. **Alert on anomalies** - Set up monitoring to alert when ticket counts are abnormal

## Troubleshooting

### Issue: Too many tickets being deleted

**Solution:** Increase retention periods or adjust test ticket patterns in `ticket_cleanup.py`

### Issue: Test tickets not being detected

**Solution:** Add your test source patterns to `TEST_SOURCES` or `TEST_ERROR_TYPES` in `src/actifix/persistence/ticket_cleanup.py`

### Issue: Cleanup not running automatically

**Solution:**
- Check `ACTIFIX_CLEANUP_ENABLED` is set to `true`
- Verify cron job or systemd timer is configured correctly
- Check application logs for errors

### Issue: Need to recover deleted tickets

**Solution:**
```python
from actifix.persistence.ticket_repo import get_ticket_repository

repo = get_ticket_repository()

# Get deleted tickets
deleted = repo.get_deleted_tickets()

# Recover a specific ticket
repo.recover_ticket('ACT-20260118-xxx')
```
## Related Files

- `src/actifix/persistence/ticket_repo.py` - Cleanup implementation
- `src/actifix/persistence/cleanup_config.py` - Configuration management
- `src/actifix/raise_af.py` - Enhanced deduplication logic
- `scripts/run_cleanup.py` - Manual cleanup script
- `src/actifix/api.py` - REST API endpoints
- `scripts/consolidate_ticket_buckets.py` - Identify redundant ticket buckets for consolidation

## Migration Notes

If you're upgrading from an earlier version:

1. No database migration needed - soft-delete uses existing `deleted` column
2. Enhanced deduplication is backward compatible
3. Existing tickets are not affected until cleanup is run
4. Configuration defaults preserve existing behavior (90-day retention)

## See Also

- [Testing Guide](TESTING.md)
- [Architecture Overview](architecture/OVERVIEW.md)
- [API Documentation](API.md)
