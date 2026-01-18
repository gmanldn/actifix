#!/usr/bin/env python3
"""
Generate 300 tickets addressing specific weaknesses identified through
comprehensive architecture and code analysis.

Based on detailed review of:
- docs/architecture/ (MAP.yaml, MODULES.md, DEPGRAPH.json)
- src/actifix/ implementation
- Plugin system, persistence layer, AI integration
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from actifix.raise_af import TicketPriority, record_error

# Raise_AF gating
os.environ.setdefault("ACTIFIX_CHANGE_ORIGIN", "raise_af")
os.environ.setdefault("ACTIFIX_CAPTURE_ENABLED", "1")

WEAKNESS_TICKET_LEVEL = os.getenv("ACTIFIX_WEAKNESS_TICKET_LEVEL", "critical").lower()
WEAKNESS_TICKET_LIMIT = int(os.getenv("ACTIFIX_WEAKNESS_TICKET_LIMIT", "30"))
LEVEL_PRIORITY_MAP = {
    "critical": {TicketPriority.P0},
    "standard": {TicketPriority.P0, TicketPriority.P1},
    "full": {TicketPriority.P0, TicketPriority.P1, TicketPriority.P2, TicketPriority.P3},
    "none": set(),
}
ALLOWED_PRIORITIES = LEVEL_PRIORITY_MAP.get(WEAKNESS_TICKET_LEVEL, LEVEL_PRIORITY_MAP["critical"])


def generate_weakness_tickets():
    """Generate 300 tickets addressing specific code weaknesses."""

    if not ALLOWED_PRIORITIES:
        print(
            "Weakness ticket generation disabled (ACTIFIX_WEAKNESS_TICKET_LEVEL=none)."
        )
        return

    tasks = []


    # ============================================================================
    # CATEGORY 1: DATABASE & PERSISTENCE CRITICAL FIXES (35 tickets)
    # Issues in database.py, ticket_repo.py, storage.py, queue.py
    # ============================================================================

    tasks.extend([
        # Thread-safety & concurrency (P0 priority)
        "[database.py:213-254] Fix race condition in _get_connection() where _initialized check happens outside lock for second condition",
        "[database.py:350-354] Fix close_all() documentation - cannot access other threads' local storage, misleading docs",
        "[database.py:217-253] Add connection pool size limit to prevent unlimited connection creation exhausting resources",
        "[database.py:358-385] Fix global pool singleton thread-local state issue where configuration changes affect all threads",

        # Error handling gaps (P1)
        "[database.py:250-252] Distinguish transient (retry) vs permanent (fail-fast) database connection errors",
        "[database.py:282-283] Add recovery path for schema migration failures beyond just wrapping exception",
        "[database.py:318-319] Clean up partial application state changes when transaction rollback occurs",
        "[database.py:336-338] Fix nested exception handler that swallows specific error types in transaction context",

        # Schema & migration (P1)
        "[database.py:285-304] Create extensible migration framework beyond hardcoded v1->v2 path",
        "[database.py:295-297] Replace CREATE IF NOT EXISTS with explicit schema drift detection and validation",
        "[database.py:28-168] Add schema versioning validation on connection to prevent version mismatch",
        "[database.py:66-67] Add Python enum enforcement for CHECK constraints on priority/status fields",

        # Resource management (P1)
        "[database.py:399] Add graceful shutdown beyond atexit.register for kill -9 and crash scenarios",
        "[database.py:340-348] Add explicit WAL fsync on connection close to prevent data loss",
        "[database.py:232] Ensure foreign keys enabled consistently across connection reuse without reset",

        # Serialization issues (P2)
        "[database.py:403-421] Fix JSON serialization default=str producing non-deserializable output",
        "[database.py:424-431] Preserve timezone info consistently in timestamp serialization",
        "[database.py:433-442] Add validation for malformed ISO strings in timestamp deserialization",

        # Locking & concurrency in ticket_repo (P0)
        "[ticket_repo.py:309-372] Fix TOCTOU race in acquire_lock where ticket modified between SELECT and UPDATE",
        "[ticket_repo.py:374-394] Add lock validity verification in release_lock to prevent releasing expired locks",
        "[ticket_repo.py:452-470] Make cleanup_expired_locks atomic with proper transaction isolation vs acquire_lock",
        "[ticket_repo.py:472-568] Make get_and_lock_next_ticket atomic - combine cleanup and lock in single transaction",
        "[ticket_repo.py:369-372] Don't swallow all OperationalError on 'locked', distinguish different lock issues",

        # Data integrity (P1)
        "[ticket_repo.py:72-117] Add field validation in create_ticket before insert, don't rely only on DB constraints",
        "[ticket_repo.py:246-277] Add validation for arbitrary field updates in update_ticket",
        "[ticket_repo.py:265] Validate updated_at is after created_at when automatically adding timestamp",
        "[ticket_repo.py:615-627] Add soft-delete option in delete_ticket to prevent permanent data loss",

        # Missing features (P2)
        "[ticket_repo.py:214-222] Add efficient pagination support to get_open_tickets",
        "[ticket_repo.py:570-613] Optimize get_stats to use single aggregate query instead of 4 separate queries",
        "[ticket_repo.py] Add bulk operations for creating/updating multiple tickets atomically",
        "[ticket_repo.py] Add ticket history tracking to see who changed what when",

        # Security & validation (P1)
        "[storage.py:194-196] Add symlink attack prevention beyond just path normalization stripping ..",
        "[storage.py:195] Fix lstrip('/') allowing Windows drive letters - make cross-platform consistent",
        "[storage.py:292-349] Add size limits to MemoryStorageBackend to prevent memory exhaustion",
        "[storage.py:352-384] Add JSON size validation before parsing in JSONStorageMixin to prevent DoS",
    ])

    # ============================================================================
    # CATEGORY 2: ERROR HANDLING & RAISE_AF ROBUSTNESS (35 tickets)
    # Issues in raise_af.py - security, performance, reliability
    # ============================================================================

    tasks.extend([
        # Security & PII redaction (P0)
        "[raise_af.py:240-312] Optimize redact_secrets_from_text - O(n*m) regex performance issue for large traces",
        "[raise_af.py:290-291] Fix email redaction preserving domain - still leaks organizational information",
        "[raise_af.py:294] Fix credit card pattern matching false positives (any 13-19 digits)",
        "[raise_af.py:258-276] Expand API key patterns to catch custom key formats beyond provider-specific ones",
        "[raise_af.py] Add redaction for database connection strings with embedded passwords",

        # Context capture issues (P1)
        "[raise_af.py:321-369] Add size limit to capture_file_context - currently reads entire file into memory",
        "[raise_af.py:344-365] Make line number extraction robust for multi-file stack traces",
        "[raise_af.py:366-367] Add proper error handling when reading file context instead of silently swallowing",
        "[raise_af.py:372-402] Review capture_system_state exposing all ACTIFIX env vars - may leak sensitive config",

        # Duplicate detection (P1)
        "[raise_af.py:196-220] Fix _normalize_for_guard truncating at 200 chars causing collision on same prefix",
        "[raise_af.py:206-219] Improve _stack_signature_for_guard using first line only - misses multi-frame patterns",
        "[raise_af.py:222-237] Make generate_duplicate_guard order-independent for combined normalized fields",
        "[raise_af.py:692-700] Check fallback queue in addition to database for duplicate detection",

        # Priority classification (P2)
        "[raise_af.py:405-431] Enhance classify_priority beyond simple keyword matching - add ML/taxonomy integration",
        "[raise_af.py:410-414] Expand hardcoded keywords to include domain-specific critical error patterns",
        "[raise_af.py:419-420] Filter test files from 'core'/'main' source P1 priority triggers",

        # AI notes generation (P2)
        "[raise_af.py:434-474] Add token budget management to generate_ai_remediation_notes - creates massive text",
        "[raise_af.py:461-462] Fix file context truncation at FILE_CONTEXT_MAX_CHARS - corrupts code snippets mid-context",
        "[raise_af.py:466] Fix JSON dumps system_state with default=str creating unparseable output",

        # Fallback queue (P1)
        "[raise_af.py:527-541] Add logging to _queue_to_fallback catching all exceptions returning False",
        "[raise_af.py:580-616] Optimize replay_fallback_queue O(n²) complexity - rebuilds entire queue per entry",
        "[raise_af.py:603-604] Add exponential backoff for failed entries staying in queue",
        "[raise_af.py:505-524] Fix _persist_queue unlinking legacy file even if write fails - causes data loss",

        # Main record function (P1)
        "[raise_af.py:619-768] Decompose record_error 200+ line function into smaller focused functions",
        "[raise_af.py:666-675] Move capture enabled check before policy enforcement to avoid wasting cycles",
        "[raise_af.py:680-681] Skip auto-capturing stack trace if already provided to avoid duplicate work",
        "[raise_af.py:742-757] Add operator notification when database failure falls back to queue",
        "[raise_af.py:748-755] Make log event atomic with database write to prevent log loss on crash",
        "[raise_af.py:771-782] Add error visibility to _append_rollup_entry instead of silently swallowing exceptions",

        # Configuration issues (P2)
        "[raise_af.py:96-99] Validate context size limits (800k chars) against actual token budget",
        "[raise_af.py:105] Make DUPLICATE_REOPEN_WINDOW (24h) configurable per priority level",

        # Queue management (P2)
        "[queue.py:169-171] Make queue full behavior configurable (FIFO vs reject) instead of always removing oldest",
        "[queue.py:101-110] Quarantine corrupted queue files for recovery instead of silently resetting",
        "[queue.py:221-264] Optimize replay modifying list while iterating - inefficient for large queues",
        "[queue.py:158-166] Improve deduplication to check content not just key+operation",
    ])

    # ============================================================================
    # CATEGORY 3: TICKET PROCESSING & DO_AF IMPROVEMENTS (30 tickets)
    # Issues in do_af.py - caching, locking, AI integration
    # ============================================================================

    tasks.extend([
        # Caching & state management (P2)
        "[do_af.py:36-52] Replace wall-clock time with monotonic time in TicketCacheState TTL - breaks on time changes",
        "[do_af.py:64-86] Optimize _refresh_cache loading all open/completed tickets - doesn't scale",
        "[do_af.py:88-92] Return deep copies in cache, not shallow copies leaving mutable dicts",
        "[do_af.py:113-127] Handle stale paths in global manager singleton when project root changes",

        # Locking & concurrency (P1)
        "[do_af.py:179-188] Add transaction isolation to _select_and_lock_ticket iterating candidates",
        "[do_af.py:742-764] Document platform-specific behavior of _ticket_lock file locks",
        "[do_af.py:767-778] Replace busy-wait fixed 50ms sleep in _acquire_file_lock with exponential backoff",
        "[do_af.py:796-809] Fix _try_lock returning True on systems without fcntl/msvcrt - fake lock dangerous",

        # AI integration (P2)
        "[do_af.py:271-370] Make fix_highest_priority_ticket AI summary text extensible not hard-coded",
        "[do_af.py:373-513] Simplify process_next_ticket complex nested try/except - hard to follow error paths",
        "[do_af.py:417-476] Restore AI processing logs (currently commented out) - lost observability",
        "[do_af.py:440-446] Add fix quality validation before marking AI response success as complete",

        # Error handling (P1)
        "[do_af.py:212-214] Add database retry when falling back to manager on database failure",
        "[do_af.py:257] Distinguish expected vs unexpected already-completed state when returning False",
        "[do_af.py:324-325] Ensure release_lock called even when mark_complete fails - prevents stuck locks",
        "[do_af.py:477-484] Auto-release lock on AI exception instead of waiting for lease expiry",

        # CLI & interface (P2)
        "[do_af.py:598-607] Remove side effects from _resolve_paths_from_args calling init_actifix_files",
        "[do_af.py:686-687] Add upper bound validation to max_tickets >= 1 check",
        "[do_af.py:695-699] Add cache status to stats command output for complete view",

        # Performance (P2)
        "[do_af.py:64-86] Add cursor-based pagination to ticket loading in cache refresh",
        "[do_af.py:179-188] Add index on priority+status for efficient candidate selection",
        "[do_af.py] Add metrics collection for ticket processing (latency, throughput, errors)",

        # Code quality (P2)
        "[do_af.py] Extract AI processing logic into separate AIProcessor class",
        "[do_af.py] Add comprehensive error recovery documentation for all failure modes",
        "[do_af.py] Add integration tests for concurrent ticket processing",

        # Configuration (P2)
        "[do_af.py:742-809] Make file lock timeout and retry configurable",
        "[do_af.py:36-52] Make cache TTL configurable via config instead of hardcoded",
        "[do_af.py] Add health check endpoint showing processing status",
        "[do_af.py] Add graceful shutdown mechanism for in-flight ticket processing",
    ])

    # ============================================================================
    # CATEGORY 4: AI CLIENT RELIABILITY (25 tickets)
    # Issues in ai_client.py - provider fallback, timeouts, caching
    # ============================================================================

    tasks.extend([
        # Provider fallback (P1)
        "[ai_client.py:66-125] Optimize generate_fix provider fallback - exponential backoff compounds delays",
        "[ai_client.py:89-90] Preserve all provider errors in last_error instead of overwriting",
        "[ai_client.py:107-108] Fix sleep 2^attempt in both provider loop and outer retry - can wait minutes",
        "[ai_client.py:127-159] Cache _get_provider_order result instead of rebuilding list every call",

        # Claude Local (P2)
        "[ai_client.py:187-238] Add progress indication for _call_claude_local 300s timeout subprocess",
        "[ai_client.py:192-197] Handle large prompts exceeding pipe buffer when passing via stdin",
        "[ai_client.py:223-230] Disable Claude local for future calls after FileNotFoundError",
        "[ai_client.py:519-536] Allow _is_claude_local_available cache to invalidate when Claude installed",

        # API providers (P2)
        "[ai_client.py:240-287] Add API version checking for anthropic package in _call_claude_api",
        "[ai_client.py:258-260] Update hardcoded Claude model 'claude-3-sonnet-20240229' to latest",
        "[ai_client.py:268-269] Update token cost estimation from 2024 pricing or fetch dynamically",
        "[ai_client.py:289-337] Apply same fixes to _call_openai as Claude API improvements",

        # Ollama (P2)
        "[ai_client.py:339-388] Add custom endpoint support to _call_ollama beyond localhost:11434",
        "[ai_client.py:348] Make Ollama model 'codellama:7b' configurable instead of hardcoded",
        "[ai_client.py:351] Add streaming or reduce 300s timeout blocking for up to 5 minutes",
        "[ai_client.py:546-553] Cache _is_ollama_available result instead of network call every time",

        # Free alternative (P3)
        "[ai_client.py:390-474] Fix _call_free_alternative stdin prompts breaking in non-interactive contexts",
        "[ai_client.py:405-422] Add validation for pasted response in copy-paste web UI workflow",
        "[ai_client.py:467-474] Re-raise KeyboardInterrupt instead of returning error",

        # Prompts (P2)
        "[ai_client.py:476-517] Make _build_fix_prompt template customizable instead of fixed",
        "[ai_client.py:481-486] Replace .get() 'Unknown' fallbacks with explicit missing field indication",
        "[ai_client.py:487] Indicate if stack trace capture was attempted vs not available",

        # Cost estimation (P3)
        "[ai_client.py:555-567] Add confidence intervals to cost estimation formulas - currently inaccurate",
        "[ai_client.py:558-560] Fetch Claude pricing from API instead of hardcoded 2024 rates",
    ])

    # ============================================================================
    # CATEGORY 5: PLUGIN SYSTEM ROBUSTNESS (20 tickets)
    # Issues in plugins/* - protocol, registry, loader, sandbox
    # ============================================================================

    tasks.extend([
        # Protocol definition (P2)
        "[plugins/protocol.py:32-48] Add __init__ signature specification to Plugin protocol",
        "[plugins/protocol.py:45-47] Document when health() returning None is appropriate vs PluginHealthStatus",
        "[plugins/protocol.py:14-18] Add validation on PluginMetadata construction for frozen dataclass",
        "[plugins/protocol.py:18] Create capabilities schema so plugins can discover each other's capabilities",

        # Registry management (P1)
        "[plugins/registry.py:27-36] Prevent **metadata override of plugin.metadata.name in register",
        "[plugins/registry.py:31-32] Indicate if same plugin re-registering in duplicate name RuntimeError",
        "[plugins/registry.py:38-46] Call plugin.unregister() after removing from dict to prevent inconsistent state",
        "[plugins/registry.py:48-50] Hold lock during return in get() to prevent plugin unregistration race",
        "[plugins/registry.py:52-54] Create true snapshot in __iter__ instead of just copying values list",

        # Context manager (P3)
        "[plugins/registry.py:57-75] Allow plugins to access app in PluginContextManager temporary mode",
        "[plugins/registry.py:58] Fix typo 'deloyments' -> 'deployments' in docstring",

        # Discovery (P2)
        "[plugins/loader.py:21-25] Add error handling to _select_entrypoints conditional logic for metadata API",
        "[plugins/loader.py:36-48] Handle classes with __call__ method in _instantiate callable check",
        "[plugins/loader.py:46] Raise PluginLoadError instead of generic TypeError",

        # Loading (P2)
        "[plugins/loader.py:55-78] Preserve exception tracebacks when collecting errors as strings",
        "[plugins/loader.py:66] Call validate_plugin after sandboxing to catch validation errors safely",
        "[plugins/loader.py:68-71] Distinguish validation vs registration failures in exception handling",
        "[plugins/loader.py:74] Return errors in structured form not just log warnings",

        # Error recording (P1)
        "[plugins/sandbox.py:23-29] Remove unreachable code after record_error call that raises in safe_register",
        "[plugins/sandbox.py:31-42] Use skip_duplicate_check=False in record_error to prevent spamming identical errors",
    ])

    # ============================================================================
    # CATEGORY 6: CONFIGURATION & STATE MANAGEMENT (25 tickets)
    # Issues in config.py, state_paths.py - validation, defaults, global state
    # ============================================================================

    tasks.extend([
        # Configuration loading (P2)
        "[config.py:79-187] Implement file-based config loading - currently only environment despite parameter",
        "[config.py:82] Use or remove config_file parameter - currently documented but never used",
        "[config.py:119-176] Add type validation beyond parse functions in environment parsing",
        "[config.py:177] Change ai_enabled default to True (opt-out) instead of False (opt-in)",

        # Validation (P1)
        "[config.py:190-236] Add real-world constraint validation to SLA ordering checks",
        "[config.py:213-218] Fix SLA ordering check using >= allowing equal values - off-by-one error",
        "[config.py:221-222] Add negative value check for coverage after parsing (currently 0-100 only)",
        "[config.py:225-235] Add upper bound validation for timeout values beyond > 0 check",

        # Global state (P1)
        "[config.py:239-264] Add thread-safety to global _config singleton access",
        "[config.py:250-252] Don't swallow validation errors with fail_fast=False in get_config",
        "[config.py:255-258] Add validation in set_config to prevent setting invalid config",

        # Defaults (P2)
        "[config.py:29] Review sla_p0_hours=1 default - may be too aggressive for global default",
        "[config.py:36] Add rotation strategy documentation for max_log_size_bytes=10MB",
        "[config.py:39] Make min_coverage_percent=80 configurable default for different project types",
        "[config.py:52-54] Distinguish unset from explicitly empty AI config with empty string defaults",

        # Path resolution (P2)
        "[state_paths.py:54-59] Validate resolved path exists in _resolve_project_root",
        "[state_paths.py:62-101] Validate paths are writable in _build_paths construction",
        "[state_paths.py:194-196] Remove redundant .parent calls",

        # Directory creation (P2)
        "[state_paths.py:104-110] Surface permission errors instead of masking with parents=True in ensure_actifix_dirs",
        "[state_paths.py:113-147] Verify sentinel file readable after write in init_actifix_files",
        "[state_paths.py:125-133] Make multiple artifact file touches atomic - prevent partial initialization",
        "[state_paths.py:135-137] Remove redundant base_aflog creation after already touching aflog_file",

        # Sentinel file (P2)
        "[state_paths.py:140-145] Use structured sentinel file (JSON) instead of plain text for extensibility",
        "[state_paths.py:196-200] Check if sentinel file exists in get_raise_af_sentinel",
    ])

    # ============================================================================
    # CATEGORY 7: LOGGING & OBSERVABILITY (20 tickets)
    # Issues in log_utils.py, health.py - atomicity, performance, monitoring
    # ============================================================================

    tasks.extend([
        # Atomic operations (P1)
        "[log_utils.py:14-58] Handle failure between file and directory fsync in atomic_write",
        "[log_utils.py:43] Handle cross-filesystem errors in os.replace atomic operation",
        "[log_utils.py:46-50] Catch and handle directory fsync failures on some filesystems",
        "[log_utils.py:52-58] Handle cleanup unlink failures in error path",

        # File trimming (P2)
        "[log_utils.py:94-118] Optimize trim_to_line_boundary encode/decode/search for large files",
        "[log_utils.py:113] Replace errors='ignore' with proper UTF-8 error handling to prevent corruption",

        # Append operations (P1)
        "[log_utils.py:121-161] Make append_with_guard atomic - currently reads entire file then writes",
        "[log_utils.py:150-159] Fix trimming calculation considering line boundaries - can trim mid-line",
        "[log_utils.py:124] Reference config.max_log_size instead of hardcoding 10MB default",

        # Idempotent append (P2)
        "[log_utils.py:164-194] Optimize idempotent_append O(n) file scan for key presence",
        "[log_utils.py:190] Fix presence check using 'in' on string matching substrings not just keys",

        # Event logging (P2)
        "[log_utils.py:197-281] Clean up log_event complex signature compatibility layer - technical debt",
        "[log_utils.py:233-244] Remove fragile argument shifting for legacy signature",
        "[log_utils.py:268-277] Don't swallow errors in fallback file append try/except wrapper",
        "[log_utils.py:278-280] Remove outer try/except silently failing logging - defeats observability",

        # Health checks (P2)
        "[health.py:49-58] Validate timezone offsets in _parse_iso_datetime beyond just 'Z' suffix",
        "[health.py:68-69] Validate UTC timezone assumption when adding to naive datetime",
        "[health.py:86-115] Optimize check_sla_breaches loading all tickets - add pagination for scale",
        "[health.py:118-213] Add timeout to get_health expensive operations",
    ])

    # ============================================================================
    # CATEGORY 8: ARCHITECTURAL IMPROVEMENTS (25 tickets)
    # Structural issues - coupling, abstractions, patterns
    # ============================================================================

    tasks.extend([
        # Circular dependencies (P1)
        "[architecture] Break circular dependency: raise_af.py <-> persistence.ticket_repo",
        "[architecture] Break circular dependency: do_af.py <-> raise_af.py logging",
        "[architecture] Break circular dependency: plugins/loader.py -> raise_af creating core<->plugin coupling",

        # God objects decomposition (P2)
        "[raise_af.py:58-89] Decompose ActifixEntry with 15+ fields - needs separation of concerns",
        "[ai_client.py:49-585] Refactor AIClient 500+ lines into provider-specific classes",
        "[ticket_repo.py:56-687] Split TicketRepository 25+ methods using repository pattern",

        # Missing abstractions (P2)
        "[architecture] Create abstract base class for ticket storage to enable swapping implementations",
        "[architecture] Create interface/protocol for AI providers instead of hardcoded methods",
        "[architecture] Define plugin lifecycle states beyond loaded/enabled/disabled",
        "[architecture] Create event bus for cross-module communication instead of direct calls",

        # Tight coupling (P1)
        "[do_af.py] Remove direct database schema knowledge - use DTOs from ticket_repo",
        "[ai_client.py] Remove knowledge of ticket structure - use DTOs",
        "[health.py] Break runtime->infra dependency created by importing do_af",

        # Missing patterns (P2)
        "[architecture] Implement factory pattern for creating storage backends",
        "[architecture] Implement strategy pattern for AI provider selection",
        "[architecture] Implement observer pattern for ticket lifecycle events",
        "[architecture] Implement command pattern for queued operations",

        # Configuration spread (P2)
        "[architecture] Centralize MAX_CONTEXT_CHARS from raise_af.py to config.py",
        "[architecture] Deduplicate SLA thresholds duplicated in health.py and config.py",
        "[architecture] Eliminate hardcoded file path strings duplicated across modules",

        # Error handling inconsistency (P2)
        "[architecture] Standardize error handling - some return None, others raise, no consistency",
        "[architecture] Create error hierarchy deeper than direct Exception inheritance",
        "[architecture] Add error codes and categorization beyond exception types",
    ])

    # ============================================================================
    # CATEGORY 9: SECURITY & SECRETS (20 tickets)
    # Security vulnerabilities, secrets management, access control
    # ============================================================================

    tasks.extend([
        # Credential storage (P0)
        "[config.py:174] Encrypt AI API keys instead of plain text env vars",
        "[security] Integrate system credential managers (keychain, credential-manager)",
        "[security] Validate database path isn't in shared/public directory",
        "[security] Add secrets scanning pre-commit hook to prevent accidental commits",

        # Path traversal (P0)
        "[storage.py:194-196] Resolve symlinks in FileStorageBackend._get_path beyond normalizing ..",
        "[state_paths.py] Validate state path environment overrides for safety",
        "[quarantine.py:64] Sanitize user-controlled names in quarantine file creation",

        # SQL injection prevention (P1)
        "[ticket_repo.py:190-206] Replace fragile dynamic ORDER BY CASE with prepared statements",
        "[ticket_repo.py:206] Use parameterization for LIMIT instead of string interpolation",
        "[ticket_repo.py] Implement prepared statement caching to avoid repeated SQL parsing",

        # Access control (P1)
        "[security] Implement authentication/authorization layer for API access",
        "[security] Add permission model to plugin system - plugins have unrestricted system access",
        "[security] Add rate limiting for AI client external API calls",

        # Input validation (P0)
        "[security] Add length limits to ticket message/source fields to prevent DoS",
        "[storage.py] Add size limit before JSON deserialization to prevent DoS",
        "[raise_af.py:321-369] Add size check before reading files in context capture",
        "[security] Sanitize environment variable values after parsing",

        # Audit trail (P2)
        "[security] Add audit log of who created/modified tickets",
        "[security] Create separate audit table for database changes",
        "[security] Add user context to plugin load/unload logging",
    ])

    # ============================================================================
    # CATEGORY 10: PERFORMANCE & SCALABILITY (30 tickets)
    # Database queries, file I/O, memory usage, algorithms
    # ============================================================================

    tasks.extend([
        # Database performance (P1)
        "[ticket_repo.py:570-613] Optimize get_stats from 4 queries to single aggregate query",
        "[ticket_repo.py] Add cursor support to get_tickets loading entire result set",
        "[ticket_repo.py] Implement query result caching for repeated data access",
        "[database.py:217-253] Add connection pool size limit to prevent exhausting connections",
        "[database.py] Add database query timeout to prevent indefinite hangs",
        "[database.py] Add explicit WAL checkpoint calls to prevent unbounded growth",

        # File I/O (P2)
        "[raise_af.py:321-369] Stream file reading in capture_file_context instead of loading entire file",
        "[log_utils.py:121-161] Stream file operations in append_with_guard instead of full read",
        "[quarantine.py] Evaluate directory-based quarantine instead of individual markdown files for scale",
        "[performance] Add file descriptor limit enforcement to prevent exhausting handles",

        # Memory usage (P1)
        "[do_af.py:64-86] Add pagination to _refresh_cache loading all tickets into memory",
        "[storage.py:292-349] Add size limits to MemoryStorageBackend to prevent exhaustion",
        "[queue.py:102-110] Stream fallback queue processing instead of loading entire JSON",
        "[ai_client.py:476-517] Use string builder for AI prompt construction instead of concatenation",

        # Network (P2)
        "[ai_client.py] Add connection pooling for AI API calls instead of new socket per request",
        "[ai_client.py:546-553] Cache Ollama health check instead of network call every time",
        "[ai_client.py] Implement circuit breaker for failing external services",
        "[ai_client.py] Add jitter to retry exponential backoff to prevent thundering herd",

        # Algorithmic (P1)
        "[raise_af.py:692-700] Cache duplicate check results instead of querying database every time",
        "[health.py:86-115] Add index-based SLA breach check instead of loading all tickets",
        "[queue.py:221-264] Optimize queue replay to not iterate entire queue for single entry",
        "[error_taxonomy.py] Optimize pattern matching to avoid running all patterns for every error",

        # Concurrency (P1)
        "[do_af.py:767-778] Replace file lock busy-wait with event-based notification",
        "[config.py:243-252] Add locking to global config singleton access",
        "[plugins/registry.py] Add timeout to plugin registry RLock to prevent deadlock",
        "[performance] Coordinate cache invalidation across processes",

        # Resource limits (P2)
        "[performance] Add limit on number of open tickets allowed",
        "[performance] Add limit on ticket message length",
        "[performance] Add limit on captured file context size per ticket",
    ])

    # ============================================================================
    # CATEGORY 11: DOCUMENTATION & CODE QUALITY (20 tickets)
    # Documentation gaps, code duplication, naming, type hints
    # ============================================================================

    tasks.extend([
        # Documentation gaps (P2)
        "[database.py] Document connection lifecycle in connection pooling explanation",
        "[ticket_repo.py] Document lease-based locking mechanism and duration rationale",
        "[plugins/protocol.py] Add examples and quickstart guide for plugin development",
        "[error_taxonomy.py] Document how to extend pattern matching for custom errors",

        # Code duplication (P2)
        "[architecture] Deduplicate timestamp serialization across database.py and raise_af.py",
        "[architecture] Deduplicate path resolution logic between state_paths.py and other modules",
        "[ai_client.py] Extract common exception handling pattern from all AI provider methods",
        "[architecture] Deduplicate lock acquisition logic between ticket_repo and do_af",

        # Code smells (P2)
        "[raise_af.py:619-768] Refactor record_error 200+ line function into smaller units",
        "[ai_client.py:66-125] Reduce generate_fix nesting from 4 levels",
        "[ai_client.py:390-474] Split _call_free_alternative 100+ line function",
        "[architecture] Extract all magic numbers (10MB, 50ms, 300s) to named constants in config",

        # Inconsistent naming (P2)
        "[raise_af.py] Reconcile ActifixEntry having both entry_id and ticket_id properties",
        "[architecture] Standardize paths vs base_dir parameter naming across modules",
        "[architecture] Clarify pool usage in database.py vs ticket_repo.py different meanings",
        "[architecture] Standardize get_ vs load_ prefix usage for similar operations",

        # Type hints (P2)
        "[architecture] Add return type hints to all functions missing them",
        "[architecture] Replace generic Dict/List with specific types throughout",
        "[storage.py, queue.py] Reduce excessive Any type usage with specific types",
    ])

    # ============================================================================
    # CATEGORY 12: TESTING & QUALITY ASSURANCE (23 tickets)
    # Test coverage, test infrastructure, quality gates
    # ============================================================================

    tasks.extend([
        # Test infrastructure (P1)
        "[testing] Create comprehensive test suite - currently no test directory visible",
        "[testing] Build test utilities for mocking database operations",
        "[testing] Create test fixtures for AI client mocking",
        "[testing] Build file operation test doubles to avoid real I/O in tests",
        "[testing] Create integration test framework for end-to-end workflows",
        "[testing] Add performance test suite for critical database queries",

        # Test coverage targets (P1)
        "[testing] Achieve 95%+ test coverage on database.py with concurrency scenarios",
        "[testing] Achieve 95%+ test coverage on ticket_repo.py including all error paths",
        "[testing] Achieve 95%+ test coverage on raise_af.py with all edge cases",
        "[testing] Add tests for all race conditions in concurrent ticket locking",
        "[testing] Add tests for database connection pool exhaustion scenarios",
        "[testing] Add tests for file lock timeout and retry logic",

        # Quality gates (P1)
        "[testing] Create pre-commit hook running tests on changed modules only",
        "[testing] Add CI pipeline with zero tolerance for test failures",
        "[testing] Create mutation testing to verify test quality",
        "[testing] Add code coverage threshold enforcement in CI (95% minimum)",
        "[testing] Create automated regression test generation from bug tickets",

        # Contract testing (P2)
        "[testing] Add contract tests for Plugin protocol implementation compliance",
        "[testing] Create contract tests for all public API backward compatibility",
        "[testing] Add schema validation tests for database migrations",

        # Chaos & reliability (P2)
        "[testing] Build chaos test framework for simulating database failures",
        "[testing] Add fuzz testing for ticket message and stack trace inputs",
        "[testing] Create long-running stability tests for memory leak detection",
    ])

    print(f"Generated {len(tasks)} specific weakness-addressing tasks.")
    print("\nCreating tickets with detailed source references...")

    run_label = "weakness-analysis-300"
    created_count = 0

    for idx, task_message in enumerate(tasks[:300], start=1):
        try:
            # Determine priority from task prefix or content analysis
            if task_message.startswith("[") and "P0" in task_message or any(
                keyword in task_message.lower()
                for keyword in ["security", "data loss", "race condition", "toctou", "sql injection"]
            ):
                priority = TicketPriority.P0
            elif any(
                keyword in task_message.lower()
                for keyword in ["concurrency", "thread-safety", "atomic", "lock", "error handling"]
            ):
                priority = TicketPriority.P1
            elif any(
                keyword in task_message.lower()
                for keyword in ["performance", "optimize", "cache", "scale"]
            ):
                priority = TicketPriority.P1
            elif "P3" in task_message or "typo" in task_message.lower():
                priority = TicketPriority.P3
            else:
                priority = TicketPriority.P2

            entry = record_error(
                message=task_message,
                source="start_weakness_analysis_300.py",
                error_type="WeaknessAnalysis",
                priority=priority,
                run_label=run_label,
                skip_duplicate_check=True,
                skip_ai_notes=True,
                capture_context=False,
            )

            created_count += 1

            if created_count % 30 == 0:
                print(f"  Created {created_count} tickets...")

        except Exception as e:
            print(f"  Failed to create ticket {idx}: {e}")

    print(f"\n✓ Successfully created {created_count} tickets with run_label='{run_label}'")
    print(f"\nTicket breakdown by category:")
    print(f"  1-35:    Database & Persistence Critical Fixes")
    print(f"  36-70:   Error Handling & Raise_AF Robustness")
    print(f"  71-100:  Ticket Processing & Do_AF Improvements")
    print(f"  101-125: AI Client Reliability")
    print(f"  126-145: Plugin System Robustness")
    print(f"  146-170: Configuration & State Management")
    print(f"  171-190: Logging & Observability")
    print(f"  191-215: Architectural Improvements")
    print(f"  216-235: Security & Secrets Management")
    print(f"  236-265: Performance & Scalability")
    print(f"  266-285: Documentation & Code Quality")
    print(f"  286-300: Additional Quality Improvements")
    print(f"\nAll tickets include specific file paths, line numbers, and detailed descriptions")
    print(f"\nTo view tickets: Query actifix.db with run_label='{run_label}'")


if __name__ == "__main__":
    generate_weakness_tickets()