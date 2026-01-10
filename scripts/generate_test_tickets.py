#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate 100 comprehensive test tickets for Actifix system validation.

This script creates tickets in 10 categories of 10 tickets each, covering:
- Core module testing
- Entry recording functionality
- Priority classification
- Duplicate prevention
- Context capture
- Secret redaction
- Persistence operations
- Ticket processing
- Health & SLA monitoring
- Integration & regression tests

Each ticket tests a specific aspect of system setup, code quality, and functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import actifix
from actifix import TicketPriority


def generate_test_tickets():
    """Generate all 100 comprehensive test tickets."""
    
    # Enable Actifix capture
    os.environ[actifix.ACTIFIX_CAPTURE_ENV_VAR] = "1"
    
    print("Generating 100 comprehensive test tickets...")
    
    tickets = []
    
    # Category 1: Core Module Tests (T001-T010)
    core_module_tests = [
        ("T001: Test raise_af.py module loading and imports", "raise_af.py", "ModuleLoadTest"),
        ("T002: Test do_af.py module loading and imports", "do_af.py", "ModuleLoadTest"),
        ("T003: Test bootstrap.py module loading and imports", "bootstrap.py", "ModuleLoadTest"),
        ("T004: Test health.py module loading and imports", "health.py", "ModuleLoadTest"),
        ("T005: Test config.py module loading and validation", "config.py", "ConfigValidationTest"),
        ("T006: Test state_paths.py module and path resolution", "state_paths.py", "PathResolutionTest"),
        ("T007: Test log_utils.py atomic operations", "log_utils.py", "AtomicOperationTest"),
        ("T008: Test quarantine.py quarantine functionality", "quarantine.py", "QuarantineTest"),
        ("T009: Test main.py entry point", "main.py", "EntryPointTest"),
        ("T010: Test __init__.py public API exports", "__init__.py", "APIExportTest"),
    ]
    
    for message, source, error_type in core_module_tests:
        tickets.append((message, source, error_type, TicketPriority.P1))
    
    # Category 2: Entry Recording Tests (T011-T020)
    entry_recording_tests = [
        ("T011: Test record_error() creates valid entry", "raise_af.py:record_error", "EntryCreationTest"),
        ("T012: Test generate_entry_id() format (ACT-YYYYMMDD-XXXXX)", "raise_af.py:generate_entry_id", "IDFormatTest"),
        ("T013: Test generate_duplicate_guard() uniqueness", "raise_af.py:generate_duplicate_guard", "DuplicateGuardTest"),
        ("T014: Test entry message capture and storage", "raise_af.py:ActifixEntry.message", "MessageCaptureTest"),
        ("T015: Test entry source capture and storage", "raise_af.py:ActifixEntry.source", "SourceCaptureTest"),
        ("T016: Test entry run_label capture", "raise_af.py:ActifixEntry.run_label", "RunLabelTest"),
        ("T017: Test entry timestamp creation (UTC)", "raise_af.py:ActifixEntry.created_at", "TimestampTest"),
        ("T018: Test entry priority assignment", "raise_af.py:ActifixEntry.priority", "PriorityAssignmentTest"),
        ("T019: Test entry error_type capture", "raise_af.py:ActifixEntry.error_type", "ErrorTypeCaptureTest"),
        ("T020: Test entry correlation_id capture", "raise_af.py:ActifixEntry.correlation_id", "CorrelationIDTest"),
    ]
    
    for message, source, error_type in entry_recording_tests:
        tickets.append((message, source, error_type, TicketPriority.P1))
    
    # Category 3: Priority Classification Tests (T021-T030)
    priority_tests = [
        ("T021: Test P0 auto-classification for 'fatal' errors", "raise_af.py:classify_priority", "P0ClassificationTest"),
        ("T022: Test P0 auto-classification for 'crash' errors", "raise_af.py:classify_priority", "P0ClassificationTest"),
        ("T023: Test P1 auto-classification for 'database' errors", "raise_af.py:classify_priority", "P1ClassificationTest"),
        ("T024: Test P1 auto-classification for 'security' errors", "raise_af.py:classify_priority", "P1ClassificationTest"),
        ("T025: Test P1 auto-classification for core module sources", "raise_af.py:classify_priority", "P1ClassificationTest"),
        ("T026: Test P2 default priority assignment", "raise_af.py:classify_priority", "P2ClassificationTest"),
        ("T027: Test P3 auto-classification for warnings", "raise_af.py:classify_priority", "P3ClassificationTest"),
        ("T028: Test P3 auto-classification for deprecation", "raise_af.py:classify_priority", "P3ClassificationTest"),
        ("T029: Test P4 auto-classification for style issues", "raise_af.py:classify_priority", "P4ClassificationTest"),
        ("T030: Test priority override via parameter", "raise_af.py:classify_priority", "PriorityOverrideTest"),
    ]
    
    for message, source, error_type in priority_tests:
        tickets.append((message, source, error_type, TicketPriority.P2))
    
    # Category 4: Duplicate Prevention Tests (T031-T040)
    duplicate_tests = [
        ("T031: Test duplicate guard generation consistency", "raise_af.py:generate_duplicate_guard", "DuplicateGuardConsistencyTest"),
        ("T032: Test duplicate detection in Active Items", "raise_af.py:check_duplicate_guard", "ActiveDuplicateTest"),
        ("T033: Test duplicate detection in Completed Items", "raise_af.py:get_completed_guards", "CompletedDuplicateTest"),
        ("T034: Test normalized message deduplication", "raise_af.py:generate_duplicate_guard", "MessageNormalizationTest"),
        ("T035: Test path normalization in guards", "raise_af.py:generate_duplicate_guard", "PathNormalizationTest"),
        ("T036: Test hash-based guard suffix", "raise_af.py:generate_duplicate_guard", "HashSuffixTest"),
        ("T037: Test different sources create different guards", "raise_af.py:generate_duplicate_guard", "SourceDifferentiationTest"),
        ("T038: Test skip_duplicate_check parameter", "raise_af.py:record_error", "SkipDuplicateTest"),
        ("T039: Test loop prevention for already-fixed issues", "raise_af.py:record_error", "LoopPreventionTest"),
        ("T040: Test guard format compliance", "raise_af.py:generate_duplicate_guard", "GuardFormatTest"),
    ]
    
    for message, source, error_type in duplicate_tests:
        tickets.append((message, source, error_type, TicketPriority.P2))
    
    # Category 5: Context Capture Tests (T041-T050)
    context_tests = [
        ("T041: Test stack trace capture", "raise_af.py:capture_stack_trace", "StackTraceTest"),
        ("T042: Test file context capture around error line", "raise_af.py:capture_file_context", "FileContextTest"),
        ("T043: Test system state capture (cwd, python version)", "raise_af.py:capture_system_state", "SystemStateTest"),
        ("T044: Test git branch capture", "raise_af.py:capture_system_state", "GitBranchTest"),
        ("T045: Test git commit capture", "raise_af.py:capture_system_state", "GitCommitTest"),
        ("T046: Test environment variable capture (ACTIFIX_*)", "raise_af.py:capture_system_state", "EnvVarTest"),
        ("T047: Test AI remediation notes generation", "raise_af.py:generate_ai_remediation_notes", "AINotesTest"),
        ("T048: Test context truncation for max size", "raise_af.py:generate_ai_remediation_notes", "ContextTruncationTest"),
        ("T049: Test secret redaction in context", "raise_af.py:redact_secrets_from_text", "ContextSecretRedactionTest"),
        ("T050: Test capture_context=False disables context", "raise_af.py:record_error", "DisableContextTest"),
    ]
    
    for message, source, error_type in context_tests:
        tickets.append((message, source, error_type, TicketPriority.P2))
    
    # Category 6: Secret Redaction Tests (T051-T060)
    redaction_tests = [
        ("T051: Test API key redaction (sk-xxx pattern)", "raise_af.py:redact_secrets_from_text", "APIKeyRedactionTest"),
        ("T052: Test Bearer token redaction", "raise_af.py:redact_secrets_from_text", "BearerTokenRedactionTest"),
        ("T053: Test AWS credentials redaction", "raise_af.py:redact_secrets_from_text", "AWSCredentialsRedactionTest"),
        ("T054: Test password in URL redaction", "raise_af.py:redact_secrets_from_text", "URLPasswordRedactionTest"),
        ("T055: Test password field redaction", "raise_af.py:redact_secrets_from_text", "PasswordFieldRedactionTest"),
        ("T056: Test private key redaction", "raise_af.py:redact_secrets_from_text", "PrivateKeyRedactionTest"),
        ("T057: Test email partial redaction", "raise_af.py:redact_secrets_from_text", "EmailRedactionTest"),
        ("T058: Test credit card number redaction", "raise_af.py:redact_secrets_from_text", "CreditCardRedactionTest"),
        ("T059: Test SSN-like pattern redaction", "raise_af.py:redact_secrets_from_text", "SSNRedactionTest"),
        ("T060: Test generic token redaction", "raise_af.py:redact_secrets_from_text", "GenericTokenRedactionTest"),
    ]
    
    for message, source, error_type in redaction_tests:
        tickets.append((message, source, error_type, TicketPriority.P3))
    
    # Category 7: Persistence Tests (T061-T070)
    persistence_tests = [
        ("T061: Test FileStorageBackend read/write", "persistence/storage.py:FileStorageBackend", "FileStorageTest"),
        ("T062: Test FileStorageBackend delete operation", "persistence/storage.py:FileStorageBackend.delete", "FileDeleteTest"),
        ("T063: Test FileStorageBackend list_keys", "persistence/storage.py:FileStorageBackend.list_keys", "FileListKeysTest"),
        ("T064: Test MemoryStorageBackend read/write", "persistence/storage.py:MemoryStorageBackend", "MemoryStorageTest"),
        ("T065: Test MemoryStorageBackend clear operation", "persistence/storage.py:MemoryStorageBackend.clear", "MemoryClearTest"),
        ("T066: Test PersistenceQueue enqueue/dequeue", "persistence/queue.py:PersistenceQueue", "QueueOperationsTest"),
        ("T067: Test PersistenceQueue replay with handler", "persistence/queue.py:PersistenceQueue.replay", "QueueReplayTest"),
        ("T068: Test atomic_write file integrity", "persistence/atomic.py:atomic_write", "AtomicWriteTest"),
        ("T069: Test fallback queue when list unwritable", "raise_af.py:_queue_to_fallback", "FallbackQueueTest"),
        ("T070: Test replay_fallback_queue recovery", "raise_af.py:replay_fallback_queue", "FallbackReplayTest"),
    ]
    
    for message, source, error_type in persistence_tests:
        tickets.append((message, source, error_type, TicketPriority.P1))
    
    # Category 8: Ticket Processing Tests (T071-T080)
    processing_tests = [
        ("T071: Test parse_ticket_block extracts all fields", "do_af.py:parse_ticket_block", "TicketParsingTest"),
        ("T072: Test get_open_tickets returns sorted by priority", "do_af.py:get_open_tickets", "OpenTicketsSortTest"),
        ("T073: Test mark_ticket_complete updates checklist", "do_af.py:mark_ticket_complete", "MarkCompleteTest"),
        ("T074: Test mark_ticket_complete moves to Completed", "do_af.py:mark_ticket_complete", "MoveToCompletedTest"),
        ("T075: Test process_next_ticket selects highest priority", "do_af.py:process_next_ticket", "NextTicketSelectionTest"),
        ("T076: Test process_tickets batch processing", "do_af.py:process_tickets", "BatchProcessingTest"),
        ("T077: Test get_ticket_stats accuracy", "do_af.py:get_ticket_stats", "TicketStatsTest"),
        ("T078: Test AI handler callback invocation", "do_af.py:process_next_ticket", "AIHandlerTest"),
        ("T079: Test ticket block format compliance", "do_af.py:parse_ticket_block", "BlockFormatTest"),
        ("T080: Test checklist state detection", "do_af.py:TicketInfo", "ChecklistStateTest"),
    ]
    
    for message, source, error_type in processing_tests:
        tickets.append((message, source, error_type, TicketPriority.P1))
    
    # Category 9: Health & SLA Tests (T081-T090)
    health_tests = [
        ("T081: Test health check file existence validation", "health.py:get_health", "HealthFileExistenceTest"),
        ("T082: Test health check writability validation", "health.py:get_health", "HealthWritabilityTest"),
        ("T083: Test SLA P0 breach detection (1h)", "health.py:check_sla_breaches", "SLAP0BreachTest"),
        ("T084: Test SLA P1 breach detection (4h)", "health.py:check_sla_breaches", "SLAP1BreachTest"),
        ("T085: Test SLA P2 breach detection (24h)", "health.py:check_sla_breaches", "SLAP2BreachTest"),
        ("T086: Test SLA P3 breach detection (72h)", "health.py:check_sla_breaches", "SLAP3BreachTest"),
        ("T087: Test high ticket count warning (>20)", "health.py:get_health", "HighTicketCountTest"),
        ("T088: Test health report formatting", "health.py:format_health_report", "HealthReportFormatTest"),
        ("T089: Test health status states (OK, WARNING, ERROR, SLA_BREACH)", "health.py:get_health", "HealthStatusTest"),
        ("T090: Test oldest ticket age calculation", "health.py:get_health", "OldestTicketAgeTest"),
    ]
    
    for message, source, error_type in health_tests:
        tickets.append((message, source, error_type, TicketPriority.P2))
    
    # Category 10: Integration & Regression Tests (T091-T100)
    integration_tests = [
        ("T091: Test full ticket lifecycle (create → process → complete)", "integration_test.py", "TicketLifecycleTest"),
        ("T092: Test bootstrap_actifix_development workflow", "bootstrap.py:bootstrap_actifix_development", "BootstrapWorkflowTest"),
        ("T093: Test enable/disable capture toggle", "bootstrap.py:enable_actifix_capture", "CaptureToggleTest"),
        ("T094: Test exception handler installation", "bootstrap.py:install_exception_handler", "ExceptionHandlerTest"),
        ("T095: Test scaffold creation (all 4 files)", "raise_af.py:ensure_scaffold", "ScaffoldCreationTest"),
        ("T096: Test ACTIFIX-LIST.md format compliance", "raise_af.py:_append_ticket_impl", "ListFormatTest"),
        ("T097: Test ACTIFIX.md rollup (last 20 entries)", "raise_af.py:_append_recent", "RollupTest"),
        ("T098: Test AFLog.txt audit logging", "log_utils.py:log_event", "AuditLoggingTest"),
        ("T099: Test public API consistency (__all__ exports)", "__init__.py", "APIConsistencyTest"),
        ("T100: Test version number presence and format", "__init__.py:__version__", "VersionFormatTest"),
    ]
    
    for message, source, error_type in integration_tests:
        tickets.append((message, source, error_type, TicketPriority.P0))
    
    # Record all tickets
    print(f"\nRecording {len(tickets)} tickets...")
    
    for i, (message, source, error_type, priority) in enumerate(tickets, 1):
        try:
            entry = actifix.record_error(
                message=message,
                source=source,
                run_label="comprehensive-test-suite",
                error_type=error_type,
                priority=priority,
                capture_context=False,  # Skip for performance
                skip_ai_notes=True,     # Skip for performance
            )
            
            if entry:
                print(f"  [{i:03d}/100] Created {entry.entry_id}: {message[:60]}...")
            else:
                print(f"  [{i:03d}/100] SKIPPED (duplicate): {message[:60]}...")
                
        except Exception as e:
            print(f"  [{i:03d}/100] ERROR: {e}")
    
    print(f"\n✅ Ticket generation complete!")
    print(f"Check actifix/ACTIFIX-LIST.md for all tickets.")
    
    return len(tickets)


def main():
    """Main entry point."""
    try:
        count = generate_test_tickets()
        print(f"\n🎯 Generated {count} comprehensive test tickets for Actifix validation")
        
    except Exception as e:
        print(f"\n❌ Error generating tickets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
