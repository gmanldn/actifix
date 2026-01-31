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
import os


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


def cmd_status(args: argparse.Namespace) -> int:
    """Show concise runtime summary."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        from datetime import datetime, timezone

        # Get ticket stats
        stats = get_ticket_stats()

        # Get health summary
        health = run_health_check(print_report=False)

        print("=== Actifix Runtime Status ===")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print(f"Health: {'OK' if health.healthy else 'DEGRADED'}")
        print()

        print("--- Tickets ---")
        print(f"Open: {stats.get('open', 0)}")
        print(f"Completed: {stats.get('completed', 0)}")
        print(f"In Progress: {stats.get('in_progress', 0)}")

        if health.sla_breaches and health.sla_breaches > 0:
            print(f"\n⚠ SLA Breaches: {health.sla_breaches}")

        print("\n--- By Priority ---")
        by_priority = stats.get('by_priority', {})
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = by_priority.get(priority, 0)
            if count > 0:
                print(f"{priority}: {count}")

        return 0 if health.healthy else 1


def cmd_metrics(args: argparse.Namespace) -> int:
    """Show quick operational metrics."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        from datetime import datetime, timezone

        # Get ticket stats
        stats = get_ticket_stats()

        # Get health
        health = run_health_check(print_report=False)

        print("=== Actifix Operational Metrics ===")
        print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        print()

        # Ticket metrics
        total = stats.get('total', 0)
        open_count = stats.get('open', 0)
        completed = stats.get('completed', 0)
        in_progress = stats.get('in_progress', 0)

        print("--- Ticket Metrics ---")
        print(f"Total Tickets: {total}")
        print(f"Open: {open_count} ({100 * open_count / total:.1f}%)" if total > 0 else "Open: 0")
        print(f"Completed: {completed} ({100 * completed / total:.1f}%)" if total > 0 else "Completed: 0")
        print(f"In Progress: {in_progress}")

        # Priority distribution
        print("\n--- Priority Distribution ---")
        by_priority = stats.get('by_priority', {})
        for priority in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = by_priority.get(priority, 0)
            pct = (100 * count / total) if total > 0 else 0
            print(f"{priority}: {count} ({pct:.1f}%)")

        # Health metrics
        print("\n--- Health Metrics ---")
        print(f"System Health: {'OK' if health.healthy else 'DEGRADED'}")
        print(f"SLA Breaches: {health.sla_breaches or 0}")

        if hasattr(health, 'oldest_ticket_age_hours') and health.oldest_ticket_age_hours:
            print(f"Oldest Ticket Age: {health.oldest_ticket_age_hours:.1f}h")

        return 0


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


def cmd_diagnostics(args: argparse.Namespace) -> int:
    """Export diagnostics bundle for support."""
    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        from .diagnostics import export_diagnostics_bundle, print_diagnostics_summary

        if args.diagnostics_action == "summary":
            print_diagnostics_summary()
            return 0

        elif args.diagnostics_action == "export":
            output_path = None
            if args.output:
                output_path = Path(args.output)

            bundle_path = export_diagnostics_bundle(
                output_path=output_path,
                include_logs=not args.no_logs,
                include_tickets=not args.no_tickets,
            )

            print(f"✓ Diagnostics bundle exported to: {bundle_path}")
            print(f"  Size: {bundle_path.stat().st_size} bytes")
            return 0

        return 1


def cmd_logs(args: argparse.Namespace) -> int:
    """View recent Actifix event logs."""
    from .persistence.event_repo import EventRepository, EventFilter

    with ActifixContext(project_root=Path(args.project_root or Path.cwd())):
        try:
            if args.logs_action != "tail":
                raise ValueError("logs_action is required (e.g., 'tail')")

            filter = EventFilter(
                event_type=args.event_type,
                ticket_id=args.ticket_id,
                correlation_id=args.correlation_id,
                level=args.level,
                source=args.source,
                limit=args.limit,
            )
            repo = EventRepository()
            events = repo.get_events(filter)
            if not events:
                print("No events found.")
                return 0

            print("=== Recent Event Log Entries ===")
            for event in reversed(events):
                timestamp = event.get("timestamp", "n/a")
                level = event.get("level", "INFO")
                event_type = event.get("event_type", "unknown")
                message = event.get("message", "")
                source = event.get("source", "")
                ticket_id = event.get("ticket_id", "")
                print(
                    f"{timestamp} [{level}] {event_type} {message}"
                    f"{' | source=' + source if source else ''}"
                    f"{' | ticket=' + ticket_id if ticket_id else ''}"
                )
            return 0
        except Exception as exc:
            record_error(
                message=f"Logs tail failed: {exc}",
                source="actifix/main.py:cmd_logs",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            print("Failed to read logs. See Actifix tickets.")
            return 1


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


def cmd_config(args: argparse.Namespace) -> int:
    """Inspect configuration."""
    from dataclasses import fields
    from .config import ActifixConfig
    from .state_paths import get_actifix_paths

    project_root = Path(args.project_root or Path.cwd())
    paths = get_actifix_paths(project_root=project_root)

    if args.config_action != "diff":
        raise ValueError("config_action is required (e.g., 'diff')")

    default_config = ActifixConfig(project_root=project_root, paths=paths)
    active_config = load_config(project_root=project_root, fail_fast=False)

    def _redact(field_name: str, value: object) -> object:
        lowered = field_name.lower()
        if any(marker in lowered for marker in ("key", "token", "secret", "password")):
            if value:
                return "***redacted***"
        return value

    def _normalize(value: object) -> object:
        if isinstance(value, Path):
            return str(value)
        return value

    diffs = []
    for field in fields(ActifixConfig):
        if field.name in {"project_root", "paths"}:
            continue
        default_value = _normalize(getattr(default_config, field.name))
        active_value = _normalize(getattr(active_config, field.name))
        if default_value != active_value:
            diffs.append(
                (
                    field.name,
                    _redact(field.name, default_value),
                    _redact(field.name, active_value),
                )
            )

    if not diffs:
        print("No config overrides detected.")
        return 0

    print("=== Config Overrides (current vs defaults) ===")
    for name, default_value, active_value in diffs:
        print(f"{name}: default={default_value} current={active_value}")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    """Manage persistence queues."""
    import json
    from .raise_af import replay_fallback_queue, LEGACY_FALLBACK_QUEUE
    from .state_paths import get_actifix_paths, init_actifix_files

    project_root = Path(args.project_root or Path.cwd())
    paths = get_actifix_paths(project_root=project_root)
    init_actifix_files(paths)

    if args.queue_action != "replay":
        raise ValueError("queue_action is required (e.g., 'replay')")

    queue_file = paths.fallback_queue_file
    legacy_file = paths.base_dir / LEGACY_FALLBACK_QUEUE

    def _count_entries(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            content = path.read_text(encoding="utf-8").strip() or "[]"
            data = json.loads(content)
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    before = _count_entries(queue_file) or _count_entries(legacy_file)
    if before == 0:
        print("No fallback queue entries to replay.")
        return 0

    print(f"Replaying fallback queue entries: {before}")
    replayed = replay_fallback_queue(base_dir=paths.base_dir)
    after = _count_entries(queue_file) or _count_entries(legacy_file)
    print(f"Replayed: {replayed} | Remaining: {after}")
    return 0


def cmd_tickets(args: argparse.Namespace) -> int:
    """Manage tickets."""
    from .persistence.ticket_cleanup import cleanup_duplicate_tickets
    from .persistence.ticket_repo import get_ticket_repository

    project_root = Path(args.project_root or Path.cwd())
    with ActifixContext(project_root=project_root):
        if args.tickets_action != "cleanup":
            raise ValueError("tickets_action is required (e.g., 'cleanup')")

        repo = get_ticket_repository()
        dry_run = not bool(args.execute)
        results = cleanup_duplicate_tickets(
            repo,
            min_age_hours=float(args.min_age_hours),
            dry_run=dry_run,
        )

        print("=== Duplicate Ticket Cleanup ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        print(f"Duplicate groups: {results.get('duplicate_groups', 0)}")
        print(f"Duplicates found: {results.get('duplicates_found', 0)}")
        print(f"Duplicates closed: {results.get('duplicates_closed', 0)}")
        print(f"Skipped locked: {results.get('duplicates_skipped_locked', 0)}")
        print(f"Skipped recent: {results.get('duplicates_skipped_recent', 0)}")
        return 0


def _normalize_module_id(module_id: str) -> str:
    if "." in module_id:
        return module_id
    return f"modules.{module_id}"


def cmd_modules(args: argparse.Namespace) -> int:
    """List or toggle module status."""
    from .state_paths import get_actifix_paths
    from .state_paths import init_actifix_files
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
        if args.modules_action == "graph":
            import json
            depgraph_path = project_root / "docs" / "architecture" / "DEPGRAPH.json"
            if not depgraph_path.exists():
                print(f"Error: DEPGRAPH.json not found at {depgraph_path}")
                return 1

            with open(depgraph_path) as f:
                depgraph = json.load(f)

            # Filter to modules domain only
            module_nodes = {
                n["id"]: n for n in depgraph.get("nodes", [])
                if n.get("domain") == "modules"
            }
            module_edges = [
                e for e in depgraph.get("edges", [])
                if e.get("from") in module_nodes and e.get("to") in module_nodes
            ]

            print("=== Module Dependency Graph ===")
            print(f"Nodes: {len(module_nodes)}")
            print(f"Edges: {len(module_edges)}\n")

            # Build dependency map
            deps_map = {}
            for edge in module_edges:
                from_id = edge["from"]
                to_id = edge["to"]
                if from_id not in deps_map:
                    deps_map[from_id] = []
                deps_map[from_id].append(to_id)

            # Print each module and its dependencies
            for node_id in sorted(module_nodes.keys()):
                node = module_nodes[node_id]
                label = node.get("label", node_id)
                print(f"\n{node_id} ({label})")
                if node_id in deps_map:
                    print("  depends on:")
                    for dep in sorted(deps_map[node_id]):
                        dep_label = module_nodes.get(dep, {}).get("label", dep)
                        print(f"    - {dep} ({dep_label})")
                else:
                    print("  (no dependencies on other modules)")

            return 0
        if args.modules_action == "validate":
            from .modules.registry import (
                _discover_module_nodes,
                _lazy_import_module,
                validate_module_package,
            )

            nodes = _discover_module_nodes(project_root)
            failures = 0
            print("=== Module Metadata Validation ===")
            for node in nodes:
                module_id = node.get("id")
                if not module_id or not module_id.startswith("modules."):
                    continue
                module_label = module_id.split(".", 1)[1]
                try:
                    module_path, module, metadata = _lazy_import_module(module_label)
                except Exception as exc:
                    failures += 1
                    record_error(
                        message=f"Failed to import module {module_id}: {exc}",
                        source="actifix/main.py:cmd_modules",
                        error_type=type(exc).__name__,
                        priority=TicketPriority.P2,
                    )
                    print(f"{module_id}: import_failed ({exc})")
                    continue

                errors = validate_module_package(module_label, module, metadata)
                if errors:
                    failures += 1
                    record_error(
                        message=f"Module {module_id} metadata validation failed: {errors}",
                        source="actifix/main.py:cmd_modules",
                        error_type="ModuleMetadataError",
                        priority=TicketPriority.P2,
                    )
                    print(f"{module_id}: FAIL -> {', '.join(errors)}")
                else:
                    print(f"{module_id}: OK")
            return 0 if failures == 0 else 1

        action = args.modules_action

        if action == "create":
            if not args.module_id:
                raise ValueError("module_id is required for create action")
            from .modules.scaffold import create_module_scaffold

            init_actifix_files(paths)
            result = create_module_scaffold(
                args.module_id,
                project_root=project_root,
                host=args.host or "127.0.0.1",
                port=int(args.port) if args.port else 8100,
                force=bool(args.force),
            )
            print(
                "Created module scaffold:\n"
                f"- module: {result['module_key']}\n"
                f"- module file: {result['module_file']}\n"
                f"- test file: {result['test_file']}\n"
                "Reminder: add the module to docs/architecture/MAP.yaml and "
                "docs/architecture/DEPGRAPH.json before committing module changes."
            )
            return 0

        if not args.module_id:
            raise ValueError("module_id is required for enable/disable actions")
        module_id = _normalize_module_id(args.module_id)
        status_payload = _read_module_status_payload(status_file)
        statuses = status_payload["statuses"]

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


def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnose Actifix environment and configuration.

    This command checks that essential configuration variables are set, verifies that
    the Actifix configuration can be loaded, runs a health check, and reports
    basic ticket statistics. It returns 0 if all diagnostics pass or 1 if any
    issues are detected.
    """
    project_root = Path(args.project_root or Path.cwd())
    ok = True
    # Use ActifixContext to ensure environment setup and logging
    with ActifixContext(project_root=project_root):
        # Verify ACTIFIX_CHANGE_ORIGIN is correctly set
        change_origin = os.environ.get("ACTIFIX_CHANGE_ORIGIN")
        if change_origin != "raise_af":
            print("✗ ACTIFIX_CHANGE_ORIGIN is not set to 'raise_af'.")
            print("  Please run: export ACTIFIX_CHANGE_ORIGIN=raise_af")
            ok = False

        # Attempt to load configuration
        try:
            load_config()
        except Exception as exc:
            print(f"✗ Failed to load configuration: {exc}")
            ok = False

        # Run system health check
        health = run_health_check(print_report=True)
        if not health.healthy:
            ok = False

        # Report ticket statistics
        stats = get_ticket_stats()
        print(f"\nTickets: total={stats['total']}, open={stats['open']}, completed={stats['completed']}")

    return 0 if ok else 1


def cmd_repair(args: argparse.Namespace) -> int:
    """Fix common database and state issues.

    This command performs maintenance operations to repair common issues:
    - Database integrity checks
    - WAL checkpoint and VACUUM
    - Orphaned record cleanup
    - State file validation
    """
    project_root = Path(args.project_root or Path.cwd())
    dry_run = not args.execute

    with ActifixContext(project_root=project_root):
        from .persistence.database import get_database_connection
        from .state_paths import get_actifix_paths

        paths = get_actifix_paths(project_root=project_root)
        enforce_raise_af_only(paths)

        print("=== Actifix Repair ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}\n")

        issues_found = 0
        issues_fixed = 0

        # 1. Database integrity check
        print("1. Running database integrity check...")
        try:
            conn = get_database_connection(paths)
            with conn:
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result and result[0] == "ok":
                    print("   ✓ Database integrity OK")
                else:
                    print(f"   ✗ Database integrity issues: {result}")
                    issues_found += 1
        except Exception as e:
            print(f"   ✗ Failed to check integrity: {e}")
            issues_found += 1

        # 2. WAL checkpoint
        print("\n2. Checking WAL checkpoint...")
        try:
            conn = get_database_connection(paths)
            with conn:
                cursor = conn.execute("PRAGMA wal_checkpoint(FULL)")
                result = cursor.fetchone()
                if result:
                    busy, log_frames, checkpointed = result
                    if log_frames > 0:
                        print(f"   ✓ Checkpointed {checkpointed} frames")
                        if not dry_run:
                            issues_fixed += 1
                    else:
                        print("   ✓ WAL checkpoint clean")
                else:
                    print("   ✓ WAL checkpoint clean")
        except Exception as e:
            print(f"   ✗ Failed to checkpoint WAL: {e}")
            issues_found += 1

        # 3. VACUUM database
        print("\n3. Optimizing database...")
        try:
            if not dry_run:
                conn = get_database_connection(paths)
                with conn:
                    conn.execute("VACUUM")
                    print("   ✓ Database optimized")
                    issues_fixed += 1
            else:
                print("   • Would run VACUUM (skipped in dry-run)")
        except Exception as e:
            print(f"   ✗ Failed to VACUUM: {e}")
            issues_found += 1

        # 4. Check for orphaned state files
        print("\n4. Checking state files...")
        orphaned_files = []
        state_dir = paths.state_dir
        if state_dir.exists():
            for file in state_dir.glob("*.json"):
                if file.name not in ["module_statuses.json", "actifix_fallback_queue.json"]:
                    orphaned_files.append(file)

        if orphaned_files:
            print(f"   • Found {len(orphaned_files)} potentially orphaned state files")
            for file in orphaned_files:
                print(f"     - {file.name}")
            issues_found += len(orphaned_files)
        else:
            print("   ✓ No orphaned state files")

        # 5. Validate module status file
        print("\n5. Validating module status...")
        module_status_file = state_dir / "module_statuses.json"
        if module_status_file.exists():
            try:
                import json
                with open(module_status_file) as f:
                    data = json.load(f)
                if "schema_version" in data and "statuses" in data:
                    print(f"   ✓ Module status file valid ({len(data.get('statuses', {}))} modules)")
                else:
                    print("   ✗ Module status file missing required fields")
                    issues_found += 1
            except Exception as e:
                print(f"   ✗ Failed to validate module status: {e}")
                issues_found += 1
        else:
            print("   • No module status file found")

        # Summary
        print("\n=== Summary ===")
        print(f"Issues found: {issues_found}")
        print(f"Issues fixed: {issues_fixed}")

        if dry_run and issues_found > 0:
            print("\nRun with --execute to apply fixes")

        return 0 if issues_found == 0 else 1


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

    # Status command
    status_parser = subparsers.add_parser("status", help="Show concise runtime summary")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show quick operational metrics")

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
    
    # Diagnostics command
    diagnostics_parser = subparsers.add_parser("diagnostics", help="Export diagnostics bundle")
    diagnostics_parser.add_argument(
        "diagnostics_action",
        choices=["summary", "export"],
        help="Diagnostics action (summary or export)",
    )
    diagnostics_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output path for diagnostics bundle (export only)",
    )
    diagnostics_parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Exclude logs from bundle",
    )
    diagnostics_parser.add_argument(
        "--no-tickets",
        action="store_true",
        help="Exclude tickets from bundle",
    )

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Inspect event logs")
    logs_subparsers = logs_parser.add_subparsers(dest="logs_action")
    logs_tail_parser = logs_subparsers.add_parser("tail", help="Show recent event log entries")
    logs_tail_parser.add_argument("--limit", type=int, default=50, help="Number of events to show")
    logs_tail_parser.add_argument("--level", help="Filter by log level (INFO, WARNING, ERROR, etc.)")
    logs_tail_parser.add_argument("--event-type", help="Filter by event type")
    logs_tail_parser.add_argument("--source", help="Filter by source")
    logs_tail_parser.add_argument("--ticket-id", help="Filter by ticket ID")
    logs_tail_parser.add_argument("--correlation-id", help="Filter by correlation ID")

    # Config command
    config_parser = subparsers.add_parser("config", help="Inspect configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    config_subparsers.add_parser("diff", help="Show config overrides vs defaults")

    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Manage persistence queues")
    queue_subparsers = queue_parser.add_subparsers(dest="queue_action")
    queue_subparsers.add_parser("replay", help="Replay fallback queue entries")

    # Tickets command
    tickets_parser = subparsers.add_parser("tickets", help="Manage tickets")
    tickets_subparsers = tickets_parser.add_subparsers(dest="tickets_action")
    tickets_cleanup = tickets_subparsers.add_parser(
        "cleanup",
        help="Auto-complete stale duplicate tickets",
    )
    tickets_cleanup.add_argument(
        "--min-age-hours",
        type=float,
        default=24.0,
        help="Minimum age before auto-completing duplicates (default: 24)",
    )
    tickets_cleanup.add_argument(
        "--execute",
        action="store_true",
        help="Apply cleanup (default is dry-run)",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run self-tests")

    # Modules command
    modules_parser = subparsers.add_parser("modules", help="Manage module status")
    modules_parser.add_argument(
        "modules_action",
        choices=["list", "enable", "disable", "create", "validate", "graph"],
        help="Module action",
    )
    modules_parser.add_argument(
        "module_id",
        nargs="?",
        help="Module identifier (e.g., modules.yahtzee)",
    )
    modules_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Module host (create only)",
    )
    modules_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Module port (create only)",
    )
    modules_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing module scaffold (create only)",
    )
    
    # Doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Diagnose environment and configuration")

    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Fix common DB/state issues")
    repair_parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply repairs (default is dry-run)",
    )

    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command
    commands = {
        "init": cmd_init,
        "health": cmd_health,
        "status": cmd_status,
        "metrics": cmd_metrics,
        "record": cmd_record,
        "process": cmd_process,
        "stats": cmd_stats,
        "quarantine": cmd_quarantine,
        "diagnostics": cmd_diagnostics,
        "logs": cmd_logs,
        "config": cmd_config,
        "queue": cmd_queue,
        "tickets": cmd_tickets,
        "test": cmd_test,
        "modules": cmd_modules,
        "doctor": cmd_doctor,
        "repair": cmd_repair,
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
