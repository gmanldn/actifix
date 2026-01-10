"""
Actifix - Automated Error Tracking and Remediation System

A generic, project-agnostic system for:
- Recording errors and creating tickets (RaiseAF)
- Dispatching tickets to AI for automated fixes (DoAF)
- Tracking ticket lifecycle (Pending → In-Progress → Completed)
- Health monitoring and SLA tracking
- Bootstrap and configuration management
- Testing framework with plan verification
- Quarantine system for corrupted data

Usage:
    from actifix import bootstrap, record_error, process_tickets, get_health
    
    # Bootstrap the system (required)
    bootstrap()
    
    # Record an error
    record_error(
        error_type="RuntimeError",
        message="Something went wrong",
        source="my_module.py:42",
        priority="P2"
    )
    
    # Process pending tickets
    process_tickets(max_tickets=5)
    
    # Check system health
    health = get_health()
"""

__version__ = "1.0.0"
__author__ = "Actifix Team"

# Core functionality
from .raise_af import record_error, record_exception, ActifixEntry, PRIORITY_P0, PRIORITY_P1, PRIORITY_P2, PRIORITY_P3
from .do_af import process_tickets, process_next_ticket, get_open_tickets, mark_ticket_complete, TicketInfo
from .health import get_health, run_health_check, ActifixHealthCheck, check_sla_breaches

# Bootstrap and configuration
from .bootstrap import bootstrap, shutdown, get_state, require_bootstrap, ActifixContext, get_correlation_id, get_run_id
from .config import load_config, get_config, ActifixConfig

# Paths and utilities
from .state_paths import get_actifix_paths, init_actifix_files, ActifixPaths

# Testing framework
from .testing import TestRunner, run_tests, assert_equals, assert_true, assert_false, assert_raises, assert_contains

# Quarantine system
from .quarantine import quarantine_content, quarantine_file, list_quarantine, repair_list_file, QuarantineEntry

__all__ = [
    # Error recording
    "record_error",
    "record_exception",
    "ActifixEntry",
    "PRIORITY_P0",
    "PRIORITY_P1",
    "PRIORITY_P2",
    "PRIORITY_P3",
    
    # Ticket dispatch
    "process_tickets",
    "process_next_ticket",
    "get_open_tickets",
    "mark_ticket_complete",
    "TicketInfo",
    
    # Health
    "get_health",
    "run_health_check",
    "ActifixHealthCheck",
    "check_sla_breaches",
    
    # Bootstrap
    "bootstrap",
    "shutdown",
    "get_state",
    "require_bootstrap",
    "ActifixContext",
    "get_correlation_id",
    "get_run_id",
    
    # Config
    "load_config",
    "get_config",
    "ActifixConfig",
    
    # Paths
    "get_actifix_paths",
    "init_actifix_files",
    "ActifixPaths",
    
    # Testing
    "TestRunner",
    "run_tests",
    "assert_equals",
    "assert_true",
    "assert_false",
    "assert_raises",
    "assert_contains",
    
    # Quarantine
    "quarantine_content",
    "quarantine_file",
    "list_quarantine",
    "repair_list_file",
    "QuarantineEntry",
]
