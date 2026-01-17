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

__version__ = "3.2.0"
__author__ = "Actifix Framework"
__description__ = "Generic Error Tracking and Management Framework with AI Integration"

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
]
