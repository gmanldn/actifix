#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actifix - Generic Error Tracking and Management Framework

A sophisticated error tracking system with AI integration...
"""

from .bootstrap import (
    bootstrap_actifix_development,
    enable_actifix_capture,
    disable_actifix_capture,
    capture_exception,
    install_exception_handler,
    uninstall_exception_handler,
    create_initial_ticket,
    track_development_progress,
)

from .raise_af import (
    record_error,
    ActifixEntry,
    TicketPriority,
    generate_entry_id,
    generate_ticket_id,
    generate_duplicate_guard,
    ensure_scaffold,
    ACTIFIX_CAPTURE_ENV_VAR,
)

from .state_paths import (
    get_actifix_state_dir,
    get_actifix_data_dir,
    get_project_root,
    get_logs_dir,
)
from .health import get_health, run_health_check, format_health_report
from .persistence.ticket_cleanup import run_automatic_cleanup, apply_retention_policy, cleanup_test_tickets
from .persistence.cleanup_config import CleanupConfig, get_cleanup_config

__version__ = "4.0.12"
__author__ = "Actifix Framework"
__description__ = "Generic Error Tracking and Management Framework with AI Integration"


def quick_start() -> None:
    """Print a quick-start guide for the core API."""
    print("Actifix Quick Start")
    print("1) enable_actifix_capture()")
    print("2) record_error(message, source, run_label, error_type, priority=None)")


__all__ = [
    "record_error",
    "ActifixEntry",
    "TicketPriority",
    "bootstrap_actifix_development",
    "enable_actifix_capture",
    "disable_actifix_capture",
    "capture_exception",
    "install_exception_handler",
    "uninstall_exception_handler",
    "create_initial_ticket",
    "track_development_progress",
    "get_actifix_state_dir",
    "get_actifix_data_dir",
    "get_project_root",
    "get_logs_dir",
    "get_health",
    "run_health_check",
    "format_health_report",
    "generate_entry_id",
    "generate_ticket_id",
    "generate_duplicate_guard",
    "ensure_scaffold",
    "ACTIFIX_CAPTURE_ENV_VAR",
    "quick_start",
    "run_automatic_cleanup",
    "apply_retention_policy",
    "cleanup_test_tickets",
    "CleanupConfig",
    "get_cleanup_config",
]
