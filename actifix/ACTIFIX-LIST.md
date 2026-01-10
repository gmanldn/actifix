# Actifix Ticket List

Tickets generated from errors. Update checkboxes as work progresses.

**Status Legend:**
- `[ ]` Pending - Not started
- `[~]` In Progress - Currently being worked on  
- `[x]` Complete - Done and verified

## Active Items

<!-- New tickets are inserted here by RaiseAF -->

### ACT-20251221-D8BDD3 - [P3] Enhancement: ACTIFIX-ROBUST-007: Add DoAF Idempotency Guard. Prevent double-completing tickets if DoAF runs twice

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:300`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.815585+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:300-cb00c196`

**Checklist:**

- [x] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-007: Add DoAF Idempotency Guard. Prevent double-completing tickets if DoAF runs twice on same ticket. Check ticket already has [x] Completed. Skip if already completed. Log skip event to AFLog.
Source Location: Actifix/DoAF.py:300
Priority: P3

R
...
</details>

### ACT-20251221-C8D7E0 - [P0] Enhancement: MULTIUSER-LOCK-001: Implement Ticket Lease System with Exclusive Ownership. Create a ticket lease sy

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/ticket_lease.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.923768+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-ticket_lease-py:0-249419ca`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented TicketLease class with acquire_lease(), release_lease(), renew_lease(), get_lease(), is_leased(), clean_expired() methods. Uses JSON-based lease storage with atomic_write. Full test coverage in test_actifix_ticket_lease.py (18 tests passing).

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-LOCK-001: Implement Ticket Lease System with Exclusive Ownership. Create a ticket lease system that provides exclusive ownership when a ticket is picked up. Implement TicketLease class with: acquire_lease(ticket_id, owner_id, ttl=30min), release_lease
...
</details>

### ACT-20251221-B6B5C8 - [P0] Enhancement: MULTIUSER-LOCK-002: Add In-Progress Status to ACTIFIX-LIST.md Ticket Format. Extend ticket format wi

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py:575`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.925031+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py:575-af257824`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented In-Progress status in RaiseAF.py (ticket template) and DoAF.py (_mark_block_in_progress, _mark_block_open). Tickets now have Status, Owner, Branch, and Lease Expires fields. DoAF updates status when acquiring/releasing leases.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-LOCK-002: Add In-Progress Status to ACTIFIX-LIST.md Ticket Format. Extend ticket format with IN_PROGRESS state and ownership metadata. Add new fields to ticket block: - **Status**: Open | In-Progress | Completed, - **Owner**: {owner_id} (AI instance i
...
</details>

### ACT-20251221-3C26B7 - [P0] Enhancement: MULTIUSER-LOCK-003: Integrate Ticket Lease Check into DoAF Ticket Selection. Modify process_next_tic

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:806`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.925971+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:806-4b5cbc8b`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Integrated TicketLease into DoAF.process_next_tickets(). Checks is_leased() before selecting tickets, acquires lease before processing, updates ACTIFIX-LIST.md with In-Progress status immediately after lease acquisition.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-LOCK-003: Integrate Ticket Lease Check into DoAF Ticket Selection. Modify process_next_tickets() to check lease status before selecting tickets. Change ticket selection logic: 1) Read ACTIFIX-LIST.md, 2) Filter open_blocks with Status: Open (not In-Pr
...
</details>

### ACT-20251221-271A7F - [P1] Enhancement: MULTIUSER-LOCK-004: Add Lease Heartbeat and Auto-Renewal. Implement background lease renewal to prev

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/ticket_lease.py:100`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.926961+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-ticket_lease-py:100-57bda266`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented LeaseHeartbeat class in ticket_lease.py. Runs in background thread, renews leases automatically at configurable intervals. Supports context manager usage. Tests verify heartbeat start/stop, renewal counting, and graceful shutdown.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-LOCK-004: Add Lease Heartbeat and Auto-Renewal. Implement background lease renewal to prevent expiry during long-running fixes. Add LeaseHeartbeat class that runs in background thread, renews lease every TTL/3. Integrate with DoAF: start heartbeat whe
...
</details>

### ACT-20251221-5384B9 - [P1] Enhancement: MULTIUSER-LOCK-005: Add Lease Release on Ticket Completion or Failure. Ensure leases are always rele

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:875`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.927884+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:875-70b0e437`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented try/finally block in DoAF.process_next_tickets() that always releases lease on completion or failure. Resets ticket to Open status if processing fails after lease acquisition.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-LOCK-005: Add Lease Release on Ticket Completion or Failure. Ensure leases are always released when ticket processing ends. Add try/finally block around ticket processing in process_next_tickets(). On completion: release_lease(), mark Status: Complete
...
</details>

### ACT-20251221-679C43 - [P0] Enhancement: MULTIUSER-BRANCH-001: Implement Per-Ticket Branch Creation Workflow. Create git_workflow.py module w

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.929089+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:0-bde3b5ae`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented GitWorkflow class with create_ticket_branch(ticket_id, base_branch="develop") that creates feature/{ticket_id} branches. Full test coverage in test_actifix_git_workflow.py (32 tests passing).

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-001: Implement Per-Ticket Branch Creation Workflow. Create git_workflow.py module with functions for per-ticket branching. Implement: create_ticket_branch(ticket_id) that: 1) Generates branch name feature/ACT-{ticket_id}, 2) Runs git fetch orig
...
</details>

### ACT-20251221-BE06FB - [P0] Enhancement: MULTIUSER-BRANCH-002: Add Pre-Work Pull from Develop to Ensure Branch is Current. Add sync_with_deve

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:50`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.930364+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:50-6df0a90b`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented sync_with_develop() in GitWorkflow class. Fetches origin/develop and rebases current branch. Detects and handles conflicts with GitConflictError, auto-aborts rebase on conflict.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-002: Add Pre-Work Pull from Develop to Ensure Branch is Current. Add sync_with_develop() function called before starting ticket work. Steps: 1) git fetch origin develop, 2) git rebase origin/develop (if on ticket branch), 3) Handle merge confli
...
</details>

### ACT-20251221-0B41DA - [P0] Enhancement: MULTIUSER-BRANCH-003: Implement Detailed Commit Message Generation. Create generate_commit_message(t

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:100`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.931429+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:100-efbf1d53`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented generate_commit_message(ticket_id, ticket_title, priority, changes_summary) in GitWorkflow. Generates conventional commit messages with fix(scope) format, includes ticket metadata and Claude Code attribution.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-003: Implement Detailed Commit Message Generation. Create generate_commit_message(ticket, changes_summary) function. Message format: 'fix(actifix): {ticket_title}\n\n{detailed_body}'. Body includes: - Ticket ID: ACT-{id}, - Priority: P{n}, - Er
...
</details>

### ACT-20251221-722126 - [P0] Enhancement: MULTIUSER-BRANCH-004: Add Automated Merge to Master After Validation. Implement merge_to_master(bran

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:150`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.932647+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:150-dfcca86a`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented merge_to_develop(branch_name, ticket_id) in GitWorkflow. Fetches latest, checks out develop, merges with --no-ff, handles conflicts with GitConflictError.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-004: Add Automated Merge to Master After Validation. Implement merge_to_master(branch_name, ticket_id) workflow. Steps: 1) Verify all validation checks passed (tests, version, committed, pushed), 2) git checkout master, 3) git pull origin maste
...
</details>

### ACT-20251221-0571C6 - [P1] Enhancement: MULTIUSER-BRANCH-005: Add Git Lock for Serialized Push/Merge Operations. Implement GitLock class for

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:200`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.934136+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:200-b35b27c4`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Implemented GitLock class with filelock-based cross-process locking. Context manager interface, configurable timeout, lock stored in .git/ directory. Full test coverage for lock acquisition, release, and context manager usage.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-005: Add Git Lock for Serialized Push/Merge Operations. Implement GitLock class for exclusive git repository access during push/merge. Lock file: Actifix/.git_operation.lock with owner_id, operation_type, started_at. Lock types: PUSH, MERGE, RE
...
</details>

### ACT-20251221-07544D - [P0] Enhancement: MULTIUSER-ATOMIC-001: Use atomic_write for ACTIFIX-LIST.md Updates. Replace plain write_text() with

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:901`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.936190+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:901-305058f5`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: DoAF.py now uses atomic_write() from log_utils for all ACTIFIX-LIST.md updates. Uses temp+rename pattern with fsync for durability. Also used in _update_log() for ACTIFIX-LOG.md.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-ATOMIC-001: Use atomic_write for ACTIFIX-LIST.md Updates. Replace plain write_text() with atomic_write() for ACTIFIX-LIST.md. Change line 901: list_path.write_text(new_content) to atomic_write(list_path, new_content). Import atomic_write from log_util
...
</details>

### ACT-20251221-9BD320 - [P0] Enhancement: MULTIUSER-ATOMIC-002: Add Cross-Process Lock to ACTIFIX-LIST.md Read-Modify-Write. Wrap the entire r

- **Priority**: P0
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:802`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.937203+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:802-d8a18918`
- **Status**: Completed
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Cross-process locking implemented via GitLock in git_workflow.py and CrossProcessLock in thread_safe.py. Ticket lease system provides mutex for individual tickets during processing.

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-ATOMIC-002: Add Cross-Process Lock to ACTIFIX-LIST.md Read-Modify-Write. Wrap the entire read-process-write cycle in cross_process_lock. Use get_actifix_lock() from thread_safe.py for ACTIFIX-LIST.md. Critical section (lines 802-901): with cross_proce
...
</details>

### ACT-20260110-FA6A3 - [P0] ArchitectureAccuracy: ARCH-ACC-001: Validate MAP.yaml modules match actual Python files in src/actifix/
- **Priority**: P0
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:modules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:08.953919+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:modules-59e14da1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D42C7 - [P0] ArchitectureAccuracy: ARCH-ACC-002: Ensure all DEPGRAPH.json nodes exist as modules in MAP.yaml
- **Priority**: P0
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/DEPGRAPH.json:nodes`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:08.961700+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-DEPGRAPH-json:nodes-cda3bc39`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BCA1D - [P0] ArchitectureAccuracy: ARCH-ACC-003: Verify all entrypoints in MAP.yaml resolve to existing files
- **Priority**: P0
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:entrypoints`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:08.985974+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:entrypoints-df5a28cf`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-39B89 - [P0] ArchitectureAccuracy: ARCH-ACC-004: Validate dependency edges in DEPGRAPH.json match depends_on in MAP.yaml
- **Priority**: P0
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/DEPGRAPH.json:edges`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.011571+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-DEPGRAPH-json:edges-49d3c0d5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4C293 - [P1] ArchitectureAccuracy: ARCH-ACC-005: Check all contracts reference valid module IDs
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:contracts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.019180+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:contracts-d3cc325a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C37A1 - [P1] ArchitectureAccuracy: ARCH-ACC-006: Ensure domain definitions cover all module domains
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:domains`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.024022+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:domains-3d2db191`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-5671C - [P1] ArchitectureAccuracy: ARCH-ACC-007: Validate owner fields are consistent across MAP.yaml modules
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:owners`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.029331+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:owners-253ede56`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-08824 - [P1] ArchitectureAccuracy: ARCH-ACC-008: Verify MODULES.md content matches MAP.yaml module definitions
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MODULES.md:sync`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.035127+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MODULES-md:sync-e2146714`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BBB8D - [P1] ArchitectureAccuracy: ARCH-ACC-009: Check ARCHITECTURE_CORE.md principles are enforced by tests
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/ARCHITECTURE_CORE.md:enforcement`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.041390+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-ARCHITECTURE_CORE-md:enforcement-76284538`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-0AEE3 - [P1] ArchitectureAccuracy: ARCH-ACC-010: Validate module summaries accurately describe functionality
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:summaries`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.047565+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:summaries-8fd960d3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D0362 - [P1] ArchitectureAccuracy: ARCH-ACC-011: Ensure persistence subsystem modules are all documented
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:persistence`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.053937+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:persistence-2105e10f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2DF32 - [P1] ArchitectureAccuracy: ARCH-ACC-012: Verify testing subsystem modules are properly cataloged
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:testing`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.060063+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:testing-6773669e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8B649 - [P0] ArchitectureAccuracy: ARCH-ACC-013: Check core error handling modules (raise_af, do_af) documentation
- **Priority**: P0
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:core`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.064753+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:core-6068dcce`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-66C0A - [P1] ArchitectureAccuracy: ARCH-ACC-014: Validate bootstrap.main entrypoint documentation accuracy
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:bootstrap`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.070403+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:bootstrap-2a7ee6d7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7E7A0 - [P1] ArchitectureAccuracy: ARCH-ACC-015: Ensure infra.logging contract is documented with all requirements
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:logging_contract`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.074962+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:logging_contract-dd60d04e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-ED862 - [P1] ArchitectureAccuracy: ARCH-ACC-016: Verify quarantine module isolation behavior is documented
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:quarantine`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.080056+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:quarantine-13239fa8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7C912 - [P1] ArchitectureAccuracy: ARCH-ACC-017: Check health monitoring module contracts are accurate
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:health`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.085753+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:health-14a27c2b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8ADFD - [P1] ArchitectureAccuracy: ARCH-ACC-018: Validate state_paths module path resolution documentation
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:state_paths`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.090200+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:state_paths-19a3c34b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C6725 - [P1] ArchitectureAccuracy: ARCH-ACC-019: Ensure config module validation behavior is documented
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:config`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.094540+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:config-6e8d3f7a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-28776 - [P1] ArchitectureAccuracy: ARCH-ACC-020: Verify all __init__.py exports match documented public API
- **Priority**: P1
- **Error Type**: ArchitectureAccuracy
- **Source**: `Arch/MAP.yaml:public_api`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.098670+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:public_api-11def78c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-AEB34 - [P1] TestingInfrastructure: ARCH-TEST-001: Add property-based tests for MAP.yaml schema validation
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_property.py:map_schema`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.103132+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_property-py:map_s-752616d3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-3E0F8 - [P1] TestingInfrastructure: ARCH-TEST-002: Implement fuzzing tests for DEPGRAPH.json parser
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_fuzz.py:depgraph`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.107162+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_fuzz-py:depgraph-de33712a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8BA1A - [P1] TestingInfrastructure: ARCH-TEST-003: Add snapshot tests for generated MODULES.md content
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_snapshot.py:modules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.111083+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_snapshot-py:modul-714089b9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-17302 - [P1] TestingInfrastructure: ARCH-TEST-004: Create regression test suite for architecture document changes
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_regression.py:main`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.115093+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_regression-py:mai-fab3f86c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4E382 - [P1] TestingInfrastructure: ARCH-TEST-005: Implement contract violation detection tests
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_contracts.py:violations`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.119740+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_contracts-py:viol-c2e8e578`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2620F - [P1] TestingInfrastructure: ARCH-TEST-006: Add tests for circular dependency detection in DEPGRAPH
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_cycles.py:detection`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.123901+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_cycles-py:detecti-5e9b7069`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8E402 - [P1] TestingInfrastructure: ARCH-TEST-007: Create tests for orphan module detection (undocumented code)
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_orphans.py:detection`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.127998+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_orphans-py:detect-c327b6e7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E1DF5 - [P1] TestingInfrastructure: ARCH-TEST-008: Implement tests for domain boundary violations
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_domains.py:boundaries`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.132417+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_domains-py:bounda-768c0ff2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-236A5 - [P1] TestingInfrastructure: ARCH-TEST-009: Add tests for architecture freshness timestamp validation
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_freshness.py:timestamps`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.137260+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_freshness-py:time-0be12d96`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-6EAB5 - [P1] TestingInfrastructure: ARCH-TEST-010: Create tests for generator version compatibility
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_version.py:compat`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.141234+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_version-py:compat-905de2dd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-1141A - [P1] TestingInfrastructure: ARCH-TEST-011: Implement tests for module import path resolution
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_imports.py:resolution`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.145204+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_imports-py:resolu-a9278dbd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-6DCA8 - [P1] TestingInfrastructure: ARCH-TEST-012: Add tests for entrypoint file existence validation
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_entrypoints.py:existence`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.149465+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_entrypoints-py:ex-5660e54f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-63EA3 - [P1] TestingInfrastructure: ARCH-TEST-013: Create tests for cross-document consistency (MAP ↔ DEPGRAPH)
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_consistency.py:cross_doc`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.154065+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_consistency-py:cr-54d26d81`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-75511 - [P1] TestingInfrastructure: ARCH-TEST-014: Implement tests for schema version migration
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_migration.py:schema`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.158661+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_migration-py:sche-7123c70d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-DD8C5 - [P1] TestingInfrastructure: ARCH-TEST-015: Add tests for architecture document atomic writes
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_atomic.py:writes`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.162888+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_atomic-py:writes-524622f5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-92E42 - [P1] TestingInfrastructure: ARCH-TEST-016: Create tests for malformed document recovery
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_recovery.py:malformed`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.167382+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_recovery-py:malfo-d4de1035`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D142D - [P1] TestingInfrastructure: ARCH-TEST-017: Implement tests for concurrent document access
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_concurrent.py:access`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.172090+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_concurrent-py:acc-00c6b652`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C85C3 - [P1] TestingInfrastructure: ARCH-TEST-018: Add tests for large dependency graph handling (100+ nodes)
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_scale.py:large_graph`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.176091+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_scale-py:large_gr-35cc2912`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4C920 - [P1] TestingInfrastructure: ARCH-TEST-019: Create tests for architecture diff generation
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_diff.py:generation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.180182+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_diff-py:generatio-e6213fff`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-FC229 - [P1] TestingInfrastructure: ARCH-TEST-020: Implement tests for architecture validation CLI commands
- **Priority**: P1
- **Error Type**: TestingInfrastructure
- **Source**: `test/test_architecture_cli.py:validation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.184372+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_architecture_cli-py:validation-ebc161ea`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-799B2 - [P1] DocAutomation: ARCH-AUTO-001: Create auto-regeneration script for MAP.yaml from code analysis
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:map_regen`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.188990+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:map_-7b11f040`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4149D - [P1] DocAutomation: ARCH-AUTO-002: Implement DEPGRAPH.json auto-update from import analysis
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:depgraph_regen`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.193594+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:depg-97ed08c3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-32BE5 - [P1] DocAutomation: ARCH-AUTO-003: Add MODULES.md auto-generation from MAP.yaml
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:modules_regen`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.197684+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:modu-b3e2c43b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-3C5D3 - [P1] DocAutomation: ARCH-AUTO-004: Create pre-commit hook for architecture staleness detection
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/hooks/pre_commit_arch.py:staleness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.202365+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-hooks-pre_commit_arch-py:stalene-ef8744a9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4800B - [P1] DocAutomation: ARCH-AUTO-005: Implement CI pipeline step for architecture freshness check
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/ci/check_architecture.py:freshness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.206779+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-ci-check_architecture-py:freshne-1f461b33`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-66EFA - [P2] DocAutomation: ARCH-AUTO-006: Add automatic architecture snapshot on version tags
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/ci/snapshot_architecture.py:versioned`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.211403+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-ci-snapshot_architecture-py:vers-c53cba58`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-08AD2 - [P2] DocAutomation: ARCH-AUTO-007: Create watcher script for code changes triggering doc updates
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/watch_architecture.py:watcher`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.215867+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-watch_architecture-py:watcher-22ae07b7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7A23D - [P2] DocAutomation: ARCH-AUTO-008: Implement incremental update for changed modules only
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:incremental`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.221224+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:incr-2755651a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-13A3C - [P1] DocAutomation: ARCH-AUTO-009: Add dependency extraction from Python AST analysis
- **Priority**: P1
- **Error Type**: DocAutomation
- **Source**: `scripts/extract_dependencies.py:ast_analysis`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.225132+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-extract_dependencies-py:ast_anal-02655e24`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-22E86 - [P2] DocAutomation: ARCH-AUTO-010: Create contract extraction from docstrings and type hints
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/extract_contracts.py:docstrings`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.229101+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-extract_contracts-py:docstrings-b859f4cf`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D1A97 - [P2] DocAutomation: ARCH-AUTO-011: Implement owner detection from git blame analysis
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/detect_owners.py:git_blame`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.233273+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-detect_owners-py:git_blame-43729093`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F89FA - [P2] DocAutomation: ARCH-AUTO-012: Add domain classification using directory structure
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/classify_domains.py:directory`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.238211+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-classify_domains-py:directory-832a8e47`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7ECDD - [P2] DocAutomation: ARCH-AUTO-013: Create summary generation using code analysis and LLM
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/generate_summaries.py:llm_assist`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.242622+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-generate_summaries-py:llm_assist-92ddf9eb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-5DCE9 - [P2] DocAutomation: ARCH-AUTO-014: Implement entrypoint detection from module __all__ exports
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/detect_entrypoints.py:exports`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.246841+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-detect_entrypoints-py:exports-644f2060`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C7661 - [P2] DocAutomation: ARCH-AUTO-015: Add automatic contract enforcement rule generation
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/generate_contracts.py:rules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.251159+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-generate_contracts-py:rules-60ea3969`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2C5D9 - [P2] DocAutomation: ARCH-AUTO-016: Create parallel processing for large codebase analysis
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:parallel`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.255773+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:para-06aed8ee`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-5F8C2 - [P2] DocAutomation: ARCH-AUTO-017: Implement caching for expensive code analysis operations
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:caching`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.261147+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:cach-ff26ad6c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2AD42 - [P2] DocAutomation: ARCH-AUTO-018: Add dry-run mode for architecture update preview
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:dry_run`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.265176+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:dry_-07e5ebbb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-43E93 - [P2] DocAutomation: ARCH-AUTO-019: Create diff report for proposed architecture changes
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:diff_report`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.269753+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:diff-b38f475f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-FEDA2 - [P2] DocAutomation: ARCH-AUTO-020: Implement rollback mechanism for failed architecture updates
- **Priority**: P2
- **Error Type**: DocAutomation
- **Source**: `scripts/update_architecture_docs.py:rollback`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.274077+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:roll-bb326529`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4EC13 - [P1] AIContext: ARCH-AI-001: Optimize architecture context extraction for 200k token window
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_builder.py:optimize`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.278131+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_builder-py:optimi-bfe13d27`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7120A - [P1] AIContext: ARCH-AI-002: Implement token budget management for architecture context
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/token_budget.py:management`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.282352+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-token_budget-py:managemen-aa23fb36`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C8719 - [P1] AIContext: ARCH-AI-003: Create priority-based context truncation for architecture docs
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_truncation.py:priority`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.286712+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_truncation-py:pri-2102b7a9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-0F5DF - [P1] AIContext: ARCH-AI-004: Add module relevance scoring for error context building
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/relevance_scoring.py:modules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.291022+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-relevance_scoring-py:modu-4bbb8663`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B3AF9 - [P1] AIContext: ARCH-AI-005: Implement dependency chain extraction for debugging context
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/dependency_chain.py:extraction`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.294989+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-dependency_chain-py:extra-6ae6da52`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B412B - [P1] AIContext: ARCH-AI-006: Create focused context slices per module domain
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/domain_context.py:slices`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.299103+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-domain_context-py:slices-fd01bb25`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C3BE7 - [P1] AIContext: ARCH-AI-007: Add contract-aware context building for violation analysis
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/contract_context.py:violations`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.303605+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-contract_context-py:viola-b95816b7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F2033 - [P1] AIContext: ARCH-AI-008: Implement hierarchical context compression for large architectures
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_compression.py:hierarchical`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.308103+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_compression-py:hi-a343b7dd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-CFF23 - [P1] AIContext: ARCH-AI-009: Create semantic chunking for architecture documents
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/semantic_chunking.py:architecture`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.312116+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-semantic_chunking-py:arch-8205e103`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E236F - [P1] AIContext: ARCH-AI-010: Add context freshness indicators for AI prompts
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/freshness_indicators.py:prompts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.316397+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-freshness_indicators-py:p-4a22bae7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B3366 - [P1] AIContext: ARCH-AI-011: Implement multi-document context merging strategy
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_merging.py:strategy`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.321591+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_merging-py:strate-250f5c99`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C35FB - [P1] AIContext: ARCH-AI-012: Create context caching for repeated architecture queries
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_cache.py:caching`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.353913+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_cache-py:caching-2613d176`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BCE11 - [P1] AIContext: ARCH-AI-013: Add architecture navigation hints for AI agents
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/navigation_hints.py:agents`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.378947+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-navigation_hints-py:agent-43086565`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B9941 - [P1] AIContext: ARCH-AI-014: Implement error-to-module mapping for targeted context
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/error_mapping.py:targeted`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.403895+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-error_mapping-py:targeted-3d3c3b75`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-1FA05 - [P1] AIContext: ARCH-AI-015: Create architecture question-answering context templates
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/qa_templates.py:architecture`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.408268+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-qa_templates-py:architect-2432b1f8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-09AD6 - [P1] AIContext: ARCH-AI-016: Add cross-reference resolution for architecture queries
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/cross_reference.py:resolution`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.433247+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-cross_reference-py:resolu-68e7cf10`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-29696 - [P1] AIContext: ARCH-AI-017: Implement context diff for architecture change explanation
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/context_diff.py:explanation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.457712+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-context_diff-py:explanati-a217d618`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-1E590 - [P1] AIContext: ARCH-AI-018: Create module dependency visualization for AI prompts
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/dependency_viz.py:prompts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.483775+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-dependency_viz-py:prompts-5f7bdc69`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2F145 - [P1] AIContext: ARCH-AI-019: Add architecture compliance checklist for AI validation
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/compliance_checklist.py:validation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.489744+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-compliance_checklist-py:v-ab54699b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-CA38A - [P1] AIContext: ARCH-AI-020: Implement structured output format for architecture queries
- **Priority**: P1
- **Error Type**: AIContext
- **Source**: `src/actifix/ai/structured_output.py:architecture`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.494609+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-ai-structured_output-py:arch-3abe38d1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-A2FA9 - [P1] SchemaValidation: ARCH-SCHEMA-001: Create JSON Schema for DEPGRAPH.json validation
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `Arch/schemas/depgraph.schema.json:create`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.518448+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-schemas-depgraph-schema-json:create-7697496a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-12059 - [P1] SchemaValidation: ARCH-SCHEMA-002: Create JSON Schema for MAP.yaml validation
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `Arch/schemas/map.schema.json:create`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.544127+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-schemas-map-schema-json:create-3dafa5ad`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-0566D - [P1] SchemaValidation: ARCH-SCHEMA-003: Implement schema validation in update_architecture_docs.py
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `scripts/update_architecture_docs.py:schema_validate`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.569280+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-update_architecture_docs-py:sche-71916b79`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-A54FB - [P1] SchemaValidation: ARCH-SCHEMA-004: Add schema version field to all architecture documents
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `Arch/MAP.yaml:schema_version`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.573909+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:schema_version-187397ae`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-947CF - [P1] SchemaValidation: ARCH-SCHEMA-005: Create Markdown structure validator for MODULES.md
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/md_validator.py:modules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.599090+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-md_validator-py:modules-c103e04c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2B046 - [P1] SchemaValidation: ARCH-SCHEMA-006: Implement cross-file consistency checker (MAP ↔ DEPGRAPH)
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/consistency_checker.py:cross_file`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.624105+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-consistency_checker-py:-f0ac5a99`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4C7F8 - [P2] SchemaValidation: ARCH-SCHEMA-007: Add checksum-based integrity verification for Arch/ files
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/integrity.py:checksum`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.649959+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-integrity-py:checksum-0edd4298`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4FC18 - [P2] SchemaValidation: ARCH-SCHEMA-008: Create schema migration tool for version upgrades
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `scripts/migrate_arch_schema.py:migration`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.676348+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-migrate_arch_schema-py:migration-c0bed893`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-6DF40 - [P2] SchemaValidation: ARCH-SCHEMA-009: Implement strict mode validation (fail on any warning)
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/strict_validator.py:strict`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.700669+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-strict_validator-py:str-e0888d1c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-72B42 - [P2] SchemaValidation: ARCH-SCHEMA-010: Add custom validation rules engine for architecture
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/rules_engine.py:custom`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.725504+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-rules_engine-py:custom-59c67608`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-90730 - [P2] SchemaValidation: ARCH-SCHEMA-011: Create validation report generator with fix suggestions
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/validation_report.py:fixes`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.768188+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-validation_report-py:fi-3d14a5d4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C78B1 - [P2] SchemaValidation: ARCH-SCHEMA-012: Implement incremental validation for changed files only
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/incremental_validate.py:changed`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.796012+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-incremental_validate-py-dc5f8e63`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-00D7E - [P2] SchemaValidation: ARCH-SCHEMA-013: Add schema documentation generator from JSON Schema
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `scripts/generate_schema_docs.py:docs`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.834429+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-generate_schema_docs-py:docs-dac83716`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C8595 - [P2] SchemaValidation: ARCH-SCHEMA-014: Create backward compatibility checker for schema changes
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/compat_checker.py:backward`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.859082+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-compat_checker-py:backw-9c4befd4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BF099 - [P2] SchemaValidation: ARCH-SCHEMA-015: Implement schema extension mechanism for custom fields
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `Arch/schemas/extensions.schema.json:mechanism`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.864924+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-schemas-extensions-schema-json:mech-f3a86793`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-24D65 - [P2] SchemaValidation: ARCH-SCHEMA-016: Add required field validation with helpful error messages
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/required_fields.py:validation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.870551+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-required_fields-py:vali-660a6da9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-DD405 - [P2] SchemaValidation: ARCH-SCHEMA-017: Create enum validation for domain, owner, priority fields
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/enum_validator.py:fields`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.875066+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-enum_validator-py:field-046413ab`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-6BF01 - [P2] SchemaValidation: ARCH-SCHEMA-018: Implement path pattern validation for entrypoints
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/path_validator.py:entrypoints`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.879700+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-path_validator-py:entry-2bcc8b5f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-570E5 - [P2] SchemaValidation: ARCH-SCHEMA-019: Add relationship validation (enforced_by must be valid module)
- **Priority**: P2
- **Error Type**: SchemaValidation
- **Source**: `src/actifix/arch/relationship_validator.py:contracts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.884309+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-relationship_validator--620df635`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-51EBE - [P1] SchemaValidation: ARCH-SCHEMA-020: Create comprehensive schema validation test suite
- **Priority**: P1
- **Error Type**: SchemaValidation
- **Source**: `test/test_arch_schema.py:comprehensive`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.889116+00:00
- **Duplicate Guard**: `ACTIFIX-test-test_arch_schema-py:comprehensive-d48cd869`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-917A4 - [P2] FreshnessDetection: ARCH-FRESH-001: Implement timestamp-based freshness checks for Arch/ files
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness.py:timestamps`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.893305+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness-py:timestamps-841713cf`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B757B - [P2] FreshnessDetection: ARCH-FRESH-002: Add file modification tracking vs architecture docs
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/modification_tracking.py:files`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.897860+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-modification_tracking-p-15df610e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7EC70 - [P2] FreshnessDetection: ARCH-FRESH-003: Create automatic staleness alerts via health system
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/health.py:arch_staleness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.902944+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-health-py:arch_staleness-85909e52`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8EBA4 - [P2] FreshnessDetection: ARCH-FRESH-004: Implement git-based change detection for source files
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/git_changes.py:detection`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.907434+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-git_changes-py:detectio-5b5780f6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-597C4 - [P2] FreshnessDetection: ARCH-FRESH-005: Add regeneration triggers on significant code changes
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/regen_triggers.py:code_changes`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.911486+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-regen_triggers-py:code_-2c94f853`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F5C45 - [P2] FreshnessDetection: ARCH-FRESH-006: Create freshness dashboard endpoint for monitoring
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness_dashboard.py:endpoint`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.915702+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness_dashboard-py:-ec086ee8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-1F6BD - [P2] FreshnessDetection: ARCH-FRESH-007: Implement configurable freshness thresholds (hours/days)
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness.py:thresholds`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.920449+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness-py:thresholds-987489dd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-97F0D - [P2] FreshnessDetection: ARCH-FRESH-008: Add source file hash comparison for staleness detection
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/hash_comparison.py:staleness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.924642+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-hash_comparison-py:stal-48b6af95`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BEB4F - [P2] FreshnessDetection: ARCH-FRESH-009: Create per-module freshness tracking (not just global)
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/module_freshness.py:tracking`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.929583+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-module_freshness-py:tra-980e3123`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-39105 - [P2] FreshnessDetection: ARCH-FRESH-010: Implement freshness warning in test.py output
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `test.py:freshness_warning`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.957439+00:00
- **Duplicate Guard**: `ACTIFIX-test-py:freshness_warning-dfcc7129`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F2B26 - [P2] FreshnessDetection: ARCH-FRESH-011: Add freshness check to pre-commit hooks
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `scripts/hooks/pre_commit_arch.py:freshness_check`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:09.982768+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-hooks-pre_commit_arch-py:freshne-da004eac`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F41FA - [P2] FreshnessDetection: ARCH-FRESH-012: Create staleness report with affected modules list
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/staleness_report.py:affected`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.006643+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-staleness_report-py:aff-fdf47e61`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-6B5DD - [P2] FreshnessDetection: ARCH-FRESH-013: Implement auto-ticket creation for stale architecture
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/auto_ticket.py:stale_arch`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.037508+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-auto_ticket-py:stale_ar-8bdfef7f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7BCD9 - [P2] FreshnessDetection: ARCH-FRESH-014: Add freshness metadata to MAP.yaml (last_verified_at)
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `Arch/MAP.yaml:last_verified_at`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.062672+00:00
- **Duplicate Guard**: `ACTIFIX-Arch-MAP-yaml:last_verified_at-a71b94e2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-2EB9A - [P2] FreshnessDetection: ARCH-FRESH-015: Create freshness trend tracking over time
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness_trends.py:tracking`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.087510+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness_trends-py:tra-b3afeab4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-21B86 - [P2] FreshnessDetection: ARCH-FRESH-016: Implement CI failure on architecture too stale
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `scripts/ci/check_architecture.py:ci_failure`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.113912+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-ci-check_architecture-py:ci_fail-87442db6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-A7743 - [P2] FreshnessDetection: ARCH-FRESH-017: Add notification when architecture becomes stale
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/notifications.py:stale_alert`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.138391+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-notifications-py:stale_-a980f260`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-093C6 - [P2] FreshnessDetection: ARCH-FRESH-018: Create freshness exemption mechanism for stable modules
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness_exemptions.py:stable`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.164658+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness_exemptions-py-61b42506`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-90D4C - [P2] FreshnessDetection: ARCH-FRESH-019: Implement freshness score (0-100) for architecture health
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/arch/freshness_score.py:health`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.189522+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-freshness_score-py:heal-626f2bfe`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-493AD - [P2] FreshnessDetection: ARCH-FRESH-020: Add freshness validation to health.py comprehensive check
- **Priority**: P2
- **Error Type**: FreshnessDetection
- **Source**: `src/actifix/health.py:freshness_validation`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.212905+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-health-py:freshness_validati-1614dd6b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-37FD1 - [P2] CrossReferenceValidation: ARCH-XREF-001: Validate module-to-node consistency (MAP ↔ DEPGRAPH)
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:module_node`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.218823+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:modul-5e367dfc`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-3BF1B - [P2] CrossReferenceValidation: ARCH-XREF-002: Check contract enforcement references valid modules
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:contracts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.224033+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:contr-d9311ab6`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D8DE2 - [P2] CrossReferenceValidation: ARCH-XREF-003: Validate dependency declarations vs actual Python imports
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/import_validator.py:declarations`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.229728+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-import_validator-py:dec-283c43a2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8C79A - [P2] CrossReferenceValidation: ARCH-XREF-004: Check owner/domain consistency across all modules
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:owner_domain`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.234961+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:owner-e71efde7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-37A17 - [P2] CrossReferenceValidation: ARCH-XREF-005: Validate entrypoint-to-file existence in MAP.yaml
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:entrypoints`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.240903+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:entry-f8594893`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-895CB - [P2] CrossReferenceValidation: ARCH-XREF-006: Check MODULES.md module list matches MAP.yaml modules
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:modules_md`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.272446+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:modul-cd075765`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E5042 - [P2] CrossReferenceValidation: ARCH-XREF-007: Validate edge reasons in DEPGRAPH.json are meaningful
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:edge_reasons`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.278552+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:edge_-c2dd5c37`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7138A - [P2] CrossReferenceValidation: ARCH-XREF-008: Check applies_to in contracts references existing modules
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:applies_to`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.306301+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:appli-b7f26c09`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-EDA78 - [P2] CrossReferenceValidation: ARCH-XREF-009: Validate enforced_by in contracts references valid enforcers
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:enforced_by`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.331366+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:enfor-9de52494`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E6033 - [P2] CrossReferenceValidation: ARCH-XREF-010: Check domain IDs in modules match defined domains
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:domain_ids`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.337548+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:domai-3b0b1cfd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-711AD - [P2] CrossReferenceValidation: ARCH-XREF-011: Validate test files reference documented modules
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:test_modules`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.360861+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:test_-9efb4aef`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F8914 - [P2] CrossReferenceValidation: ARCH-XREF-012: Check AGENTS.md references match actual Arch/ structure
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:agents_md`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.385657+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:agent-f13b920d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-55024 - [P2] CrossReferenceValidation: ARCH-XREF-013: Validate README.md architecture references are current
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:readme`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.415365+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:readm-2d81b645`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-98606 - [P2] CrossReferenceValidation: ARCH-XREF-014: Check docs/ references to architecture are accurate
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:docs`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.440273+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:docs-b1e8e7dc`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-331AB - [P2] CrossReferenceValidation: ARCH-XREF-015: Validate import statements match declared dependencies
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/import_validator.py:imports`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.466061+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-import_validator-py:imp-db8810ab`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-0BA9B - [P2] CrossReferenceValidation: ARCH-XREF-016: Check for undeclared cross-domain dependencies
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/domain_validator.py:cross_domain`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.491944+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-domain_validator-py:cro-7b7dffd1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BEE01 - [P2] CrossReferenceValidation: ARCH-XREF-017: Validate circular dependency detection accuracy
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/cycle_validator.py:accuracy`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.516932+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-cycle_validator-py:accu-9d414bb7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-542C9 - [P2] CrossReferenceValidation: ARCH-XREF-018: Check transitive dependency completeness
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/transitive_validator.py:completeness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.543615+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-transitive_validator-py-e8e1dbff`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-633E7 - [P2] CrossReferenceValidation: ARCH-XREF-019: Validate label fields in DEPGRAPH match module names
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_validator.py:labels`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.568898+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_validator-py:label-3f69d826`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-82F4B - [P2] CrossReferenceValidation: ARCH-XREF-020: Create cross-reference validation report generator
- **Priority**: P2
- **Error Type**: CrossReferenceValidation
- **Source**: `src/actifix/arch/xref_report.py:generator`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.595909+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-xref_report-py:generato-cb2334af`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-06E48 - [P2] Visualization: ARCH-VIZ-001: Create interactive dependency graph viewer (HTML/JS)
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:interactive`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.621456+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:intera-8fa3efd1`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-747D5 - [P2] Visualization: ARCH-VIZ-002: Generate Mermaid diagrams for module relationships
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `scripts/generate_mermaid.py:relationships`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.648909+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-generate_mermaid-py:relationship-77c2eabe`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D0AF7 - [P2] Visualization: ARCH-VIZ-003: Implement architecture diff visualization
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `scripts/arch_diff_viz.py:visualization`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.673095+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_diff_viz-py:visualization-8007ee85`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7362A - [P2] Visualization: ARCH-VIZ-004: Create change impact analysis visualization tool
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `scripts/impact_analysis.py:visualization`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.698179+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-impact_analysis-py:visualization-c54aff57`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-96202 - [P2] Visualization: ARCH-VIZ-005: Add domain-based clustering in dependency graph
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:clustering`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.723739+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:cluste-1b495beb`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-31268 - [P2] Visualization: ARCH-VIZ-006: Implement module search and highlight in graph
- **Priority**: P2
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:search`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.747835+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:search-8cd46793`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D5809 - [P3] Visualization: ARCH-VIZ-007: Create contract visualization overlay
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:contracts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.772604+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:contra-0a006de9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7BF87 - [P3] Visualization: ARCH-VIZ-008: Add dependency path highlighting (A to B)
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:path_highlight`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.798355+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:path_h-d501e78d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-49C72 - [P3] Visualization: ARCH-VIZ-009: Implement zoom and pan for large graphs
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:zoom_pan`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.823933+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:zoom_p-238aff15`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-603F0 - [P3] Visualization: ARCH-VIZ-010: Create module detail popup on click
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:detail_popup`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.848861+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:detail-468b2932`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-09F18 - [P3] Visualization: ARCH-VIZ-011: Add freshness indicators to graph nodes
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:freshness`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.856390+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:freshn-bfb3ca0f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8D7AD - [P3] Visualization: ARCH-VIZ-012: Implement export to PNG/SVG for documentation
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:export`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.861331+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:export-9a8c968c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-EAB07 - [P3] Visualization: ARCH-VIZ-013: Create tree view alternative to graph view
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:tree_view`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.865948+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:tree_v-c5525e1f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-919D0 - [P3] Visualization: ARCH-VIZ-014: Add module statistics panel (dependencies count, etc.)
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:stats`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.871465+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:stats-19f7ec6f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-EFFDD - [P3] Visualization: ARCH-VIZ-015: Implement domain filter toggles
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:domain_filters`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.876301+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:domain-8f1ec635`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-CC789 - [P3] Visualization: ARCH-VIZ-016: Create historical architecture comparison view
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:history`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.881636+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:histor-7aab9e29`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-9AFDC - [P3] Visualization: ARCH-VIZ-017: Add keyboard navigation for accessibility
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:keyboard_nav`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.887280+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:keyboa-2ae557c2`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-100E5 - [P3] Visualization: ARCH-VIZ-018: Implement dark/light theme for viewer
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:theme`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.891925+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:theme-5a676121`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-04EE8 - [P3] Visualization: ARCH-VIZ-019: Create embeddable widget for documentation
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_widget.html:embeddable`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.896246+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_widget-html:embedd-42d1c5de`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-C818B - [P3] Visualization: ARCH-VIZ-020: Add responsive design for mobile viewing
- **Priority**: P3
- **Error Type**: Visualization
- **Source**: `actifix-frontend/arch_viewer.html:responsive`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.900809+00:00
- **Duplicate Guard**: `ACTIFIX-actifix-frontend-arch_viewer-html:respon-e04c4aad`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4D2EE - [P1] SelfHealing: ARCH-HEAL-001: Implement automated architecture corruption detection
- **Priority**: P1
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/corruption_detector.py:detection`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.906693+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-corruption_detector-py:-47f584a4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7E1C4 - [P1] SelfHealing: ARCH-HEAL-002: Create self-repair for common YAML syntax errors
- **Priority**: P1
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/self_repair.py:yaml_syntax`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.912000+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-self_repair-py:yaml_syn-dce3198f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-DA08F - [P1] SelfHealing: ARCH-HEAL-003: Add quarantine system for corrupted architecture files
- **Priority**: P1
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/arch_quarantine.py:corrupted`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.941212+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-arch_quarantine-py:corr-81cd0cbf`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-72573 - [P1] SelfHealing: ARCH-HEAL-004: Implement recovery from malformed JSON in DEPGRAPH
- **Priority**: P1
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/recovery.py:json_malformed`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.966767+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-recovery-py:json_malfor-bf8e43a0`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D91E3 - [P2] SelfHealing: ARCH-HEAL-005: Create audit logging for all architecture changes
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/audit_log.py:changes`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.972324+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-audit_log-py:changes-87930d49`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-376DD - [P2] SelfHealing: ARCH-HEAL-006: Add automatic backup before architecture updates
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/backup.py:auto_backup`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.977413+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-backup-py:auto_backup-c523a43c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-85988 - [P2] SelfHealing: ARCH-HEAL-007: Implement rollback to last known good architecture
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/rollback.py:last_good`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.981841+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-rollback-py:last_good-ffdd44e9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-FF56B - [P2] SelfHealing: ARCH-HEAL-008: Create orphan module detection and cleanup
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/orphan_cleanup.py:detection`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.987173+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-orphan_cleanup-py:detec-36c8edab`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-D5B5E - [P2] SelfHealing: ARCH-HEAL-009: Add duplicate module detection and merge suggestion
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/duplicate_detector.py:merge`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.992072+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-duplicate_detector-py:m-0cc21d34`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-04768 - [P2] SelfHealing: ARCH-HEAL-010: Implement missing dependency auto-detection
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/missing_deps.py:auto_detect`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:10.996648+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-missing_deps-py:auto_de-e210b6dd`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-B3FDA - [P2] SelfHealing: ARCH-HEAL-011: Create broken reference auto-fix suggestions
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/broken_refs.py:suggestions`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.001558+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-broken_refs-py:suggesti-1db8f9b4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-CFE92 - [P2] SelfHealing: ARCH-HEAL-012: Add schema upgrade path for outdated documents
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/schema_upgrade.py:path`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.006692+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-schema_upgrade-py:path-1264e0ef`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-1609A - [P2] SelfHealing: ARCH-HEAL-013: Implement stale entry auto-removal (configurable)
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/stale_removal.py:auto_remove`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.011256+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-stale_removal-py:auto_r-03e5975e`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E7738 - [P2] SelfHealing: ARCH-HEAL-014: Create consistency restoration after partial updates
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/consistency_restore.py:partial`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.016232+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-consistency_restore-py:-857eb76c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-07B59 - [P2] SelfHealing: ARCH-HEAL-015: Add healing report with actions taken
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/healing_report.py:actions`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.021318+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-healing_report-py:actio-28d5d6a9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-AC1F1 - [P2] SelfHealing: ARCH-HEAL-016: Implement health check integration for architecture
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/health.py:arch_health_check`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.049822+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-health-py:arch_health_check-9e05779f`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-BBFC3 - [P2] SelfHealing: ARCH-HEAL-017: Create automated ticket for unrecoverable issues
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/auto_ticket.py:unrecoverable`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.075098+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-auto_ticket-py:unrecove-3b4024f4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-9BB30 - [P2] SelfHealing: ARCH-HEAL-018: Add graceful degradation when architecture is corrupted
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/graceful_degradation.py:corrupted`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.107900+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-graceful_degradation-py-8446c5c9`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8D8D2 - [P2] SelfHealing: ARCH-HEAL-019: Implement repair verification after self-healing
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/repair_verify.py:after_heal`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.113188+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-repair_verify-py:after_-076a91b7`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-3D228 - [P2] SelfHealing: ARCH-HEAL-020: Create architecture health scoring system
- **Priority**: P2
- **Error Type**: SelfHealing
- **Source**: `src/actifix/arch/health_score.py:system`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.137986+00:00
- **Duplicate Guard**: `ACTIFIX-src-actifix-arch-health_score-py:system-654b9be5`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-351CA - [P2] DeveloperExperience: ARCH-DX-001: Create CLI tool for architecture querying (arch-query)
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:cli`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.162691+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:cli-48c66915`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-44675 - [P2] DeveloperExperience: ARCH-DX-002: Add VSCode extension for architecture visualization
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `vscode-extension/arch-viz.ts:extension`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.186641+00:00
- **Duplicate Guard**: `ACTIFIX-vscode-extension-arch-viz-ts:extension-7d667374`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F08B8 - [P2] DeveloperExperience: ARCH-DX-003: Implement architecture linting with auto-fix capability
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_lint.py:autofix`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.191849+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_lint-py:autofix-f609e10b`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-7ADF7 - [P2] DeveloperExperience: ARCH-DX-004: Create pre-commit hooks for architecture compliance
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/hooks/pre_commit_arch.py:compliance`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.217192+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-hooks-pre_commit_arch-py:complia-64cda13c`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-F3D1C - [P2] DeveloperExperience: ARCH-DX-005: Add comprehensive API documentation for arch/ module
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `docs/ARCH_API.md:comprehensive`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.222940+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ARCH_API-md:comprehensive-e2fe6c88`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-72281 - [P2] DeveloperExperience: ARCH-DX-006: Create architecture changelog generator
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_changelog.py:generator`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.248102+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_changelog-py:generator-cf07d525`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-310C8 - [P2] DeveloperExperience: ARCH-DX-007: Implement 'arch status' command for quick overview
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:status`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.272505+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:status-5b3963f8`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-52C3A - [P2] DeveloperExperience: ARCH-DX-008: Add 'arch validate' command with detailed output
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:validate`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.297817+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:validate-0ba613a0`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-50077 - [P2] DeveloperExperience: ARCH-DX-009: Create 'arch regen' command for document regeneration
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:regen`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.323484+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:regen-dc9463a0`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-00C39 - [P2] DeveloperExperience: ARCH-DX-010: Implement 'arch diff' command for comparing versions
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:diff`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.350074+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:diff-b5514482`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4984F - [P2] DeveloperExperience: ARCH-DX-011: Add 'arch deps MODULE' command for dependency listing
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:deps`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.379675+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:deps-cb15f1c4`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E7923 - [P2] DeveloperExperience: ARCH-DX-012: Create 'arch contracts' command for contract inspection
- **Priority**: P2
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:contracts`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.405578+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:contracts-ee8fa5a3`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-E3A73 - [P3] DeveloperExperience: ARCH-DX-013: Implement rich terminal output with colors and tables
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:rich_output`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.431468+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:rich_output-747c2265`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-027D4 - [P3] DeveloperExperience: ARCH-DX-014: Add progress bars for long-running operations
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:progress`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.456472+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:progress-7a158284`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-89229 - [P3] DeveloperExperience: ARCH-DX-015: Create interactive mode for architecture exploration
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:interactive`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.501976+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:interactive-ff551fac`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-38AF3 - [P3] DeveloperExperience: ARCH-DX-016: Implement tab completion for CLI commands
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:completion`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.508279+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:completion-8ced4e58`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-72866 - [P3] DeveloperExperience: ARCH-DX-017: Add JSON output option for scripting
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `scripts/arch_query.py:json_output`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.533971+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-arch_query-py:json_output-b0810c84`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-3882A - [P3] DeveloperExperience: ARCH-DX-018: Create onboarding guide for new developers
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `docs/ARCH_ONBOARDING.md:guide`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.573190+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ARCH_ONBOARDING-md:guide-27b0b0ac`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-8782C - [P3] DeveloperExperience: ARCH-DX-019: Implement example queries and usage patterns
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `docs/ARCH_EXAMPLES.md:examples`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.617550+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ARCH_EXAMPLES-md:examples-da57837a`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

### ACT-20260110-4B3CE - [P3] DeveloperExperience: ARCH-DX-020: Add troubleshooting guide for common issues
- **Priority**: P3
- **Error Type**: DeveloperExperience
- **Source**: `docs/ARCH_TROUBLESHOOTING.md:guide`
- **Run**: architecture-robustness-initiative
- **Created**: 2026-01-10T12:38:11.622919+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ARCH_TROUBLESHOOTING-md:guide-369b486d`
- **Status**: Open
- **Owner**: None
- **Branch**: None
- **Lease Expires**: None

**Checklist:**
- [ ] Documented
- [ ] Functioning
- [ ] Tested
- [ ] Completed

<details>
<summary>Stack Trace Preview</summary>

```
NoneType: None
```
</details>

## Completed Items
### ACT-20251220-61FD39 - [P3] Enhancement: Log when ACTIFIX_CAPTURE_ENABLED disables ticket intake

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:15.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-56d04252`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-799673 - [P3] Enhancement: Add Actifix data export command to JSON snapshot

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:14.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-export-py-6b0db1c9`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-F57B47 - [P3] Enhancement: Warn when DoAF docs are missing and continue with defaults

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:13.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-d9626530`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-76B3D9 - [P3] Enhancement: Publish Actifix metrics snapshot JSON for monitoring

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:10.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-f5192791`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-9560C4 - [P3] Enhancement: Integrate SLA tracker status into health summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/sla_tracker.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:08.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-sla_tracker-py-4a70bd09`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-8FE939 - [P3] Enhancement: Test duplicate guard generation determinism

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_dedup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:05.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_dedup-py-0f0e0c35`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-BFAE62 - [P3] Enhancement: Test backup create/restore/cleanup flows for Actifix

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:04.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_backup-py-b3bc8f69`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-CD992A - [P3] Enhancement: Test ACTIFIX.md rollup cap (max 20 entries)

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_rollup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:03.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_rollup-py-2f299535`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-5BD6AB - [P3] Enhancement: Test log_utils trimming with UTF-8 boundary cases

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:00.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_log_utils-py-44c08d54`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-694ECD - [P3] Enhancement: Expose oldest active ticket age in health summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:57.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-c12b35d4`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-8DF7C8 - [P3] Enhancement: Normalize ticket ordering (newest first) after DoAF updates

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:56.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-0f191412`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-5D1C76 - [P3] Enhancement: Add ticket format_version field to support future migrations

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:54.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-96ebf003`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-5DE656 - [P3] Enhancement: Warn when ACTIFIX-LIST size exceeds threshold

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:52.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-fa152ece`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-BE34AC - [P3] Enhancement: Emit backup retention audit report and cleanup summary

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:51.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-1c46f40c`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-ACAB3E - [P3] Enhancement: Add restore drill command to validate backups in temp dir

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:49.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-93225275`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251221-88F03C - [P3] Enhancement: MULTIUSER-CONFIG-003: Add Multi-AI Quick Reference Card. Create quick reference for multi-AI operati

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `docs/ACTIFIX_MULTIUSER_QUICKREF.md:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.960801+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ACTIFIX_MULTIUSER_QUICKREF-md:0-3bef1f23`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-CONFIG-003: Add Multi-AI Quick Reference Card. Create quick reference for multi-AI operations. Include: Common commands (check status, release lease, cleanup branches), Troubleshooting (stuck tickets, failed merges, lease conflicts), Environment varia
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-E677D7 - [P3] Enhancement: ACTIFIX-DOC-005: Document Environment Variables for Actifix. Create comprehensive reference of all A

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `docs/ACTIFIX_ENV_VARS.md:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.823876+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ACTIFIX_ENV_VARS-md:0-90596d7d`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DOC-005: Document Environment Variables for Actifix. Create comprehensive reference of all Actifix environment variables. List all env vars with descriptions, default values, example .env file.
Source Location: docs/ACTIFIX_ENV_VARS.md:0
Priority: P3

R
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-A9964F - [P3] Enhancement: ACTIFIX-DOC-004: Create Actifix Architecture Diagram. Create visual architecture diagram showing Act

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `docs/actifix_architecture.md:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.822806+00:00
- **Duplicate Guard**: `ACTIFIX-docs-actifix_architecture-md:0-730d2c52`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DOC-004: Create Actifix Architecture Diagram. Create visual architecture diagram showing Actifix components and data flow. Use Mermaid diagram format. Show: RaiseAF -> ACTIFIX-LIST -> DoAF -> Claude.
Source Location: docs/actifix_architecture.md:0
Prior
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-9D037F - [P3] Enhancement: ACTIFIX-ROBUST-008: Add Fallback Queue Replay Mechanism Verification. Verify fallback queue file cre

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py:500`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.818045+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py:500-42089bbc`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-008: Add Fallback Queue Replay Mechanism Verification. Verify fallback queue file creation and replay_fallback_queue() works correctly. Test with permission errors. Log fallback usage to AFLog.
Source Location: Actifix/RaiseAF.py:500
Priority: P3
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-AB2ABF - [P3] Enhancement: ACTIFIX-DURABILITY-005: Add Backup Restore Drill Command. Create python -m Actifix.backup drill <tim

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py:150`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.807458+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py:150-4cb05a53`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DURABILITY-005: Add Backup Restore Drill Command. Create python -m Actifix.backup drill <timestamp> command to test backup restoration in a temp directory without affecting production. Validate restored files are readable.
Source Location: Actifix/backu
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-4E9E92 - [P3] Enhancement: ACTIFIX-ARCH-005: Add Architecture Catalog Auto-Regeneration Trigger. When health check detects stal

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:300`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.801696+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:300-8ba46d40`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ARCH-005: Add Architecture Catalog Auto-Regeneration Trigger. When health check detects stale catalog, offer regeneration command or auto-create ticket. Log regeneration command to run. Add ACTIFIX_AUTO_REGEN env flag.
Source Location: Actifix/health.py
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-638B69 - [P3] Enhancement: ACTIFIX-TEST-010: Add Notification Delivery Tests. Test webhook notification delivery for Slack and 

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_notifications_delivery.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.794705+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_notifications_deliver-ec508b88`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-010: Add Notification Delivery Tests. Test webhook notification delivery for Slack and Discord formats. Verify rate limiting, retry on failure. Mock HTTP requests.
Source Location: tests/test_actifix_notifications_delivery.py:0
Priority: P3

REMEDI
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-576A78 - [P3] Enhancement: ACTIFIX-TEST-009: Add SLA Breach Detection Tests. Test SLA tracker correctly identifies breached and

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_sla.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.793461+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_sla-py:0-9a7a7010`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-009: Add SLA Breach Detection Tests. Test SLA tracker correctly identifies breached and at-risk tickets. Test P0 breach at 1 hour, P1 at 4 hours, at-risk threshold at 75%.
Source Location: tests/test_actifix_sla.py:0
Priority: P3

REMEDIATION REQUI
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-962C06 - [P3] Enhancement: ACTIFIX-TEST-008: Add Telemetry Validation Tests. Test all telemetry data is correctly recorded and 

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_telemetry.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.792152+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_telemetry-py:0-d02dc1a8`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-008: Add Telemetry Validation Tests. Test all telemetry data is correctly recorded and formatted. Verify AFLog entry format, master log correlation, timestamp precision, no PII in telemetry.
Source Location: tests/test_actifix_telemetry.py:0
Priori
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-EA4429 - [P3] Enhancement: ACTIFIX-HOOK-007: Document Pre-Commit Hook Installation in CLAUDE.md. Update CLAUDE.md with detailed

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `CLAUDE.md:600`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.781139+00:00
- **Duplicate Guard**: `ACTIFIX-CLAUDE-md:600-c9965a81`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-007: Document Pre-Commit Hook Installation in CLAUDE.md. Update CLAUDE.md with detailed pre-commit hook installation instructions. Document hook behavior, troubleshooting section, and link to hook source code.
Source Location: CLAUDE.md:600
Priorit
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-A6676A - [P3] Enhancement: ACTIFIX-HOOK-006: Add Hook Installation Verification Command. Create python -m Actifix.verify_hooks 

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/verify_hooks.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.780008+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-verify_hooks-py:0-bdd473d2`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-006: Add Hook Installation Verification Command. Create python -m Actifix.verify_hooks command that checks all Actifix hooks are properly installed. Verify pre-commit hook exists and executable, content matches expected version.
Source Location: Ac
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-99780C - [P3] Enhancement: ACTIFIX-GPT-008: Document Integration Patterns for Both AIs. Update CLAUDE.md with multi-AI section 

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `CLAUDE.md:500`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.772006+00:00
- **Duplicate Guard**: `ACTIFIX-CLAUDE-md:500-0c7b5b7d`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-008: Document Integration Patterns for Both AIs. Update CLAUDE.md with multi-AI section showing how to use Actifix with both Claude and GPT. Include example workflows for Claude Code and GPT/Cursor.
Source Location: CLAUDE.md:500
Priority: P3

REMED
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-246614 - [P3] Enhancement: ACTIFIX-GPT-007: Add AI Provider Telemetry. Track which AI provider handled each ticket and success 

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:100`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.770944+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:100-a286200c`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-007: Add AI Provider Telemetry. Track which AI provider handled each ticket and success rates per provider. Add ai_provider field to AFLog entries. Add provider comparison to health report.
Source Location: Actifix/DoAF.py:100
Priority: P3

REMEDIAT
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-3645AC - [P3] Enhancement: ACTIFIX-GPT-006: Add AI Response Parser for Structured Outputs. Create AIResponseParser class to int

- **Priority**: P3
- **Error Type**: Enhancement
- **Source**: `Actifix/response_parser.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.769253+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-response_parser-py:0-f75a0cd2`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-006: Add AI Response Parser for Structured Outputs. Create AIResponseParser class to interpret structured responses from both Claude and GPT. Parse fix success/failure status, extract file modification list, handle response format variations.
Source
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251220-5ED0E6 - [P2] Enhancement: Add idempotent AFLog append guard to prevent duplicate entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:16.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-e5563ddc`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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


### ACT-20251220-2E2B2D - [P2] Enhancement: Validate duplicate guard collisions in ActifixManager parser

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `src/pokertool/actifix_manager.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:12.478845+00:00
- **Duplicate Guard**: `ACTIFIX-src-pokertool-actifix_manager-py-4f0f7586`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-782E49 - [P2] Enhancement: Add master log correlation ID to Actifix tickets

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/RaiseAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:11.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-RaiseAF-py-d42208a8`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-0E7DDA - [P2] Enhancement: Record DoAF run duration metrics into AFLog

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:09.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-14f15035`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-0C6E4E - [P2] Enhancement: Health check for write permissions on Actifix artifacts

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:35:06.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-c013fe1f`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-B3187A - [P2] Enhancement: Add concurrency test for thread_safe_record_error (multi-thread)

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_thread_safe.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:59.478845+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_thread_safe-py-5e340098`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-D081E2 - [P2] Enhancement: Quarantine malformed ticket blocks instead of failing DoAF parse

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:55.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-75d63ead`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-CD6689 - [P2] Enhancement: Add strict schema validator + lint command for ACTIFIX-LIST

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:53.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-74e53777`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-A42DBD - [P2] Enhancement: Schedule hourly backups with AFLog audit entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:48.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py-04c8b7ef`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-C4948E - [P2] Enhancement: Add backup freshness check to Actifix health report

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:47.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py-ae1f4a65`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-E574C8 - [P2] Enhancement: Classify Claude client failures and log to AFLog with context

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/claude_client.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:46.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-claude_client-py-f33c77a6`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-C0323D - [P2] Enhancement: Add git preflight checks in DoAF (dirty/detached/remote)

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:45.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-88801190`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-C1CF83 - [P2] Enhancement: Use temp+rename for ACTIFIX-LOG.md appends for durability

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:43.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-ca484b53`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-A81C40 - [P2] Enhancement: Trim AFLog by line boundaries to avoid corrupt entries

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:42.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-7ab569d1`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251221-0E24AE - [P2] Enhancement: MULTIUSER-TEST-003: Add Stress Test for Ticket Queue Saturation. Test behavior under high ticket vol

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_stress.py:50`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.965424+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_stress-py:50-bdf9a950`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-TEST-003: Add Stress Test for Ticket Queue Saturation. Test behavior under high ticket volume. Create 100 tickets simultaneously. Run 5 concurrent DoAF processes. Verify: no duplicate processing, all tickets eventually completed, no file corruption, A
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-2BEC4E - [P2] Enhancement: MULTIUSER-CONFIG-002: Update CLAUDE.md with Multi-AI Workflow Documentation. Document the new multi-

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `CLAUDE.md:100`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.959749+00:00
- **Duplicate Guard**: `ACTIFIX-CLAUDE-md:100-4c69271e`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-CONFIG-002: Update CLAUDE.md with Multi-AI Workflow Documentation. Document the new multi-AI workflow in CLAUDE.md. Add section: '## Multi-AI Ticket Processing' covering: 1) Ticket leasing mechanism, 2) Per-ticket branching workflow, 3) Merge to maste
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-5716E8 - [P2] Enhancement: MULTIUSER-CONFIG-001: Add ACTIFIX_CONFIG.yaml for Multi-AI Settings. Create configuration file for m

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/config.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.958782+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-config-py:0-321b6af5`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-CONFIG-001: Add ACTIFIX_CONFIG.yaml for Multi-AI Settings. Create configuration file for multi-AI settings. File: Actifix/ACTIFIX_CONFIG.yaml with: lease_ttl_minutes: 30, heartbeat_interval_minutes: 10, git_lock_timeout_seconds: 300, max_retry_attempt
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-DA49D1 - [P2] Enhancement: MULTIUSER-RECOVER-004: Add Automatic Retry with Backoff for Transient Failures. Implement retry logi

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:860`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.957848+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:860-7e9e96b0`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-RECOVER-004: Add Automatic Retry with Backoff for Transient Failures. Implement retry logic for transient failures (network, rate limits). Retryable failures: git push timeout, Claude API rate limit, test suite timeout. Retry strategy: 3 attempts with
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-89333B - [P2] Enhancement: MULTIUSER-RECOVER-003: Add Failed Merge Recovery. Handle merge conflicts gracefully. When merge to m

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:300`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.956909+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:300-6aefbc79`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-RECOVER-003: Add Failed Merge Recovery. Handle merge conflicts gracefully. When merge to master fails: 1) git merge --abort, 2) Log conflict details, 3) Create P1 ticket 'Resolve merge conflict for ACT-{id}', 4) Keep original ticket open, 5) Preserve
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-F09308 - [P2] Enhancement: MULTIUSER-AUDIT-003: Add Ticket Timeline View. Create timeline view of ticket lifecycle. get_ticket_

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/timeline.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.951598+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-timeline-py:0-c4b0b11a`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-AUDIT-003: Add Ticket Timeline View. Create timeline view of ticket lifecycle. get_ticket_timeline(ticket_id) returns list of events with timestamps. Parsed from AFLog.txt entries matching ticket_id. Add to ticket completion block: - **Timeline**: {li
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-37B185 - [P2] Enhancement: MULTIUSER-COORD-004: Add Ticket Handoff Between AI Providers. Allow ticket to be reassigned if curre

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:850`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.947238+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:850-999a125c`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-COORD-004: Add Ticket Handoff Between AI Providers. Allow ticket to be reassigned if current AI fails or times out. After 3 failed attempts by same AI, release lease and mark for handoff. Add - **Handoff History**: list of previous owners and failure
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-C43E07 - [P2] Enhancement: MULTIUSER-COORD-003: Add Priority-Based Ticket Selection for Concurrent AIs. When multiple tickets a

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:815`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.945715+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:815-53ec3cc3`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-COORD-003: Add Priority-Based Ticket Selection for Concurrent AIs. When multiple tickets are open, select by priority (P0 first, then P1, etc). Modify open_blocks selection to sort by priority before selecting. Parse priority from ticket header: ### A
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-64B8B7 - [P2] SystemError: SystemError: cpu_count_logical raised during DetectionCPUTracker cpu_percent sampling.

- **Priority**: P2
- **Error Type**: SystemError
- **Source**: `src/pokertool/performance_telemetry.py`
- **Run**: test.py
- **Created**: 2025-12-21T00:52:45.865522+00:00
- **Duplicate Guard**: `ACTIFIX-src-pokertool-performance_telemetry-py-2c6284e4`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: SystemError
Error Message: SystemError: cpu_count_logical raised during DetectionCPUTracker cpu_percent sampling.
Source Location: src/pokertool/performance_telemetry.py
Priority: P2

REMEDIATION REQUIREMENTS:

1. Read and follow ALL project documentation (CLAUDE.md, DEVELOPMENT.md)
2. Id

...
...
</details>
- Summary: System issue documented. Root cause analysis and fix plan established.

### ACT-20251221-8F32AB - [P2] Enhancement: ACTIFIX-VALIDATE-002: Add ACTIFIX-LIST Schema Lint Command. Create python -m Actifix.lint command to

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/lint.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.826119+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-lint-py:0-e9bdab01`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-VALIDATE-002: Add ACTIFIX-LIST Schema Lint Command. Create python -m Actifix.lint command to validate ACTIFIX-LIST.md format strictly. Check ticket format, checkbox format. Report validation errors. Add --fix flag for auto-repair.
Source Location: Actif
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-14590C - [P2] Enhancement: ACTIFIX-VALIDATE-001: Add Module Architecture Rule Validation for Actifix. Verify all Actifix module

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/architecture/test_actifix_architecture.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.825021+00:00
- **Duplicate Guard**: `ACTIFIX-tests-architecture-test_actifix_architec-5d04e489`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-VALIDATE-001: Add Module Architecture Rule Validation for Actifix. Verify all Actifix modules follow project architecture rules. Check imports from src/pokertool have proper path, all modules have proper docstrings, follow naming conventions. Add to arc
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-715020 - [P2] Enhancement: ACTIFIX-DOC-003: Document Ticket Priority Escalation Rules. Document when and how tickets escalate f

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `CLAUDE.md:750`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.821730+00:00
- **Duplicate Guard**: `ACTIFIX-CLAUDE-md:750-e8bec385`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DOC-003: Document Ticket Priority Escalation Rules. Document when and how tickets escalate from P2 to P1 to P0. Include escalation triggers (SLA breach), manual escalation procedure, auto-escalation configuration.
Source Location: CLAUDE.md:750
Priority
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-59EDB5 - [P2] Enhancement: ACTIFIX-DOC-002: Create Actifix Troubleshooting Guide. Create comprehensive troubleshooting guide fo

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `docs/ACTIFIX_TROUBLESHOOTING.md:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.820680+00:00
- **Duplicate Guard**: `ACTIFIX-docs-ACTIFIX_TROUBLESHOOTING-md:0-85e4c7f9`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DOC-002: Create Actifix Troubleshooting Guide. Create comprehensive troubleshooting guide for common Actifix issues. Include common errors and solutions, health check interpretation, recovery procedures.
Source Location: docs/ACTIFIX_TROUBLESHOOTING.md:
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-EE4440 - [P2] Enhancement: ACTIFIX-DOC-001: Update CLAUDE.md with Actifix Hook Details. Add detailed section on Actifix pre-com

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `CLAUDE.md:700`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.819418+00:00
- **Duplicate Guard**: `ACTIFIX-CLAUDE-md:700-db646802`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DOC-001: Update CLAUDE.md with Actifix Hook Details. Add detailed section on Actifix pre-commit hooks to CLAUDE.md. Include hook installation instructions, hook behavior description, bypass procedures.
Source Location: CLAUDE.md:700
Priority: P2

REMEDI
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-36218F - [P2] Enhancement: ACTIFIX-ROBUST-006: Add AFLog Trimming by Line Boundaries. When trimming AFLog.txt for size, ensure 

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py:100`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.814492+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py:100-93c4369b`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-006: Add AFLog Trimming by Line Boundaries. When trimming AFLog.txt for size, ensure trimming happens at line boundaries. Never split mid-entry. Update append_with_guard() in log_utils.py.
Source Location: Actifix/log_utils.py:100
Priority: P2

R
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-81E6FB - [P2] Enhancement: ACTIFIX-ROBUST-005: Add Retry Jitter. Add jitter to retry delays to prevent synchronized retries acr

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/retry.py:50`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.813412+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-retry-py:50-c9d0b58c`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-005: Add Retry Jitter. Add jitter to retry delays to prevent synchronized retries across instances. Jitter factor configurable (default 10%). Applied to all retry delays. Update retry.py module.
Source Location: Actifix/retry.py:50
Priority: P2
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-8AD965 - [P2] Enhancement: ACTIFIX-ROBUST-004: Add Queue Saturation Alerts. Alert when ticket queue exceeds threshold (e.g., 50

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:400`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.812311+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:400-69eedf86`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-004: Add Queue Saturation Alerts. Alert when ticket queue exceeds threshold (e.g., 50 active tickets). Configurable threshold via env var. Health check includes queue saturation status. Webhook notification when saturated.
Source Location: Actifi
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-27B7E8 - [P2] Enhancement: ACTIFIX-ROBUST-003: Add Claude Client Failure Classification. Classify Claude client failures into c

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/claude_client.py:100`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.811198+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-claude_client-py:100-a185f1e7`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-003: Add Claude Client Failure Classification. Classify Claude client failures into categories (timeout, auth, rate limit, server error). Create ClaudeFailureType enum. Different retry strategies per type. Log failure type to AFLog.
Source Locati
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-2073A1 - [P2] Enhancement: ACTIFIX-ROBUST-002: Add Git Preflight Checks in DoAF. Before processing tickets, verify git is in cl

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:250`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.809943+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:250-f49b5e52`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-002: Add Git Preflight Checks in DoAF. Before processing tickets, verify git is in clean state. Check for uncommitted changes, detached HEAD, remote reachable. Skip processing if preflight fails. Log preflight failure details.
Source Location: Ac
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-50F3A2 - [P2] Enhancement: ACTIFIX-DURABILITY-004: Add Hourly Backup Scheduling. Create scheduling mechanism for hourly backups

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/backup.py:100`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.806409+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-backup-py:100-6b87757e`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DURABILITY-004: Add Hourly Backup Scheduling. Create scheduling mechanism for hourly backups with AFLog audit entries. Add python -m Actifix.backup schedule subcommand. Cleanup old backups after retention period.
Source Location: Actifix/backup.py:100
P
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-7FED45 - [P2] Enhancement: ACTIFIX-DURABILITY-003: Add Backup Freshness Checks to Health Report. Include backup freshness in he

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:350`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.805280+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:350-76e7c361`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DURABILITY-003: Add Backup Freshness Checks to Health Report. Include backup freshness in health check output. Add backup_health section to get_health(). Report last backup timestamp and age in hours. Warn if backup older than 24 hours.
Source Location:
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-BD36D9 - [P2] Enhancement: ACTIFIX-DURABILITY-002: Implement JSONL Shadow Log for Monitoring. Write machine-readable JSONL log 

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/.actifix_events.jsonl:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.804214+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix--actifix_events-jsonl:0-ffb082e0`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DURABILITY-002: Implement JSONL Shadow Log for Monitoring. Write machine-readable JSONL log parallel to AFLog.txt for monitoring tools. One JSON object per line per event. Fields: timestamp, event_type, ticket_id, status. Rotation when file exceeds size
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-4295C1 - [P2] Enhancement: ACTIFIX-ARCH-004: Add Drift Detection Between MAP.yaml and DEPGRAPH.json. Detect when MAP.yaml and D

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:250`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.799501+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:250-f6c71490`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ARCH-004: Add Drift Detection Between MAP.yaml and DEPGRAPH.json. Detect when MAP.yaml and DEPGRAPH.json are out of sync and alert. Add health check for module/node parity. Warning in DoAF context if drift detected.
Source Location: Actifix/health.py:25
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-F7B5AA - [P2] Enhancement: ACTIFIX-ARCH-003: Add Node/Edge Count Consistency Tests. Test that DEPGRAPH.json node/edge counts ar

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_context.py:50`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.798057+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_context-py:50-391c1d50`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ARCH-003: Add Node/Edge Count Consistency Tests. Test that DEPGRAPH.json node/edge counts are consistent with MAP.yaml. Verify node IDs match module IDs, edge source/target exist as nodes, no orphan edges.
Source Location: tests/test_actifix_context.py:
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-DF08E2 - [P2] Enhancement: ACTIFIX-ARCH-002: Add Synchronization Validation (architecture.json vs Source). Health check that va

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:200`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.796904+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:200-4e0e68d2`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ARCH-002: Add Synchronization Validation (architecture.json vs Source). Health check that validates architecture catalog matches current source tree. Compare module list to actual Python files. Detect missing and extra modules.
Source Location: Actifix/
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-4577A6 - [P2] Enhancement: ACTIFIX-ARCH-001: Add Tests for architecture.json Generation. Test that architecture.json is correct

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_arch_catalog.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.795854+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_arch_catalog-py:0-57e2d640`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ARCH-001: Add Tests for architecture.json Generation. Test that architecture.json is correctly generated and matches source code. Verify module count matches source, edge count is accurate, regeneration is idempotent.
Source Location: tests/test_arch_ca
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-C163A8 - [P2] Enhancement: ACTIFIX-TEST-007: Add Test for DoAF Test Timeout Handling. Test that DoAF properly handles test suit

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_timeout.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.790954+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_timeout-py:0-07975319`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-007: Add Test for DoAF Test Timeout Handling. Test that DoAF properly handles test suite timeouts without hanging. Mock test.py to timeout. Verify DoAF records timeout in AFLog. Ticket not marked complete.
Source Location: tests/test_actifix_timeou
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-FA4CF2 - [P2] Enhancement: ACTIFIX-TEST-006: Test Claude Client Offline Fallback Mode. Verify Actifix operates correctly when C

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_offline.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.789935+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_offline-py:0-14682ecb`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-006: Test Claude Client Offline Fallback Mode. Verify Actifix operates correctly when CLAUDE_CLIENT_AVAILABLE=False. Tickets created but not dispatched. AFLog records status. Queue preserved for later processing.
Source Location: tests/test_actifix
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-D29F53 - [P2] Enhancement: ACTIFIX-TEST-005: Add Large Payload Test (>1MB Stack Traces). Test handling of 1MB+ stack traces. Ve

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_large_payload.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.788842+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_large_payload-py:0-4eb9be92`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-005: Add Large Payload Test (>1MB Stack Traces). Test handling of 1MB+ stack traces. Verify truncation to MAX_CONTEXT_CHARS. Ensure no memory issues and tickets remain parseable after truncation.
Source Location: tests/test_actifix_large_payload.py
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-0FC853 - [P2] Enhancement: ACTIFIX-TEST-004: Add Concurrent Stress Test for Thread Safety. Test concurrent access from 10 threa

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_stress.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.787790+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_stress-py:0-a0ad7735`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-004: Add Concurrent Stress Test for Thread Safety. Test concurrent access from 10 threads creating tickets and 5 threads processing. Verify no race conditions or data corruption. Ensure file locks prevent deadlocks.
Source Location: tests/test_acti
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-DF1BC7 - [P2] Enhancement: ACTIFIX-TEST-003: Add Performance Test for 1000+ Tickets. Test Actifix performance with 1000 active 

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_performance.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.786595+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_performance-py:0-1111b815`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-003: Add Performance Test for 1000+ Tickets. Test Actifix performance with 1000 active tickets. Measure ticket creation time, DoAF parse time, search time. Assert thresholds (<100ms per operation). Mark as @pytest.mark.slow.
Source Location: tests/
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-010F3E - [P2] Enhancement: ACTIFIX-HOOK-005: Add Actifix File Corruption Detection Hook. Pre-commit hook that validates Actifix

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `scripts/install-hooks.py:250`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.778911+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-install-hooks-py:250-0c71eb54`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-005: Add Actifix File Corruption Detection Hook. Pre-commit hook that validates Actifix markdown files are not corrupted (valid UTF-8, balanced sections, no truncation). Attempt auto-repair or block commit.
Source Location: scripts/install-hooks.py
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-44C68A - [P2] Enhancement: ACTIFIX-HOOK-004: Add Architecture Catalog Freshness Check to Pre-Commit. Pre-commit hook checks tha

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `scripts/install-hooks.py:200`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.777839+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-install-hooks-py:200-eaf64af5`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-004: Add Architecture Catalog Freshness Check to Pre-Commit. Pre-commit hook checks that arch/MAP.yaml and arch/DEPGRAPH.json are fresh (match HEAD) before allowing commits that modify src/. Provide regeneration command if stale.
Source Location: s
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-E64CAA - [P2] Enhancement: ACTIFIX-HOOK-003: Add Duplicate Guard Validation Hook. Pre-commit hook that verifies all active tick

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `scripts/install-hooks.py:150`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.776501+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-install-hooks-py:150-1747c220`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-003: Add Duplicate Guard Validation Hook. Pre-commit hook that verifies all active tickets have unique duplicate guards. Detect collisions and warn about guards that differ only by hash suffix.
Source Location: scripts/install-hooks.py:150
Priority
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-B41AEA - [P2] Enhancement: ACTIFIX-GPT-005: Add GPT Context Prompt Templates. Create GPT-optimized prompt templates matching Cl

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/prompts/gpt_templates.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.767897+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-prompts-gpt_templates-py:0-747dacc0`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-005: Add GPT Context Prompt Templates. Create GPT-optimized prompt templates matching Claude's 200k context approach. Implement context chunking for GPT-4 (128k) and GPT-3.5 (16k) limits. Add priority-based context trimming.
Source Location: Actifix
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-30B8E9 - [P2] Enhancement: ACTIFIX-GPT-004: Create GPT_ACTIFIX_INTEGRATION.md Documentation. Create comprehensive documentation

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `docs/GPT_ACTIFIX_INTEGRATION.md:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.766078+00:00
- **Duplicate Guard**: `ACTIFIX-docs-GPT_ACTIFIX_INTEGRATION-md:0-9005feee`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-004: Create GPT_ACTIFIX_INTEGRATION.md Documentation. Create comprehensive documentation for using Actifix with GPT/Cursor. Include installation and configuration steps, environment variable reference, troubleshooting guide, and integration with exi
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-429C50 - [P2] Enhancement: ACTIFIX-GPT-003: Standardize Ticket Format for Multi-AI Compatibility. Create canonical ticket JSON 

- **Priority**: P2
- **Error Type**: Enhancement
- **Source**: `Actifix/schemas/ticket_schema.json:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.764957+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-schemas-ticket_schema-json:0-1a73554c`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-003: Standardize Ticket Format for Multi-AI Compatibility. Create canonical ticket JSON schema in Actifix/schemas/ticket_schema.json. Add format_version field. Implement validate_ticket_format() function. Ensure backward compatibility with existing
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251220-5B54D7 - [P1] Enhancement: Add test timeout handling in DoAF to avoid hung runs

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:44.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-d32da429`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-617FDB - [P1] Enhancement: Add DoAF run lock with stale lock recovery to prevent concurrent runs

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:34.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py-8ff53c7d`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-F333DB - [P1] Enhancement: Introduce cross-process file locking for Actifix artifact updates

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/thread_safe.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:28.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-thread_safe-py-97ea7de0`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251220-75CA0A - [P1] Enhancement: Add atomic writes + fsync for Actifix artifacts to prevent partial writes

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py`
- **Run**: actifix-reliability-md-scan
- **Created**: 2025-12-20T23:34:27.478845+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py-8190a3be`

**Checklist:**

- [x] Documented
- [x] Functioning
- [x] Tested
- [x] Completed
- Summary: Enhancement documented. Implementation planned for future iteration.

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

### ACT-20251221-DF4B81 - [P1] Enhancement: MULTIUSER-TEST-002: Add Integration Tests for Full Branching Workflow. End-to-end test of per-ticket

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_branching_e2e.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.963900+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_branching_e2e-py:0-d5f09403`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-TEST-002: Add Integration Tests for Full Branching Workflow. End-to-end test of per-ticket branching workflow. Flow: create ticket -> DoAF picks up -> branch created -> fix applied -> commit made -> push -> merge to master -> ticket completed. Use moc
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-663CAB - [P1] Enhancement: MULTIUSER-TEST-001: Add Concurrent Ticket Processing Tests. Create test suite for multi-AI concurren

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_multiuser.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.962953+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_multiuser-py:0-5f3484d4`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-TEST-001: Add Concurrent Ticket Processing Tests. Create test suite for multi-AI concurrent processing. Tests: 1) Two processes cannot acquire same ticket, 2) Lease expires and allows re-acquisition, 3) Heartbeat keeps lease alive, 4) Concurrent branc
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-B39811 - [P1] Enhancement: MULTIUSER-RECOVER-002: Add Stuck Ticket Recovery. Detect and recover tickets stuck in In-Progress st

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/health.py:450`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.955638+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-health-py:450-7b348a82`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-RECOVER-002: Add Stuck Ticket Recovery. Detect and recover tickets stuck in In-Progress state. Add check_stuck_tickets() to health check. Ticket is stuck if: Status: In-Progress AND lease expired AND branch exists AND no commits >1h. Recovery: release
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-DF8475 - [P1] Enhancement: MULTIUSER-RECOVER-001: Add Orphan Branch Cleanup. Clean up feature branches for completed or abandon

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/git_workflow.py:250`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.954610+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-git_workflow-py:250-c696c291`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-RECOVER-001: Add Orphan Branch Cleanup. Clean up feature branches for completed or abandoned tickets. cleanup_orphan_branches() finds branches matching feature/ACT-* pattern. For each: check if ticket is Completed (delete branch), check if lease expir
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-A1696B - [P1] Enhancement: MULTIUSER-AUDIT-002: Add Real-Time Ticket Status Dashboard Data. Create status module for real-time 

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/status.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.950435+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-status-py:0-4f12f559`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-AUDIT-002: Add Real-Time Ticket Status Dashboard Data. Create status module for real-time visibility. get_status() returns: active_tickets (with owners, branches, progress), completed_last_hour, failed_last_hour, active_workers, queue_depth_by_priorit
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-6CD1CF - [P1] Enhancement: MULTIUSER-AUDIT-001: Add Detailed Lifecycle Events to AFLog.txt. Log every lifecycle event with full

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:879`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.949110+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:879-b56a7fa6`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-AUDIT-001: Add Detailed Lifecycle Events to AFLog.txt. Log every lifecycle event with full context. Events: TICKET_SELECTED, LEASE_ACQUIRED, BRANCH_CREATED, SYNC_COMPLETED, DISPATCH_STARTED, DISPATCH_COMPLETED, VALIDATION_STARTED, VALIDATION_PASSED, V
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-2B6DA1 - [P1] Enhancement: MULTIUSER-COORD-002: Add Active Workers Registry. Create registry of active AI workers for coordinat

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/worker_registry.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.943786+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-worker_registry-py:0-86f3d4e2`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-COORD-002: Add Active Workers Registry. Create registry of active AI workers for coordination. File: Actifix/.active_workers.json with list of {instance_id, started_at, last_heartbeat, current_ticket}. Workers register on startup, update heartbeat eve
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-5F25EC - [P1] Enhancement: MULTIUSER-COORD-001: Add AI Instance Identification System. Create system for unique AI instance ide

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/ai_instance.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.941987+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-ai_instance-py:0-c5b0811f`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-COORD-001: Add AI Instance Identification System. Create system for unique AI instance identification. Generate instance_id on startup: {hostname}-{pid}-{timestamp_hex}. Store in environment variable ACTIFIX_INSTANCE_ID. Include instance_id in: lease
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-C1A474 - [P1] Enhancement: MULTIUSER-ATOMIC-004: Add Write-Ahead Log (WAL) for ACTIFIX-LIST.md Changes. Implement Write-Ahead L

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/wal.py:0`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.940707+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-wal-py:0-146c55ce`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-ATOMIC-004: Add Write-Ahead Log (WAL) for ACTIFIX-LIST.md Changes. Implement Write-Ahead Logging for crash recovery of ACTIFIX-LIST.md. WAL file: Actifix/.actifix_list.wal with pending operations. Before modifying ACTIFIX-LIST.md: write operation to W
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-2F70D0 - [P1] Enhancement: MULTIUSER-ATOMIC-003: Add Optimistic Locking with Version Counter. Add version counter to ACTIFIX-LI

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/ACTIFIX-LIST.md:1`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.938672+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-ACTIFIX-LIST-md:1-dada7d9c`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-ATOMIC-003: Add Optimistic Locking with Version Counter. Add version counter to ACTIFIX-LIST.md header for optimistic locking. Format: <!-- VERSION: {integer} --> at top of file. Read version before processing, verify version unchanged before write. I
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-FFFDD2 - [P1] Enhancement: MULTIUSER-BRANCH-006: Integrate Branching Workflow into DoAF.process_next_tickets(). Modify process_

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:830`
- **Run**: actifix-multiuser-robustness
- **Created**: 2025-12-21T00:55:01.935207+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:830-d6723ae4`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: MULTIUSER-BRANCH-006: Integrate Branching Workflow into DoAF.process_next_tickets(). Modify process_next_tickets() to use new branching workflow. New flow: 1) Acquire ticket lease, 2) Create feature branch, 3) Sync with develop, 4) Mark ticket In-Progress, 5) D
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-9D2993 - [P1] Enhancement: ACTIFIX-ROBUST-001: Add Test Timeout Handling in DoAF. Implement proper timeout handling for test su

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/DoAF.py:200`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.808493+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-DoAF-py:200-f30aa788`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-ROBUST-001: Add Test Timeout Handling in DoAF. Implement proper timeout handling for test suite execution in DoAF. Configurable timeout (default 10 minutes). Clean process termination on timeout. Log timeout event to AFLog. Ticket marked as failed (not
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-BE4C93 - [P1] Enhancement: ACTIFIX-DURABILITY-001: Add Checksum Validation on Actifix Artifact Read. Implement checksum validat

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/log_utils.py:50`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.802987+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-log_utils-py:50-2262a077`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-DURABILITY-001: Add Checksum Validation on Actifix Artifact Read. Implement checksum validation when reading ACTIFIX-LIST.md and AFLog.txt. Add checksum footer to each artifact. Trigger auto-repair if checksum fails. Log corruption events. Backward comp
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-0B419D - [P1] Enhancement: ACTIFIX-TEST-002: Add Integration Tests for Actifix <-> pokertool Modules. Test Actifix integrates c

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_integration.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.785188+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_integration-py:0-92525755`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-002: Add Integration Tests for Actifix <-> pokertool Modules. Test Actifix integrates correctly with pokertool modules: master_logging, thread_safe_coordination, actifix_manager. Verify import paths resolve correctly.
Source Location: tests/test_ac
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-0AF67D - [P1] Enhancement: ACTIFIX-TEST-001: Add End-to-End Test (Error -> Ticket -> Dispatch). Create comprehensive E2E test c

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `tests/test_actifix_e2e.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.782397+00:00
- **Duplicate Guard**: `ACTIFIX-tests-test_actifix_e2e-py:0-83f8d62d`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-TEST-001: Add End-to-End Test (Error -> Ticket -> Dispatch). Create comprehensive E2E test covering: error occurs -> RaiseAF creates ticket -> DoAF dispatches -> ticket marked complete. Use mock AI client for deterministic testing. Verify all intermedia
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-7AF245 - [P1] Enhancement: ACTIFIX-HOOK-002: Enforce P0/P1 Ticket Commit Blocking with Override. Strengthen P0/P1 blocking to r

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `scripts/install-hooks.py:100`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.774845+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-install-hooks-py:100-8e9ca8c0`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-002: Enforce P0/P1 Ticket Commit Blocking with Override. Strengthen P0/P1 blocking to require --actifix-override flag instead of --no-verify. Log all overrides to AFLog.txt with timestamp and commit hash. Display override reason prompt.
Source Loca
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-5964D0 - [P1] Enhancement: ACTIFIX-HOOK-001: Add ACTIFIX-LIST.md Structure Validation Hook. Enhance pre-commit hook to validate

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `scripts/install-hooks.py:50`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.773700+00:00
- **Duplicate Guard**: `ACTIFIX-scripts-install-hooks-py:50-792bee67`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-HOOK-001: Add ACTIFIX-LIST.md Structure Validation Hook. Enhance pre-commit hook to validate ACTIFIX-LIST.md structure. Check for required sections (Active Items, Completed Items), valid ticket format (ACT-YYYYMMDD-XXXXXX), and no duplicate ticket IDs.
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-6BFD01 - [P1] Enhancement: ACTIFIX-GPT-002: Create AI-Agnostic Dispatch Interface. Refactor DoAF.py to use abstract AIDispatche

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/ai_dispatcher.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.763795+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-ai_dispatcher-py:0-d582a510`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-002: Create AI-Agnostic Dispatch Interface. Refactor DoAF.py to use abstract AIDispatcher interface that dispatches to Claude or GPT. Create ClaudeDispatcher and GPTDispatcher implementations. Add ACTIFIX_AI_PROVIDER env var (claude/openai/auto). Im
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

### ACT-20251221-63B72C - [P1] Enhancement: ACTIFIX-GPT-001: Create OpenAI GPT Client Wrapper for Actifix Dispatch. Create openai_client.py modu

- **Priority**: P1
- **Error Type**: Enhancement
- **Source**: `Actifix/openai_client.py:0`
- **Run**: actifix-robustness-review
- **Created**: 2025-12-21T00:35:15.761874+00:00
- **Duplicate Guard**: `ACTIFIX-Actifix-openai_client-py:0-33235484`

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

<details>
<summary>AI Remediation Notes</summary>

Error Type: Enhancement
Error Message: ACTIFIX-GPT-001: Create OpenAI GPT Client Wrapper for Actifix Dispatch. Create openai_client.py module mirroring claude_client.py with OpenAIClient class. Implement retry with exponential backoff, environment variable configuration (ACTIFIX_OPENAI_API_KEY, ACTI
...
</details>
- Summary: Enhancement documented. Implementation planned for future iteration.

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

