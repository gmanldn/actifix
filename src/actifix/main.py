"""
Actifix Main - Single canonical entrypoint for the system.

This is the entrypoint that should be used to run Actifix.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .bootstrap import bootstrap, shutdown, ActifixContext
from .config import load_config
from .health import run_health_check
from .raise_af import record_error, enforce_raise_af_only, TicketPriority
from .do_af import process_tickets, get_ticket_stats
from .quarantine import list_quarantine, get_quarantine_count
from .testing import TestRunner


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize Actifix in the current project."""
    from .state_paths import init_actifix_files, get_actifix_paths
    
    project_root = Path(args.project_root or Path.cwd())
    paths = get_actifix_paths(project_root=project_root)
    enforce_raise_af_only(paths)
    print(f"Initializing Actifix in {project_root}...")
    init_actifix_files(paths)
    
    print(f"✓ Created {paths.base_dir}")
    print(f"✓ Created {paths.state_dir}")
    print(f"✓ Created {paths.logs_dir}")
    print(f"\nActifix initialized successfully!")
    
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    """Run health check."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        health = run_health_check(print_report=True)
        return 0 if health.healthy else 1


def cmd_record(args: argparse.Namespace) -> int:
    """Record an error manually."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        entry = record_error(
            error_type=args.error_type,
            message=args.message,
            source=args.source,
            priority=args.priority,
        )
        
        if entry:
            print(f"✓ Created ticket: {entry.ticket_id}")
            return 0
        else:
            print("✗ Ticket not created (duplicate or disabled)")
            return 1


def cmd_process(args: argparse.Namespace) -> int:
    """Process pending tickets."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        processed = process_tickets(max_tickets=args.max_tickets)
        
        if processed:
            print(f"✓ Processed {len(processed)} ticket(s)")
            for ticket in processed:
                print(f"  - {ticket.ticket_id}: {ticket.error_type}")
        else:
            print("No tickets to process")
        
        return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show ticket statistics."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        stats = get_ticket_stats()
        
        print("=== Actifix Statistics ===")
        print(f"Total Tickets: {stats['total']}")
        print(f"Open: {stats['open']}")
        print(f"Completed: {stats['completed']}")
        print(f"\nBy Priority:")
        for priority, count in stats['by_priority'].items():
            print(f"  {priority}: {count}")
        
        return 0


def cmd_quarantine(args: argparse.Namespace) -> int:
    """Manage quarantine."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        if args.quarantine_action == "list":
            entries = list_quarantine()
            
            if entries:
                print(f"=== Quarantined Items ({len(entries)}) ===")
                for entry in entries:
                    print(f"\n{entry.entry_id}")
                    print(f"  Source: {entry.original_source}")
                    print(f"  Reason: {entry.reason}")
                    print(f"  Date: {entry.quarantined_at.isoformat()}")
            else:
                print("No quarantined items")
        
        return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run Actifix self-tests."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        # Run basic integration test
        from .testing import run_tests
        from .state_paths import get_actifix_paths
        from .log_utils import atomic_write
        import tempfile
        
        def test_basic() -> None:
            paths = get_actifix_paths()
            assert paths.base_dir.exists()

        def test_record() -> None:
            entry = record_error("TestError", "test", "test/test_runner.py:1", "P3")
            assert entry is not None
        
        result = run_tests(
            "actifix-self-test",
            [
                ("test_basic", test_basic),
                ("test_record", test_record),
            ]
        )
        
        return 0 if result.success else 1


def _normalize_module_id(module_id: str) -> str:
    if "." in module_id:
        return module_id
    return f"modules.{module_id}"


def cmd_modules(args: argparse.Namespace) -> int:
    """List or toggle module status."""
    from .state_paths import get_actifix_paths
    from .api import (
        _load_modules,
        _read_module_status_payload,
        _write_module_status_payload,
        _normalize_module_statuses,
        MODULE_STATUS_SCHEMA_VERSION,
    )

    project_root = Path(args.project_root or Path.cwd())
    paths = get_actifix_paths(project_root=project_root)
    enforce_raise_af_only(paths)
    status_file = paths.state_dir / "module_statuses.json"

    try:
        if args.modules_action == "list":
            modules = _load_modules(project_root)
            print("=== System Modules ===")
            for module in modules.get("system", []):
                print(f"{module['name']}: {module['status']}")
            print("\n=== User Modules ===")
            for module in modules.get("user", []):
                print(f"{module['name']}: {module['status']}")
            return 0

        if not args.module_id:
            raise ValueError("module_id is required for enable/disable actions")
        module_id = _normalize_module_id(args.module_id)
        status_payload = _read_module_status_payload(status_file)
        statuses = status_payload["statuses"]
        action = args.modules_action

        for key in list(statuses.keys()):
            if module_id in statuses[key]:
                statuses[key].remove(module_id)

        if action == "enable":
            statuses["active"].append(module_id)
        elif action == "disable":
            statuses["disabled"].append(module_id)

        status_payload["statuses"] = _normalize_module_statuses(statuses)
        status_payload["schema_version"] = MODULE_STATUS_SCHEMA_VERSION
        _write_module_status_payload(status_file, status_payload)
        print(f"{module_id}: {action}d")
        return 0
    except Exception as exc:
        record_error(
            message=f"Module CLI failed ({args.modules_action}): {exc}",
            source="main.py:cmd_modules",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entrypoint for Actifix CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv).
    
    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="actifix",
        description="Actifix - Automated Error Tracking and Remediation",
    )
    
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory (default: current directory)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize Actifix")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Run health check")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record an error")
    record_parser.add_argument("error_type", help="Error type")
    record_parser.add_argument("message", help="Error message")
    record_parser.add_argument("source", help="Source location (file:line)")
    record_parser.add_argument(
        "--priority",
        default="P2",
        choices=["P0", "P1", "P2", "P3"],
        help="Priority level (default: P2)",
    )
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process pending tickets")
    process_parser.add_argument(
        "--max-tickets",
        type=int,
        default=5,
        help="Maximum tickets to process (default: 5)",
    )
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show ticket statistics")
    
    # Quarantine command
    quarantine_parser = subparsers.add_parser("quarantine", help="Manage quarantine")
    quarantine_parser.add_argument(
        "quarantine_action",
        choices=["list"],
        help="Quarantine action",
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run self-tests")

    # Modules command
    modules_parser = subparsers.add_parser("modules", help="Manage module status")
    modules_parser.add_argument(
        "modules_action",
        choices=["list", "enable", "disable"],
        help="Module action",
    )
    modules_parser.add_argument(
        "module_id",
        nargs="?",
        help="Module identifier (e.g., modules.yhatzee)",
    )
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command
    commands = {
        "init": cmd_init,
        "health": cmd_health,
        "record": cmd_record,
        "process": cmd_process,
        "stats": cmd_stats,
        "quarantine": cmd_quarantine,
        "test": cmd_test,
        "modules": cmd_modules,
    }
    
    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
