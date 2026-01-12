#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actifix - Generic Error Tracking and Management Framework

A sophisticated error tracking system with AI integration, context capture,
and self-improvement capabilities. Originally inspired by the pokertool actifix system.

Version: 2.7.5 (Generic)
"""

from .raise_af import (
    record_error,
    ActifixEntry,
    TicketPriority,
    generate_entry_id,
    generate_ticket_id,
    generate_duplicate_guard,
    ensure_scaffold,
    ACTIFIX_CAPTURE_ENV_VAR
)

from .bootstrap import (
    bootstrap_actifix_development,
    enable_actifix_capture,
    disable_actifix_capture,
    capture_exception,
    install_exception_handler,
    uninstall_exception_handler,
    create_initial_ticket,
    track_development_progress
)

from .state_paths import (
    get_actifix_state_dir,
    get_actifix_data_dir,
    get_project_root,
    get_logs_dir
)
from .health import get_health, run_health_check, format_health_report

__version__ = "2.7.10"
__author__ = "Actifix Framework"
__description__ = "Generic Error Tracking and Management Framework with AI Integration"

# Main API
__all__ = [
    # Core error recording
    "record_error",
    "ActifixEntry",
    "TicketPriority",
    
    # Bootstrap and development
    "bootstrap_actifix_development",
    "enable_actifix_capture",
    "disable_actifix_capture",
    "capture_exception",
    "install_exception_handler",
    "uninstall_exception_handler",
    "create_initial_ticket",
    "track_development_progress",
    
    # State management
    "get_actifix_state_dir",
    "get_actifix_data_dir",
    "get_project_root",
    "get_health",
    "run_health_check",
    "format_health_report",
    
    # Utilities
    "generate_entry_id",
    "generate_ticket_id",
    "generate_duplicate_guard",
    "ensure_scaffold",
    
    # Constants
    "ACTIFIX_CAPTURE_ENV_VAR"
]


def quick_start():
    """
    Quick start guide for actifix.
    
    This function provides a simple way to get started with actifix
    for new users.
    """
    print("=== Actifix Quick Start ===")
    print()
    print("1. Enable error capture:")
    print("   import actifix")
    print("   actifix.enable_actifix_capture()")
    print()
    print("2. Record an error:")
    print("   try:")
    print("       # Your code here")
    print("       pass")
    print("   except Exception as e:")
    print("       actifix.record_error(")
    print("           message=str(e),")
    print("           source='your_module.py',")
    print("           run_label='your-application',")
    print("           error_type=type(e).__name__")
    print("       )")
    print()
    print("3. Bootstrap self-development mode:")
    print("   actifix.bootstrap_actifix_development()")
    print()
    print("Check the 'actifix/' directory for generated tickets!")
