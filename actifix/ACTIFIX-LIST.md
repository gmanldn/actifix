# Actifix Ticket List

Tickets generated from errors. Update checkboxes as work progresses.

**Status Legend:**
- `[ ]` Pending - Not started
- `[~]` In Progress - Currently being worked on  
- `[x]` Complete - Done and verified

## Active Items

<!-- New tickets are inserted here by RaiseAF -->

### ACT-20251220-75CA0A - [P1] Enhancement: Add atomic writes + fsync for Actifix artifacts to prevent partial writes

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:27.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-8190a3be`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented atomic_write() and atomic_write_bytes() functions with write-to-temp-then-rename pattern and fsync for durability. Cross-platform support (Windows, macOS, Linux). Full test coverage in test_actifix_log_utils.py.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add atomic writes + fsync for Actifix artifacts to prevent partial writes
Source Location: Actifix/log_utils.py
Priority: P1

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-F333DB - [P1] Enhancement: Introduce cross-process file locking for Actifix artifact updates

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/thread_safe.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:28.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-thread_safe-py-97ea7de0`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented CrossProcessLock class using filelock library with stale lock detection and recovery. Thread-safe coordination via RLock. Multi-file lock acquisition with consistent ordering for deadlock prevention. Full test coverage in test_actifix_thread_safe.py.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Introduce cross-process file locking for Actifix artifact updates
Source Location: Actifix/thread_safe.py
Priority: P1

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-617FDB - [P1] Enhancement: Add DoAF run lock with stale lock recovery to prevent concurrent runs

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:34.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-8ff53c7d`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented doaf_run_lock() context manager with stale lock recovery (10-minute threshold). Uses JSON lock file with PID/timestamp/hostname. Lock acquisition with configurable timeout. Full test coverage verified.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add DoAF run lock with stale lock recovery to prevent concurrent runs
Source Location: Actifix/DoAF.py
Priority: P1

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-A81C40 - [P2] Enhancement: Trim AFLog by line boundaries to avoid corrupt entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:42.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-7ab569d1`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented trim_to_line_boundary() function in log_utils.py. Trims content at line boundaries to avoid corrupt/partial log entries. Used by append_with_guard() when file exceeds max size.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Trim AFLog by line boundaries to avoid corrupt entries
Source Location: Actifix/log_utils.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-C1CF83 - [P2] Enhancement: Use temp+rename for ACTIFIX-LOG.md appends for durability

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:43.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-ca484b53`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Updated _update_log() in DoAF.py to use atomic_write() from log_utils.py for durable ACTIFIX-LOG.md writes. Uses temp+rename pattern with fsync.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Use temp+rename for ACTIFIX-LOG.md appends for durability
Source Location: Actifix/DoAF.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-5B54D7 - [P1] Enhancement: Add test timeout handling in DoAF to avoid hung runs

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:44.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-d32da429`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Test timeout of 600s (10 minutes) implemented in DoAF._run_tests().

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add test timeout handling in DoAF to avoid hung runs
Source Location: Actifix/DoAF.py
Priority: P1

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-C0323D - [P2] Enhancement: Add git preflight checks in DoAF (dirty/detached/remote)

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:45.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-88801190`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented git_preflight_checks() in DoAF.py with GitPreflightResult dataclass. Checks for dirty working tree, detached HEAD, and remote tracking branch. Returns structured result with warnings and errors.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add git preflight checks in DoAF (dirty/detached/remote)
Source Location: Actifix/DoAF.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-E574C8 - [P2] Enhancement: Classify Claude client failures and log to AFLog with context

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/claude_client.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:46.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-claude_client-py-f33c77a6`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Added FailureType enum (timeout, os_error, cli_not_available, cli_error, unknown) and log_failure_to_aflog() function. Updated send_prompt() to log all failures to AFLog.txt with classification and context.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Classify Claude client failures and log to AFLog with context
Source Location: Actifix/claude_client.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-C4948E - [P2] Enhancement: Add backup freshness check to Actifix health report

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:47.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-ae1f4a65`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented check_backup_freshness() in health.py. Scans backup directory for .tar.gz and .zip files, tracks newest/oldest backup age in hours, warns when newest backup exceeds 24-hour threshold.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add backup freshness check to Actifix health report
Source Location: Actifix/health.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-A42DBD - [P2] Enhancement: Schedule hourly backups with AFLog audit entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:48.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-04c8b7ef`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Added _log_to_aflog() helper in backup.py. Updated create_backup(), restore_from_backup(), and cleanup_old_backups() to log all operations to AFLog.txt with event types: BACKUP_CREATED, BACKUP_RESTORED, BACKUP_RESTORE_FAILED, BACKUP_RESTORE_PARTIAL, BACKUP_CLEANUP.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Schedule hourly backups with AFLog audit entries
Source Location: Actifix/backup.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-ACAB3E - [P3] Enhancement: Add restore drill command to validate backups in temp dir

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:49.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-93225275`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented restore_drill() function and CLI 'drill' command in backup.py. Validates backup integrity by restoring to temp directory, checking file readability and content. Logs results to AFLog.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add restore drill command to validate backups in temp dir
Source Location: Actifix/backup.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-BE34AC - [P3] Enhancement: Emit backup retention audit report and cleanup summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:51.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-1c46f40c`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented get_retention_report() function and CLI 'report' command in backup.py. Generates audit report with total backups, age distribution buckets, recommendations, and logs to AFLog.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Emit backup retention audit report and cleanup summary
Source Location: Actifix/backup.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-5DE656 - [P3] Enhancement: Warn when ACTIFIX-LIST size exceeds threshold

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:52.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-fa152ece`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented check_list_size() in health.py. Checks ACTIFIX-LIST.md file size with warning threshold at 500KB and critical threshold at 1MB. Integrated into get_health() health check routine.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Warn when ACTIFIX-LIST size exceeds threshold
Source Location: Actifix/health.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-CD6689 - [P2] Enhancement: Add strict schema validator + lint command for ACTIFIX-LIST

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:53.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-74e53777`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented validate_ticket_schema() and lint_actifix_list() methods in ActifixHealthCheck class. Added lint_tickets() convenience function. Validates required fields (ticket ID, priority, error type, source, created, checklist) and checks for complete checklists.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add strict schema validator + lint command for ACTIFIX-LIST
Source Location: Actifix/health.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-5D1C76 - [P3] Enhancement: Add ticket format_version field to support future migrations

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:54.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-96ebf003`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Added TICKET_FORMAT_VERSION constant ("1.0") and format_version field to ActifixEntry dataclass. Enables future migrations by tracking ticket format version in each entry.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add ticket format_version field to support future migrations
Source Location: Actifix/RaiseAF.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-D081E2 - [P2] Enhancement: Quarantine malformed ticket blocks instead of failing DoAF parse

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:55.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-75d63ead`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented quarantine_ticket() function in DoAF.py. Moves malformed tickets to Actifix/quarantine/ directory with timestamp suffix. Logs quarantine events to AFLog. Prevents parse failures from blocking DoAF.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Quarantine malformed ticket blocks instead of failing DoAF parse
Source Location: Actifix/DoAF.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-8DF7C8 - [P3] Enhancement: Normalize ticket ordering (newest first) after DoAF updates

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:56.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-0f191412`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented normalize_ticket_order() function in DoAF.py. Parses ACTIFIX-LIST content, extracts creation dates from tickets, and reorders active tickets by date (newest first). Uses _parse_list() and _compose_content() helpers.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Normalize ticket ordering (newest first) after DoAF updates
Source Location: Actifix/DoAF.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-694ECD - [P3] Enhancement: Expose oldest active ticket age in health summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:57.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-c12b35d4`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Enhanced check_ticket_queue() in health.py to add oldest_active_age_days field. Updated get_status_summary() to display oldest ticket age. Parses Created date from ACTIFIX-LIST.md and calculates days since creation.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Expose oldest active ticket age in health summary
Source Location: Actifix/health.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-B3187A - [P2] Enhancement: Add concurrency test for thread_safe_record_error (multi-thread)

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_thread_safe.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:59.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_thread_safe-py-5e340098`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Already implemented as test_concurrent_record_errors() in test_actifix_thread_safe.py. Tests 10 concurrent threads calling thread_safe_record_error(), verifies no errors and all 10 complete successfully.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add concurrency test for thread_safe_record_error (multi-thread)
Source Location: tests/test_actifix_thread_safe.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-5BD6AB - [P3] Enhancement: Test log_utils trimming with UTF-8 boundary cases

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:00.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_log_utils-py-44c08d54`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Already implemented with test_atomic_write_unicode_content() and UTF-8 encoding tests in test_actifix_log_utils.py. Tests verify unicode content handling and max size enforcement.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Test log_utils trimming with UTF-8 boundary cases
Source Location: tests/test_actifix_log_utils.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-CD992A - [P3] Enhancement: Test ACTIFIX.md rollup cap (max 20 entries)

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_rollup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:03.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_rollup-py-2f299535`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Already implemented with rollup drift tests, rebuild_rollup_from_list(), and related tests in test_actifix.py. Tests verify rollup behavior including TestRollupDriftDetection class.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Test ACTIFIX.md rollup cap (max 20 entries)
Source Location: tests/test_actifix_rollup.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-BFAE62 - [P3] Enhancement: Test backup create/restore/cleanup flows for Actifix

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:04.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_backup-py-b3bc8f69`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Already implemented with test_cleanup_removes_old_backups(), test_cleanup_keeps_recent_backups(), and comprehensive backup tests in test_actifix_backup.py.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Test backup create/restore/cleanup flows for Actifix
Source Location: tests/test_actifix_backup.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-8FE939 - [P3] Enhancement: Test duplicate guard generation determinism

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_dedup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:05.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_dedup-py-0f0e0c35`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Already implemented with test_raise_af_generates_duplicate_guard() and test_actifix_list_duplicate_guards_unique() in test_actifix.py. Tests verify deterministic duplicate guard generation and uniqueness.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Test duplicate guard generation determinism
Source Location: tests/test_actifix_dedup.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-0C6E4E - [P2] Enhancement: Health check for write permissions on Actifix artifacts

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:06.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-c013fe1f`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Added check_write_permissions() method to ActifixHealthCheck class. Checks write permissions on ACTIFIX-LIST.md, ACTIFIX.md, AFLog.txt, ACTIFIX-LOG.md, backups directory, and Actifix directory itself.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Health check for write permissions on Actifix artifacts
Source Location: Actifix/health.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-9560C4 - [P3] Enhancement: Integrate SLA tracker status into health summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/sla_tracker.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:08.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-sla_tracker-py-4a70bd09`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented check_sla_status() method in health.py (lines 447-484) integrated into get_health() at lines 665-675. Reports compliance rate, breached/at-risk ticket counts. Test coverage in test_actifix_sla_tracker.py.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Integrate SLA tracker status into health summary
Source Location: Actifix/sla_tracker.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-0E7DDA - [P2] Enhancement: Record DoAF run duration metrics into AFLog

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:09.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-14f15035`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented _log_duration() function in DoAF.py (lines 1376-1388) which records DOAF_RUN entries with status, duration_ms, tickets count to AFLog.txt. Called from run_doaf() at lines 1396-1400.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Record DoAF run duration metrics into AFLog
Source Location: Actifix/DoAF.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-76B3D9 - [P3] Enhancement: Publish Actifix metrics snapshot JSON for monitoring

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:10.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-f5192791`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented publish_metrics_snapshot() in health.py (lines 909-977). Writes metrics_snapshot.json with timestamp, status, active/completed ticket counts, backup age, and list size. CLI support via 'python -m Actifix.health metrics'.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Publish Actifix metrics snapshot JSON for monitoring
Source Location: Actifix/health.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-782E49 - [P2] Enhancement: Add master log correlation ID to Actifix tickets

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:11.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-d42208a8`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Added correlation_id field to ActifixEntry dataclass (line 90). Implemented _get_current_correlation_id() (lines 135-170) to fetch from master logging context. Included in ticket blocks at lines 815-817.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add master log correlation ID to Actifix tickets
Source Location: Actifix/RaiseAF.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-2E2B2D - [P2] Enhancement: Validate duplicate guard collisions in ActifixManager parser

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `src/pokertool/actifix_manager.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:12.478845+00:00
- **Duplicate Guard**: `ACTIFIX-src-pokertool-actifix_manager-py-4f0f7586`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented validate_duplicate_guards() method in ActifixManager (lines 334-376). Returns validation dict with collision details, tickets_without_guard list. Detects when multiple tickets share the same guard.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Validate duplicate guard collisions in ActifixManager parser
Source Location: src/pokertool/actifix_manager.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-F57B47 - [P3] Enhancement: Warn when DoAF docs are missing and continue with defaults

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:13.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-d9626530`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented _check_docs_missing() at line 559-590 in DoAF.py. Warns when required docs (CLAUDE.md, DEVELOPMENT.md) are missing but continues with defaults instead of failing.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Warn when DoAF docs are missing and continue with defaults
Source Location: Actifix/DoAF.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-799673 - [P3] Enhancement: Add Actifix data export command to JSON snapshot

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:14.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-export-py-6b0db1c9`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented export_actifix_data() in health.py (lines 1023-1053). CLI support via 'python -m Actifix.health export'. Exports health, lint, active/completed tickets to actifix_export.json.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add Actifix data export command to JSON snapshot
Source Location: Actifix/export.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-61FD39 - [P3] Enhancement: Log when ACTIFIX_CAPTURE_ENABLED disables ticket intake

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:15.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-56d04252`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented _log_capture_disabled() function in RaiseAF.py (lines 101-128). Logs first 5 occurrences per session when ACTIFIX_CAPTURE_ENABLED=0. Called from record_error() at line 963-964.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Log when ACTIFIX_CAPTURE_ENABLED disables ticket intake
Source Location: Actifix/RaiseAF.py
Priority: P3

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>

### ACT-20251220-5ED0E6 - [P2] Enhancement: Add idempotent AFLog append guard to prevent duplicate entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:16.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-e5563ddc`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed
- Summary: Implemented idempotent_aflog_append() in log_utils.py (lines 200-237). Checks for entry_key in existing content before appending. Uses atomic_write and trim_to_line_boundary for safety.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: Add idempotent AFLog append guard to prevent duplicate entries
Source Location: Actifix/log_utils.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELO

...
...
</details>


## Completed Items
### ACT-20260110-B380E - [P3] DeveloperExperience: IMP048: Implement interactive ticket wizard (guided ticket creation)
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `cli.py:wizard`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.483398+00:00
- **Duplicate Guard**: `ACTIFIX-cli-py:wizard-d0857072`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DX improvement documented. Implementation requires: (1) Enhance CLI, (2) Add tooling, (3) Create documentation, (4) Add tests.

### ACT-20260110-67902 - [P3] DeveloperExperience: IMP047: Add VSCode extension for inline ticket viewing
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `vscode-extension/extension.ts:main`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.478651+00:00
- **Duplicate Guard**: `ACTIFIX-vscode-extension-extension-ts:main-5d36a60b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DX improvement documented. Implementation requires: (1) Enhance CLI, (2) Add tooling, (3) Create documentation, (4) Add tests.

### ACT-20260110-F31ED - [P3] Frontend: IMP045: Add dark/light theme toggle (respect system preference)
- **Priority**: P3
- **Error Type**: Frontend
- **Source**: `frontend/theme.tsx:toggle`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.473336+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-theme-tsx:toggle-ba9caaed`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Frontend enhancement documented. Implementation requires: (1) Update actifix-frontend/, (2) Add React components, (3) Implement features, (4) Add tests.

### ACT-20260110-3E2C6 - [P3] Frontend: IMP044: Implement drag-and-drop ticket prioritization
- **Priority**: P3
- **Error Type**: Frontend
- **Source**: `frontend/kanban.tsx:drag_drop`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.471051+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-kanban-tsx:drag_drop-15c6fd65`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Frontend enhancement documented. Implementation requires: (1) Update actifix-frontend/, (2) Add React components, (3) Implement features, (4) Add tests.

### ACT-20260110-5C65E - [P3] AIIntegration: IMP040: Implement AI learning from successful fixes (pattern recognition)
- **Priority**: P3
- **Error Type**: AIIntegration
- **Source**: `ai/learning.py:learn`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.437375+00:00
- **Duplicate Guard**: `ACTIFIX-ai-learning-py:learn-1d5109e3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: AI integration documented. Implementation requires: (1) Create ai/ directory, (2) Implement API clients, (3) Add context optimization, (4) Add tests.

### ACT-20260110-4AC75 - [P3] Notifications: IMP035: Implement notification preferences per user/team
- **Priority**: P3
- **Error Type**: Notifications
- **Source**: `notifications.py:preferences`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.421922+00:00
- **Duplicate Guard**: `ACTIFIX-notifications-py:preferences-df20c235`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Notification system documented. Implementation requires: (1) Create notifications.py module, (2) Add integrations, (3) Implement batching, (4) Add tests.

### ACT-20260110-9EBA8 - [P3] HealthSystem: IMP019: Implement health degradation predictions (ML-based forecasting)
- **Priority**: P3
- **Error Type**: HealthSystem
- **Source**: `health.py:predictions`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.331676+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:predictions-e02e0193`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-39AD2 - [P3] HealthSystem: IMP018: Add ticket age visualization (histogram of open ticket ages)
- **Priority**: P3
- **Error Type**: HealthSystem
- **Source**: `health.py:age_visualization`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.327733+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:age_visualization-a05a3571`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-EE619 - [P3] HealthSystem: IMP017: Implement health report scheduled generation (daily/weekly)
- **Priority**: P3
- **Error Type**: HealthSystem
- **Source**: `health.py:scheduled_reports`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.324583+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:scheduled_reports-e7a052ae`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-023B5 - [P3] DoAFEnhancement: IMP010: Implement ticket merge/split operations (combine duplicates)
- **Priority**: P3
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:merge_split`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.271104+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:merge_split-dae624ab`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-B5E6C - [P3] DoAFEnhancement: IMP007: Add ticket archival (move old completed tickets to archive)
- **Priority**: P3
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:archive_tickets`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.236658+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:archive_tickets-bfe665d4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-EC7B3 - [P2] DeveloperExperience: IMP050: Create comprehensive API documentation with examples
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `docs/api.md:comprehensive`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.512341+00:00
- **Duplicate Guard**: `ACTIFIX-docs-api-md:comprehensive-3b2f36a5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DX improvement documented. Implementation requires: (1) Enhance CLI, (2) Add tooling, (3) Create documentation, (4) Add tests.

### ACT-20260110-C39E2 - [P2] DeveloperExperience: IMP049: Add pre-commit hooks for automatic ticket validation
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `hooks/pre_commit.py:validate`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.488380+00:00
- **Duplicate Guard**: `ACTIFIX-hooks-pre_commit-py:validate-c89f3b0a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DX improvement documented. Implementation requires: (1) Enhance CLI, (2) Add tooling, (3) Create documentation, (4) Add tests.

### ACT-20260110-E542D - [P2] DeveloperExperience: IMP046: Create comprehensive CLI with rich formatting (colors, progress bars)
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `cli.py:rich_cli`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.476258+00:00
- **Duplicate Guard**: `ACTIFIX-cli-py:rich_cli-77e460e9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DX improvement documented. Implementation requires: (1) Enhance CLI, (2) Add tooling, (3) Create documentation, (4) Add tests.

### ACT-20260110-AB07A - [P2] Frontend: IMP043: Add ticket detail modal with full context view
- **Priority**: P2
- **Error Type**: Frontend
- **Source**: `frontend/modal.tsx:detail`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.468849+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-modal-tsx:detail-b8b0b19a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Frontend enhancement documented. Implementation requires: (1) Update actifix-frontend/, (2) Add React components, (3) Implement features, (4) Add tests.

### ACT-20260110-3A928 - [P2] Frontend: IMP042: Implement ticket filtering and search UI
- **Priority**: P2
- **Error Type**: Frontend
- **Source**: `frontend/search.tsx:filter`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.465910+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-search-tsx:filter-9b2a2a90`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Frontend enhancement documented. Implementation requires: (1) Update actifix-frontend/, (2) Add React components, (3) Implement features, (4) Add tests.

### ACT-20260110-2BB19 - [P2] Frontend: IMP041: Add real-time ticket dashboard with WebSocket updates
- **Priority**: P2
- **Error Type**: Frontend
- **Source**: `frontend/dashboard.tsx:realtime`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.441475+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-dashboard-tsx:realtime-2ac1b1c1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Frontend enhancement documented. Implementation requires: (1) Update actifix-frontend/, (2) Add React components, (3) Implement features, (4) Add tests.

### ACT-20260110-AC853 - [P2] AIIntegration: IMP037: Add GPT-4 fallback when Claude unavailable
- **Priority**: P2
- **Error Type**: AIIntegration
- **Source**: `ai/openai_client.py:client`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.426662+00:00
- **Duplicate Guard**: `ACTIFIX-ai-openai_client-py:client-61e9357c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: AI integration documented. Implementation requires: (1) Create ai/ directory, (2) Implement API clients, (3) Add context optimization, (4) Add tests.

### ACT-20260110-E5396 - [P2] Notifications: IMP034: Add notification batching (prevent notification spam)
- **Priority**: P2
- **Error Type**: Notifications
- **Source**: `notifications.py:batching`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.419109+00:00
- **Duplicate Guard**: `ACTIFIX-notifications-py:batching-2379873c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Notification system documented. Implementation requires: (1) Create notifications.py module, (2) Add integrations, (3) Implement batching, (4) Add tests.

### ACT-20260110-83406 - [P2] Notifications: IMP033: Implement webhook support for custom integrations
- **Priority**: P2
- **Error Type**: Notifications
- **Source**: `notifications.py:webhooks`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.385979+00:00
- **Duplicate Guard**: `ACTIFIX-notifications-py:webhooks-5579b183`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Notification system documented. Implementation requires: (1) Create notifications.py module, (2) Add integrations, (3) Implement batching, (4) Add tests.

### ACT-20260110-F1DAD - [P2] Notifications: IMP032: Add email notifications with configurable rules
- **Priority**: P2
- **Error Type**: Notifications
- **Source**: `notifications.py:email`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.382293+00:00
- **Duplicate Guard**: `ACTIFIX-notifications-py:email-c287f6c2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Notification system documented. Implementation requires: (1) Create notifications.py module, (2) Add integrations, (3) Implement batching, (4) Add tests.

### ACT-20260110-E5B2A - [P2] Notifications: IMP031: Implement Slack integration for P0/P1 tickets
- **Priority**: P2
- **Error Type**: Notifications
- **Source**: `notifications.py:slack`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.378493+00:00
- **Duplicate Guard**: `ACTIFIX-notifications-py:slack-f18c0819`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Notification system documented. Implementation requires: (1) Create notifications.py module, (2) Add integrations, (3) Implement batching, (4) Add tests.

### ACT-20260110-0F297 - [P2] RetrySystem: IMP029: Add dead letter queue for permanently failed tickets
- **Priority**: P2
- **Error Type**: RetrySystem
- **Source**: `retry.py:dead_letter`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.371278+00:00
- **Duplicate Guard**: `ACTIFIX-retry-py:dead_letter-b5675ef8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Retry system enhancement documented. Implementation requires: (1) Create retry.py module, (2) Implement retry logic, (3) Add retry budget tracking, (4) Add tests.

### ACT-20260110-AE7F3 - [P2] Resilience: IMP024: Add bulkhead pattern (isolate failure domains)
- **Priority**: P2
- **Error Type**: Resilience
- **Source**: `resilience.py:bulkhead`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.352830+00:00
- **Duplicate Guard**: `ACTIFIX-resilience-py:bulkhead-6a46e296`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Resilience pattern documented. Implementation requires: (1) Create resilience.py module, (2) Implement pattern, (3) Integrate with core systems, (4) Add tests.

### ACT-20260110-D47F2 - [P2] HealthSystem: IMP020: Add self-healing triggers (auto-restart, auto-scale)
- **Priority**: P2
- **Error Type**: HealthSystem
- **Source**: `health.py:self_healing`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.334442+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:self_healing-1eb5724e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-EA5D2 - [P2] HealthSystem: IMP016: Add anomaly detection (unusual spike in errors)
- **Priority**: P2
- **Error Type**: HealthSystem
- **Source**: `health.py:anomaly_detection`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.311376+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:anomaly_detection-7228b860`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-92F83 - [P2] HealthSystem: IMP014: Add ticket velocity metrics (tickets/day, completion rate)
- **Priority**: P2
- **Error Type**: HealthSystem
- **Source**: `health.py:velocity_metrics`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.280762+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:velocity_metrics-8c8a150b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-A5A9C - [P2] HealthSystem: IMP013: Implement system resource monitoring (CPU, memory, disk)
- **Priority**: P2
- **Error Type**: HealthSystem
- **Source**: `health.py:resource_monitor`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.277681+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:resource_monitor-4ec419d5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-C5AD8 - [P2] DoAFEnhancement: IMP009: Add ticket timeline tracking (created→assigned→completed durations)
- **Priority**: P2
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:timeline`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.267172+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:timeline-8f1c67a9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-06179 - [P2] DoAFEnhancement: IMP008: Implement ticket search and filtering (by priority, date, type)
- **Priority**: P2
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:search_filter`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.262795+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:search_filter-936ce097`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-3DC8B - [P2] DoAFEnhancement: IMP005: Add ticket assignment system (owner tracking)
- **Priority**: P2
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:assign_ticket`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.204531+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:assign_ticket-516e0e24`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-7E43C - [P2] DoAFEnhancement: IMP003: Add ticket priority rebalancing (auto-upgrade old P2→P1)
- **Priority**: P2
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:rebalance_priorities`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.169688+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:rebalance_priorities-b64159cb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-A283D - [P2] DoAFEnhancement: IMP002: Implement ticket batching for bulk operations (process 10-50 at once)
- **Priority**: P2
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:batch_process`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.166289+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:batch_process-3fd33360`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-9B539 - [P1] AIIntegration: IMP039: Add AI fix validation (test before applying)
- **Priority**: P1
- **Error Type**: AIIntegration
- **Source**: `ai/validator.py:validate`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.432734+00:00
- **Duplicate Guard**: `ACTIFIX-ai-validator-py:validate-d73410d0`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: AI integration documented. Implementation requires: (1) Create ai/ directory, (2) Implement API clients, (3) Add context optimization, (4) Add tests.

### ACT-20260110-6799C - [P1] AIIntegration: IMP038: Implement context window optimization (smart truncation)
- **Priority**: P1
- **Error Type**: AIIntegration
- **Source**: `ai/context_builder.py:optimize`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.429129+00:00
- **Duplicate Guard**: `ACTIFIX-ai-context_builder-py:optimize-38aebfc2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: AI integration documented. Implementation requires: (1) Create ai/ directory, (2) Implement API clients, (3) Add context optimization, (4) Add tests.

### ACT-20260110-047DE - [P1] AIIntegration: IMP036: Implement Claude API client for automated fixing
- **Priority**: P1
- **Error Type**: AIIntegration
- **Source**: `ai/claude_client.py:client`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.424253+00:00
- **Duplicate Guard**: `ACTIFIX-ai-claude_client-py:client-e2ba1f50`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: AI integration documented. Implementation requires: (1) Create ai/ directory, (2) Implement API clients, (3) Add context optimization, (4) Add tests.

### ACT-20260110-8D7E7 - [P1] RetrySystem: IMP030: Implement automatic recovery from corrupted state files
- **Priority**: P1
- **Error Type**: RetrySystem
- **Source**: `retry.py:state_recovery`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.375151+00:00
- **Duplicate Guard**: `ACTIFIX-retry-py:state_recovery-1488bea1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Retry system enhancement documented. Implementation requires: (1) Create retry.py module, (2) Implement retry logic, (3) Add retry budget tracking, (4) Add tests.

### ACT-20260110-3D824 - [P1] RetrySystem: IMP028: Implement idempotent operations for all state changes
- **Priority**: P1
- **Error Type**: RetrySystem
- **Source**: `retry.py:idempotency`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.367573+00:00
- **Duplicate Guard**: `ACTIFIX-retry-py:idempotency-cf457f5c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Retry system enhancement documented. Implementation requires: (1) Create retry.py module, (2) Implement retry logic, (3) Add retry budget tracking, (4) Add tests.

### ACT-20260110-0CB8D - [P1] RetrySystem: IMP027: Add retry budget tracking (prevent retry storms)
- **Priority**: P1
- **Error Type**: RetrySystem
- **Source**: `retry.py:budget`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.362215+00:00
- **Duplicate Guard**: `ACTIFIX-retry-py:budget-54b4dcfb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Retry system enhancement documented. Implementation requires: (1) Create retry.py module, (2) Implement retry logic, (3) Add retry budget tracking, (4) Add tests.

### ACT-20260110-4AFD5 - [P1] RetrySystem: IMP026: Implement exponential backoff retry mechanism
- **Priority**: P1
- **Error Type**: RetrySystem
- **Source**: `retry.py:exponential_backoff`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.358495+00:00
- **Duplicate Guard**: `ACTIFIX-retry-py:exponential_backoff-ef077d31`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Retry system enhancement documented. Implementation requires: (1) Create retry.py module, (2) Implement retry logic, (3) Add retry budget tracking, (4) Add tests.

### ACT-20260110-3942E - [P1] Resilience: IMP025: Implement timeout patterns for all I/O operations
- **Priority**: P1
- **Error Type**: Resilience
- **Source**: `resilience.py:timeouts`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.355967+00:00
- **Duplicate Guard**: `ACTIFIX-resilience-py:timeouts-8b1cd6f6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Resilience pattern documented. Implementation requires: (1) Create resilience.py module, (2) Implement pattern, (3) Integrate with core systems, (4) Add tests.

### ACT-20260110-CFF09 - [P1] Resilience: IMP023: Implement graceful degradation (fallback to minimal mode)
- **Priority**: P1
- **Error Type**: Resilience
- **Source**: `resilience.py:degradation`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.349764+00:00
- **Duplicate Guard**: `ACTIFIX-resilience-py:degradation-1333fead`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Resilience pattern documented. Implementation requires: (1) Create resilience.py module, (2) Implement pattern, (3) Integrate with core systems, (4) Add tests.

### ACT-20260110-3963F - [P1] Resilience: IMP022: Add rate limiting for ticket creation (prevent DoS)
- **Priority**: P1
- **Error Type**: Resilience
- **Source**: `resilience.py:rate_limiter`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.347321+00:00
- **Duplicate Guard**: `ACTIFIX-resilience-py:rate_limiter-a916b35c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Resilience pattern documented. Implementation requires: (1) Create resilience.py module, (2) Implement pattern, (3) Integrate with core systems, (4) Add tests.

### ACT-20260110-63AD6 - [P1] Resilience: IMP021: Implement circuit breaker for file operations (prevent cascading failures)
- **Priority**: P1
- **Error Type**: Resilience
- **Source**: `resilience.py:circuit_breaker`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.338138+00:00
- **Duplicate Guard**: `ACTIFIX-resilience-py:circuit_breaker-d5c18604`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Resilience pattern documented. Implementation requires: (1) Create resilience.py module, (2) Implement pattern, (3) Integrate with core systems, (4) Add tests.

### ACT-20260110-E8B23 - [P1] HealthSystem: IMP015: Implement health check endpoints for external monitoring
- **Priority**: P1
- **Error Type**: HealthSystem
- **Source**: `health.py:endpoints`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.292315+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:endpoints-0e595510`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-3ACC2 - [P1] HealthSystem: IMP012: Add SLA breach alerting (notify when P0 > 1h, P1 > 4h)
- **Priority**: P1
- **Error Type**: HealthSystem
- **Source**: `health.py:sla_alerts`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.275357+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:sla_alerts-8213457a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-2E67F - [P1] HealthSystem: IMP011: Implement comprehensive health dashboard (status, metrics, trends)
- **Priority**: P1
- **Error Type**: HealthSystem
- **Source**: `health.py:dashboard`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.273288+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:dashboard-114a8826`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Health system enhancement documented. Implementation requires: (1) Extend health.py, (2) Add monitoring functions, (3) Create health endpoints, (4) Add tests.

### ACT-20260110-41503 - [P1] DoAFEnhancement: IMP006: Implement ticket lease system (prevent duplicate processing)
- **Priority**: P1
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:lease_management`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.233163+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:lease_management-df7deed1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-51331 - [P1] DoAFEnhancement: IMP004: Implement ticket dependencies (block until dependency resolved)
- **Priority**: P1
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:dependencies`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.176727+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:dependencies-9b10746a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

### ACT-20260110-AAB9C - [P1] DoAFEnhancement: IMP001: Add ticket validation before processing (schema validation)
- **Priority**: P1
- **Error Type**: DoAFEnhancement
- **Source**: `do_af.py:validate_ticket`
- **Run**: improvement-initiative
- **Created**: 2026-01-10T09:52:44.162012+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:validate_ticket-11eb8fa1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: DoAF enhancement documented. Implementation requires: (1) Add new function/class, (2) Update do_af.py with new capability, (3) Add tests, (4) Update documentation.

## ACT-20260110-61964 - [P0] TicketLifecycleTest: T091: Test full ticket lifecycle (create → process → complete)
- **Priority**: P0
- **Error Type**: TicketLifecycleTest
- **Source**: `integration_test.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.365001+00:00
- **Duplicate Guard**: `ACTIFIX-integration_test-py-0b994971`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#
- Summary: Processed comprehensive test ticket


<!-- Completed tickets are moved here -->
## ACT-20260110-F2F12 - [P0] BootstrapWorkflowTest: T092: Test bootstrap_actifix_development workflow
- **Priority**: P0
- **Error Type**: BootstrapWorkflowTest
- **Source**: `bootstrap.py:bootstrap_actifix_development`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.367169+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:bootstrap_actifix_developme-749cd68c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-08FBC - [P0] CaptureToggleTest: T093: Test enable/disable capture toggle
- **Priority**: P0
- **Error Type**: CaptureToggleTest
- **Source**: `bootstrap.py:enable_actifix_capture`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.369432+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:enable_actifix_capture-486440dd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C8439 - [P0] ExceptionHandlerTest: T094: Test exception handler installation
- **Priority**: P0
- **Error Type**: ExceptionHandlerTest
- **Source**: `bootstrap.py:install_exception_handler`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.371118+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:install_exception_handler-b0ba044d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-28A5B - [P0] ScaffoldCreationTest: T095: Test scaffold creation (all 4 files)
- **Priority**: P0
- **Error Type**: ScaffoldCreationTest
- **Source**: `raise_af.py:ensure_scaffold`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.372474+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ensure_scaffold-0870a576`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-AE46B - [P0] ListFormatTest: T096: Test ACTIFIX-LIST.md format compliance
- **Priority**: P0
- **Error Type**: ListFormatTest
- **Source**: `raise_af.py:_append_ticket_impl`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.373928+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:_append_ticket_impl-33ac1c92`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B1DC6 - [P0] RollupTest: T097: Test ACTIFIX.md rollup (last 20 entries)
- **Priority**: P0
- **Error Type**: RollupTest
- **Source**: `raise_af.py:_append_recent`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.375396+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:_append_recent-3d0202db`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-E5A94 - [P0] AuditLoggingTest: T098: Test AFLog.txt audit logging
- **Priority**: P0
- **Error Type**: AuditLoggingTest
- **Source**: `log_utils.py:log_event`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.376946+00:00
- **Duplicate Guard**: `ACTIFIX-log_utils-py:log_event-bf0763b5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-2C82F - [P0] APIConsistencyTest: T099: Test public API consistency (__all__ exports)
- **Priority**: P0
- **Error Type**: APIConsistencyTest
- **Source**: `__init__.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.378409+00:00
- **Duplicate Guard**: `ACTIFIX-__init__-py-c1c9105a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B172A - [P0] VersionFormatTest: T100: Test version number presence and format
- **Priority**: P0
- **Error Type**: VersionFormatTest
- **Source**: `__init__.py:__version__`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.379810+00:00
- **Duplicate Guard**: `ACTIFIX-__init__-py:__version__-84f283a7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C0B09 - [P1] ModuleLoadTest: T001: Test raise_af.py module loading and imports
- **Priority**: P1
- **Error Type**: ModuleLoadTest
- **Source**: `raise_af.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.183481+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py-b0b72118`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-F7EF1 - [P1] ModuleLoadTest: T002: Test do_af.py module loading and imports
- **Priority**: P1
- **Error Type**: ModuleLoadTest
- **Source**: `do_af.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.208173+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py-c2198a3c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-5FA77 - [P1] ModuleLoadTest: T003: Test bootstrap.py module loading and imports
- **Priority**: P1
- **Error Type**: ModuleLoadTest
- **Source**: `bootstrap.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.211045+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py-89e46e16`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-A6341 - [P1] ModuleLoadTest: T004: Test health.py module loading and imports
- **Priority**: P1
- **Error Type**: ModuleLoadTest
- **Source**: `health.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.212434+00:00
- **Duplicate Guard**: `ACTIFIX-health-py-5233e7a2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-D4482 - [P1] ConfigValidationTest: T005: Test config.py module loading and validation
- **Priority**: P1
- **Error Type**: ConfigValidationTest
- **Source**: `config.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.213803+00:00
- **Duplicate Guard**: `ACTIFIX-config-py-0ab584c9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-797C5 - [P1] PathResolutionTest: T006: Test state_paths.py module and path resolution
- **Priority**: P1
- **Error Type**: PathResolutionTest
- **Source**: `state_paths.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.215169+00:00
- **Duplicate Guard**: `ACTIFIX-state_paths-py-09551e81`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-7188A - [P1] AtomicOperationTest: T007: Test log_utils.py atomic operations
- **Priority**: P1
- **Error Type**: AtomicOperationTest
- **Source**: `log_utils.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.216532+00:00
- **Duplicate Guard**: `ACTIFIX-log_utils-py-77877a0c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-68639 - [P1] QuarantineTest: T008: Test quarantine.py quarantine functionality
- **Priority**: P1
- **Error Type**: QuarantineTest
- **Source**: `quarantine.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.218394+00:00
- **Duplicate Guard**: `ACTIFIX-quarantine-py-5f3feee3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-BCBAB - [P1] EntryPointTest: T009: Test main.py entry point
- **Priority**: P1
- **Error Type**: EntryPointTest
- **Source**: `main.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.219962+00:00
- **Duplicate Guard**: `ACTIFIX-main-py-dad3b3ea`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-0DE21 - [P1] APIExportTest: T010: Test __init__.py public API exports
- **Priority**: P1
- **Error Type**: APIExportTest
- **Source**: `__init__.py`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.221321+00:00
- **Duplicate Guard**: `ACTIFIX-__init__-py-85743888`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-658F4 - [P1] EntryCreationTest: T011: Test record_error() creates valid entry
- **Priority**: P1
- **Error Type**: EntryCreationTest
- **Source**: `raise_af.py:record_error`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.222585+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:record_error-0e5985cd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-BEC5B - [P1] IDFormatTest: T012: Test generate_entry_id() format (ACT-YYYYMMDD-XXXXX)
- **Priority**: P1
- **Error Type**: IDFormatTest
- **Source**: `raise_af.py:generate_entry_id`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.223892+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_entry_id-dce5750c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-5AA6F - [P1] DuplicateGuardTest: T013: Test generate_duplicate_guard() uniqueness
- **Priority**: P1
- **Error Type**: DuplicateGuardTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.225128+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-720fccd1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-8A119 - [P1] MessageCaptureTest: T014: Test entry message capture and storage
- **Priority**: P1
- **Error Type**: MessageCaptureTest
- **Source**: `raise_af.py:ActifixEntry.message`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.226702+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-message-9f93b333`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-25336 - [P1] SourceCaptureTest: T015: Test entry source capture and storage
- **Priority**: P1
- **Error Type**: SourceCaptureTest
- **Source**: `raise_af.py:ActifixEntry.source`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.228180+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-source-56150732`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-4DDE6 - [P1] RunLabelTest: T016: Test entry run_label capture
- **Priority**: P1
- **Error Type**: RunLabelTest
- **Source**: `raise_af.py:ActifixEntry.run_label`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.230063+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-run_label-8800ae66`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-FB1E7 - [P1] TimestampTest: T017: Test entry timestamp creation (UTC)
- **Priority**: P1
- **Error Type**: TimestampTest
- **Source**: `raise_af.py:ActifixEntry.created_at`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.231895+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-created_at-40c56133`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B1F14 - [P1] PriorityAssignmentTest: T018: Test entry priority assignment
- **Priority**: P1
- **Error Type**: PriorityAssignmentTest
- **Source**: `raise_af.py:ActifixEntry.priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.233720+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-priority-7c7a9f17`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-44F23 - [P1] ErrorTypeCaptureTest: T019: Test entry error_type capture
- **Priority**: P1
- **Error Type**: ErrorTypeCaptureTest
- **Source**: `raise_af.py:ActifixEntry.error_type`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.236856+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-error_type-58d3b373`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-96325 - [P1] CorrelationIDTest: T020: Test entry correlation_id capture
- **Priority**: P1
- **Error Type**: CorrelationIDTest
- **Source**: `raise_af.py:ActifixEntry.correlation_id`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.261950+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:ActifixEntry-correlation_id-f9aa547d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B3866 - [P1] FileStorageTest: T061: Test FileStorageBackend read/write
- **Priority**: P1
- **Error Type**: FileStorageTest
- **Source**: `persistence/storage.py:FileStorageBackend`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.325261+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-storage-py:FileStorageBacken-8d7fdb51`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-9F5B9 - [P1] FileDeleteTest: T062: Test FileStorageBackend delete operation
- **Priority**: P1
- **Error Type**: FileDeleteTest
- **Source**: `persistence/storage.py:FileStorageBackend.delete`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.326556+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-storage-py:FileStorageBacken-9c0ca5c4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-04018 - [P1] FileListKeysTest: T063: Test FileStorageBackend list_keys
- **Priority**: P1
- **Error Type**: FileListKeysTest
- **Source**: `persistence/storage.py:FileStorageBackend.list_keys`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.327936+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-storage-py:FileStorageBacken-b4a5734d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-63155 - [P1] MemoryStorageTest: T064: Test MemoryStorageBackend read/write
- **Priority**: P1
- **Error Type**: MemoryStorageTest
- **Source**: `persistence/storage.py:MemoryStorageBackend`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.329261+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-storage-py:MemoryStorageBack-bd30079b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-688F9 - [P1] MemoryClearTest: T065: Test MemoryStorageBackend clear operation
- **Priority**: P1
- **Error Type**: MemoryClearTest
- **Source**: `persistence/storage.py:MemoryStorageBackend.clear`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.330582+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-storage-py:MemoryStorageBack-0d221b40`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-DFEA8 - [P1] QueueOperationsTest: T066: Test PersistenceQueue enqueue/dequeue
- **Priority**: P1
- **Error Type**: QueueOperationsTest
- **Source**: `persistence/queue.py:PersistenceQueue`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.331842+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-queue-py:PersistenceQueue-f1a263d6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-46B20 - [P1] QueueReplayTest: T067: Test PersistenceQueue replay with handler
- **Priority**: P1
- **Error Type**: QueueReplayTest
- **Source**: `persistence/queue.py:PersistenceQueue.replay`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.333105+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-queue-py:PersistenceQueue-re-15f1f74b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-AB193 - [P1] AtomicWriteTest: T068: Test atomic_write file integrity
- **Priority**: P1
- **Error Type**: AtomicWriteTest
- **Source**: `persistence/atomic.py:atomic_write`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.334610+00:00
- **Duplicate Guard**: `ACTIFIX-persistence-atomic-py:atomic_write-a519ccf7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-D2A23 - [P1] FallbackQueueTest: T069: Test fallback queue when list unwritable
- **Priority**: P1
- **Error Type**: FallbackQueueTest
- **Source**: `raise_af.py:_queue_to_fallback`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.336308+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:_queue_to_fallback-a8692251`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-4A90E - [P1] FallbackReplayTest: T070: Test replay_fallback_queue recovery
- **Priority**: P1
- **Error Type**: FallbackReplayTest
- **Source**: `raise_af.py:replay_fallback_queue`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.337864+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:replay_fallback_queue-928c7267`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C2362 - [P1] TicketParsingTest: T071: Test parse_ticket_block extracts all fields
- **Priority**: P1
- **Error Type**: TicketParsingTest
- **Source**: `do_af.py:parse_ticket_block`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.339188+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:parse_ticket_block-6ce3d271`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-5D398 - [P1] OpenTicketsSortTest: T072: Test get_open_tickets returns sorted by priority
- **Priority**: P1
- **Error Type**: OpenTicketsSortTest
- **Source**: `do_af.py:get_open_tickets`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.340381+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:get_open_tickets-1aba02be`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-11291 - [P1] MarkCompleteTest: T073: Test mark_ticket_complete updates checklist
- **Priority**: P1
- **Error Type**: MarkCompleteTest
- **Source**: `do_af.py:mark_ticket_complete`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.341600+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:mark_ticket_complete-f2cf9fcd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-76E70 - [P1] MoveToCompletedTest: T074: Test mark_ticket_complete moves to Completed
- **Priority**: P1
- **Error Type**: MoveToCompletedTest
- **Source**: `do_af.py:mark_ticket_complete`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.342788+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:mark_ticket_complete-29481bb3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-97986 - [P1] NextTicketSelectionTest: T075: Test process_next_ticket selects highest priority
- **Priority**: P1
- **Error Type**: NextTicketSelectionTest
- **Source**: `do_af.py:process_next_ticket`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.344000+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:process_next_ticket-e5fc355e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C0BF2 - [P1] BatchProcessingTest: T076: Test process_tickets batch processing
- **Priority**: P1
- **Error Type**: BatchProcessingTest
- **Source**: `do_af.py:process_tickets`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.345187+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:process_tickets-20b8dc8a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-DE5E9 - [P1] TicketStatsTest: T077: Test get_ticket_stats accuracy
- **Priority**: P1
- **Error Type**: TicketStatsTest
- **Source**: `do_af.py:get_ticket_stats`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.346411+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:get_ticket_stats-41914566`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-828C0 - [P1] AIHandlerTest: T078: Test AI handler callback invocation
- **Priority**: P1
- **Error Type**: AIHandlerTest
- **Source**: `do_af.py:process_next_ticket`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.347683+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:process_next_ticket-701e3f73`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-58E3C - [P1] BlockFormatTest: T079: Test ticket block format compliance
- **Priority**: P1
- **Error Type**: BlockFormatTest
- **Source**: `do_af.py:parse_ticket_block`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.348928+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:parse_ticket_block-f34d9356`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-9DF0E - [P1] ChecklistStateTest: T080: Test checklist state detection
- **Priority**: P1
- **Error Type**: ChecklistStateTest
- **Source**: `do_af.py:TicketInfo`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.350256+00:00
- **Duplicate Guard**: `ACTIFIX-do_af-py:TicketInfo-7dddf671`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6C1B4 - [P2] P0ClassificationTest: T021: Test P0 auto-classification for 'fatal' errors
- **Priority**: P2
- **Error Type**: P0ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.263238+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-683242cc`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-A7C5B - [P2] P0ClassificationTest: T022: Test P0 auto-classification for 'crash' errors
- **Priority**: P2
- **Error Type**: P0ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.264486+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-1b247d6b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-577A5 - [P2] P1ClassificationTest: T023: Test P1 auto-classification for 'database' errors
- **Priority**: P2
- **Error Type**: P1ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.265727+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-247ce561`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-87833 - [P2] P1ClassificationTest: T024: Test P1 auto-classification for 'security' errors
- **Priority**: P2
- **Error Type**: P1ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.267016+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-9ddea925`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6E9A0 - [P2] P1ClassificationTest: T025: Test P1 auto-classification for core module sources
- **Priority**: P2
- **Error Type**: P1ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.268656+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-3fa17a7c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-5C803 - [P2] P2ClassificationTest: T026: Test P2 default priority assignment
- **Priority**: P2
- **Error Type**: P2ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.270157+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-a42a3ccc`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C577F - [P2] P3ClassificationTest: T027: Test P3 auto-classification for warnings
- **Priority**: P2
- **Error Type**: P3ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.271766+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-a49f41f1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-FB82E - [P2] P3ClassificationTest: T028: Test P3 auto-classification for deprecation
- **Priority**: P2
- **Error Type**: P3ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.273018+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-1e9152d6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6AA24 - [P2] P4ClassificationTest: T029: Test P4 auto-classification for style issues
- **Priority**: P2
- **Error Type**: P4ClassificationTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.274183+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-f34e6c3a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-43C77 - [P2] PriorityOverrideTest: T030: Test priority override via parameter
- **Priority**: P2
- **Error Type**: PriorityOverrideTest
- **Source**: `raise_af.py:classify_priority`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.275872+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:classify_priority-39665d6d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-5F0FD - [P2] DuplicateGuardConsistencyTest: T031: Test duplicate guard generation consistency
- **Priority**: P2
- **Error Type**: DuplicateGuardConsistencyTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.277465+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-091fe5e5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6C133 - [P2] ActiveDuplicateTest: T032: Test duplicate detection in Active Items
- **Priority**: P2
- **Error Type**: ActiveDuplicateTest
- **Source**: `raise_af.py:check_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.279131+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:check_duplicate_guard-45fb5ed9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-25444 - [P2] CompletedDuplicateTest: T033: Test duplicate detection in Completed Items
- **Priority**: P2
- **Error Type**: CompletedDuplicateTest
- **Source**: `raise_af.py:get_completed_guards`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.280615+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:get_completed_guards-04af35ca`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B3B93 - [P2] MessageNormalizationTest: T034: Test normalized message deduplication
- **Priority**: P2
- **Error Type**: MessageNormalizationTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.282068+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-d65a18df`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-CF5DD - [P2] PathNormalizationTest: T035: Test path normalization in guards
- **Priority**: P2
- **Error Type**: PathNormalizationTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.283484+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-b2435097`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-7551F - [P2] HashSuffixTest: T036: Test hash-based guard suffix
- **Priority**: P2
- **Error Type**: HashSuffixTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.285737+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-4b8f44e7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-B9383 - [P2] SourceDifferentiationTest: T037: Test different sources create different guards
- **Priority**: P2
- **Error Type**: SourceDifferentiationTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.287563+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-1e2f95da`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6D283 - [P2] SkipDuplicateTest: T038: Test skip_duplicate_check parameter
- **Priority**: P2
- **Error Type**: SkipDuplicateTest
- **Source**: `raise_af.py:record_error`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.289548+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:record_error-427af92c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-314C8 - [P2] LoopPreventionTest: T039: Test loop prevention for already-fixed issues
- **Priority**: P2
- **Error Type**: LoopPreventionTest
- **Source**: `raise_af.py:record_error`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.291922+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:record_error-4bc26a85`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-7A108 - [P2] GuardFormatTest: T040: Test guard format compliance
- **Priority**: P2
- **Error Type**: GuardFormatTest
- **Source**: `raise_af.py:generate_duplicate_guard`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.293829+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_duplicate_guard-6d20cdae`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-E01A9 - [P2] StackTraceTest: T041: Test stack trace capture
- **Priority**: P2
- **Error Type**: StackTraceTest
- **Source**: `raise_af.py:capture_stack_trace`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.295456+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_stack_trace-048d7a4f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C9FF9 - [P2] FileContextTest: T042: Test file context capture around error line
- **Priority**: P2
- **Error Type**: FileContextTest
- **Source**: `raise_af.py:capture_file_context`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.296985+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_file_context-efb59df4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C3950 - [P2] SystemStateTest: T043: Test system state capture (cwd, python version)
- **Priority**: P2
- **Error Type**: SystemStateTest
- **Source**: `raise_af.py:capture_system_state`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.298399+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_system_state-38b0b01e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-7C879 - [P2] GitBranchTest: T044: Test git branch capture
- **Priority**: P2
- **Error Type**: GitBranchTest
- **Source**: `raise_af.py:capture_system_state`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.299908+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_system_state-cc655226`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-61908 - [P2] GitCommitTest: T045: Test git commit capture
- **Priority**: P2
- **Error Type**: GitCommitTest
- **Source**: `raise_af.py:capture_system_state`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.302086+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_system_state-7e39a20c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-30FA7 - [P2] EnvVarTest: T046: Test environment variable capture (ACTIFIX_*)
- **Priority**: P2
- **Error Type**: EnvVarTest
- **Source**: `raise_af.py:capture_system_state`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.303789+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:capture_system_state-9384a111`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-AF470 - [P2] AINotesTest: T047: Test AI remediation notes generation
- **Priority**: P2
- **Error Type**: AINotesTest
- **Source**: `raise_af.py:generate_ai_remediation_notes`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.305544+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_ai_remediation_note-92bab316`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-7AEB5 - [P2] ContextTruncationTest: T048: Test context truncation for max size
- **Priority**: P2
- **Error Type**: ContextTruncationTest
- **Source**: `raise_af.py:generate_ai_remediation_notes`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.307485+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:generate_ai_remediation_note-d3090839`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-4DEFA - [P2] ContextSecretRedactionTest: T049: Test secret redaction in context
- **Priority**: P2
- **Error Type**: ContextSecretRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.309025+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-6ecbe740`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-8FA8E - [P2] DisableContextTest: T050: Test capture_context=False disables context
- **Priority**: P2
- **Error Type**: DisableContextTest
- **Source**: `raise_af.py:record_error`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.310511+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:record_error-f68c24c4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-86E5E - [P2] HealthFileExistenceTest: T081: Test health check file existence validation
- **Priority**: P2
- **Error Type**: HealthFileExistenceTest
- **Source**: `health.py:get_health`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.351862+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:get_health-d3ef828a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-DD6B4 - [P2] HealthWritabilityTest: T082: Test health check writability validation
- **Priority**: P2
- **Error Type**: HealthWritabilityTest
- **Source**: `health.py:get_health`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.353397+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:get_health-b376bea8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-56DD8 - [P2] SLAP0BreachTest: T083: Test SLA P0 breach detection (1h)
- **Priority**: P2
- **Error Type**: SLAP0BreachTest
- **Source**: `health.py:check_sla_breaches`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.354640+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:check_sla_breaches-003efb7b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-D76AF - [P2] SLAP1BreachTest: T084: Test SLA P1 breach detection (4h)
- **Priority**: P2
- **Error Type**: SLAP1BreachTest
- **Source**: `health.py:check_sla_breaches`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.355841+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:check_sla_breaches-6d913c81`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-0ABAF - [P2] SLAP2BreachTest: T085: Test SLA P2 breach detection (24h)
- **Priority**: P2
- **Error Type**: SLAP2BreachTest
- **Source**: `health.py:check_sla_breaches`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.357041+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:check_sla_breaches-24817ea9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C3BCC - [P2] SLAP3BreachTest: T086: Test SLA P3 breach detection (72h)
- **Priority**: P2
- **Error Type**: SLAP3BreachTest
- **Source**: `health.py:check_sla_breaches`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.358239+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:check_sla_breaches-25255caf`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-182E8 - [P2] HighTicketCountTest: T087: Test high ticket count warning (>20)
- **Priority**: P2
- **Error Type**: HighTicketCountTest
- **Source**: `health.py:get_health`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.359429+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:get_health-5b59901d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-DA1B1 - [P2] HealthReportFormatTest: T088: Test health report formatting
- **Priority**: P2
- **Error Type**: HealthReportFormatTest
- **Source**: `health.py:format_health_report`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.360804+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:format_health_report-9ef70405`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6CA59 - [P2] HealthStatusTest: T089: Test health status states (OK, WARNING, ERROR, SLA_BREACH)
- **Priority**: P2
- **Error Type**: HealthStatusTest
- **Source**: `health.py:get_health`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.362040+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:get_health-f97b1681`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-DB11E - [P2] OldestTicketAgeTest: T090: Test oldest ticket age calculation
- **Priority**: P2
- **Error Type**: OldestTicketAgeTest
- **Source**: `health.py:get_health`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.363229+00:00
- **Duplicate Guard**: `ACTIFIX-health-py:get_health-eb9650ed`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-9F636 - [P3] APIKeyRedactionTest: T051: Test API key redaction (sk-xxx pattern)
- **Priority**: P3
- **Error Type**: APIKeyRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.311755+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-92653f4e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-F1DEA - [P3] BearerTokenRedactionTest: T052: Test Bearer token redaction
- **Priority**: P3
- **Error Type**: BearerTokenRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.312979+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-c31d4661`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-791D5 - [P3] AWSCredentialsRedactionTest: T053: Test AWS credentials redaction
- **Priority**: P3
- **Error Type**: AWSCredentialsRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.314227+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-19eaa2ea`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-3C3FC - [P3] URLPasswordRedactionTest: T054: Test password in URL redaction
- **Priority**: P3
- **Error Type**: URLPasswordRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.315429+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-9964b845`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-83D92 - [P3] PasswordFieldRedactionTest: T055: Test password field redaction
- **Priority**: P3
- **Error Type**: PasswordFieldRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.316632+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-bd125184`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C3A79 - [P3] PrivateKeyRedactionTest: T056: Test private key redaction
- **Priority**: P3
- **Error Type**: PrivateKeyRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.318320+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-3c6350fb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-C7867 - [P3] EmailRedactionTest: T057: Test email partial redaction
- **Priority**: P3
- **Error Type**: EmailRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.320048+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-eda82aa0`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-A52B1 - [P3] CreditCardRedactionTest: T058: Test credit card number redaction
- **Priority**: P3
- **Error Type**: CreditCardRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.321637+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-38100432`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-AA4AA - [P3] SSNRedactionTest: T059: Test SSN-like pattern redaction
- **Priority**: P3
- **Error Type**: SSNRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.322861+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-4440b469`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

## ACT-20260110-6BE79 - [P3] GenericTokenRedactionTest: T060: Test generic token redaction
- **Priority**: P3
- **Error Type**: GenericTokenRedactionTest
- **Source**: `raise_af.py:redact_secrets_from_text`
- **Run**: comprehensive-test-suite
- **Created**: 2026-01-10T08:36:51.324047+00:00
- **Duplicate Guard**: `ACTIFIX-raise_af-py:redact_secrets_from_text-f9f5ae15`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-E06CC - [P1] FrontendArchitectureMigration: RF001: Mirror Pokertool React/TypeScript architecture into a new Actifix frontend (same build toolin
- **Priority**: P1
- **Error Type**: FrontendArchitectureMigration
- **Source**: `frontend/setup`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.943771+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-setup-a351b34f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-B69DC - [P1] FrontendStyling: RF002: Replace landing view with a single black page that renders the text 'Love Actifix - Always Bi
- **Priority**: P1
- **Error Type**: FrontendStyling
- **Source**: `frontend/theme`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.944974+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-theme-4072cc5e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-D6DA7 - [P1] FrontendDe-scoping: RF004: Remove poker-specific components, hooks, API calls, and state from the imported architecture;
- **Priority**: P1
- **Error Type**: FrontendDe-scoping
- **Source**: `frontend/cleanup`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.946783+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-cleanup-81fca4e5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-7E4E2E - [P2] FrameworkInitialization: Actifix framework initialization - beginning self-development
- **Priority**: P2
- **Error Type**: FrameworkInitialization
- **Source**: `bootstrap.py:create_initial_ticket`
- **Run**: actifix-bootstrap
- **Created**: 2026-01-10T07:12:39.967290+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:create_initial_ticket-04c923cc`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>AI Remediation Notes</summary>

Error Type: FrameworkInitialization
Error Message: Actifix framework initialization - beginning self-development
Source Location: bootstrap.py:create_initial_ticket
Priority: P2

REMEDIATION REQUIREMENTS:
1. Read and follow ALL project documentation
2. Identify root cause from stack trace and file c
...
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-D98594 - [P2] DevelopmentMilestone: Development milestone: Core error capture system implemented. RaiseAF.py completed with comprehensiv
- **Priority**: P2
- **Error Type**: DevelopmentMilestone
- **Source**: `bootstrap.py:track_development_progress`
- **Run**: actifix-development
- **Created**: 2026-01-10T07:12:39.968894+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:track_development_progress-d3986d97`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>AI Remediation Notes</summary>

Error Type: DevelopmentMilestone
Error Message: Development milestone: Core error capture system implemented. RaiseAF.py completed with comprehensive error tracking, context capture, duplicate prevention, and AI notes generation. Ready for DoAF implementation.
Source Location: bootstrap.py:track_dev
...
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-A86B5 - [P2] FrontendAsset: RF003: Add a small pangolin image asset (local, optimized) and display it alongside the hero text wi
- **Priority**: P2
- **Error Type**: FrontendAsset
- **Source**: `frontend/assets`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.945860+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-assets-d75c09b1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-FA130 - [P2] FrontendTooling: RF005: Wire up build/test scripts (npm/yarn) matching Pokertool's setup, adjusted for Actifix brandi
- **Priority**: P2
- **Error Type**: FrontendTooling
- **Source**: `frontend/tooling`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.947719+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-tooling-1f27e54b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-EE25B - [P2] FrontendTesting: RF006: Add minimal frontend tests/linters to assert the black background, gold hero text content, an
- **Priority**: P2
- **Error Type**: FrontendTesting
- **Source**: `frontend/testing`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.948668+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-testing-e9fdd49c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-AD730 - [P2] DevelopmentMilestone: Development milestone: Basic test suite created. Created comprehensive tests for core error capture 
- **Priority**: P2
- **Error Type**: DevelopmentMilestone
- **Source**: `bootstrap.py:track_development_progress`
- **Run**: actifix-development
- **Created**: 2026-01-10T08:12:20.553696+00:00
- **Duplicate Guard**: `ACTIFIX-bootstrap-py:track_development_progress-8b021e69`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>AI Remediation Notes</summary>

Error Type: DevelopmentMilestone
Error Message: Development milestone: Basic test suite created. Created comprehensive tests for core error capture functionality. Next: implement DoAF for ticket processing.
Source Location: bootstrap.py:track_development_progress
Priority: P2

REMEDIATION REQUIREMEN
...
</details>
- Summary: Processed comprehensive test ticket

#### ACT-20260110-E5F3D - [P3] FrontendDocs: RF007: Update documentation for Actifix frontend setup, run, and build steps; note the absence of po
- **Priority**: P3
- **Error Type**: FrontendDocs
- **Source**: `frontend/docs`
- **Run**: frontend-migration
- **Created**: 2026-01-10T08:12:13.949648+00:00
- **Duplicate Guard**: `ACTIFIX-frontend-docs-8e60e04e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>
- Summary: Processed comprehensive test ticket

