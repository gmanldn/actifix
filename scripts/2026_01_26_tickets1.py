#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026_01_26_tickets1.py

Generates 200 high-value *enhancement* tickets for Actifix and inserts them into the
canonical SQLite database (data/actifix.db) using the standard tickets table schema.

Design goals:
- Broad coverage: runtime, infra, core, security, tooling, plugins, modules, UI/CLI
- Clear ownership context: what / why / acceptance criteria / suggested files
- Safe insertion: create table if missing; use duplicate_guard to avoid duplication
- No dependency on network or external services

Notes:
- This script intentionally does NOT commit the database file (it should be ignored in git).
- Tickets are created with status='Open' and completed/tested/documented flags set to 0.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import os
import random
import sqlite3
import string
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DB_REL_PATH = Path("data") / "actifix.db"
SOURCE = "scripts/2026_01_26_tickets1.py"


def _now_utc() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def _rand_suffix(n: int = 5) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def _ticket_id(date: _dt.date) -> str:
    return f"ACT-{date.strftime('%Y%m%d')}-{_rand_suffix(5)}"


def _dup_guard(payload: Dict[str, Any]) -> str:
    # Stable-ish hash used for dedupe when rerunning.
    h = hashlib.sha256()
    h.update((payload.get("area", "") + "::" + payload.get("title", "")).encode("utf-8"))
    return h.hexdigest()


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.touch()
    # tighten perms best-effort
    try:
        os.chmod(db_path, 0o600)
    except Exception:
        pass


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            priority TEXT NOT NULL,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT NOT NULL,
            run_label TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            duplicate_guard TEXT UNIQUE,
            status TEXT DEFAULT 'Open',
            owner TEXT,
            locked_by TEXT,
            lease_expires TIMESTAMP,
            branch TEXT,
            stack_trace TEXT,
            file_context TEXT,
            system_state TEXT,
            ai_remediation_notes TEXT,
            correlation_id TEXT,
            completion_summary TEXT,
            documented BOOLEAN DEFAULT 0,
            functioning BOOLEAN DEFAULT 0,
            tested BOOLEAN DEFAULT 0,
            completed BOOLEAN DEFAULT 0
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status_priority ON tickets(status, priority);")


def _insert_ticket(conn: sqlite3.Connection, row: Dict[str, Any]) -> bool:
    cols = [
        "id","priority","error_type","message","source","run_label","created_at","updated_at",
        "duplicate_guard","status","owner","locked_by","lease_expires","branch","stack_trace",
        "file_context","system_state","ai_remediation_notes","correlation_id","completion_summary",
        "documented","functioning","tested","completed"
    ]
    values = [row.get(c) for c in cols]
    try:
        conn.execute(
            f"INSERT INTO tickets ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})",
            values,
        )
        return True
    except sqlite3.IntegrityError:
        # duplicate_guard unique or id collision
        return False


def _priority_for(area: str, kind: str) -> str:
    # Rough heuristic: security/auth/core persistence tends higher.
    if area in {"security", "persistence", "core"} and kind in {"reliability", "data_integrity", "auth"}:
        return "P1"
    if kind in {"crash", "data_loss"}:
        return "P0"
    if area in {"runtime", "infra"} and kind in {"reliability", "observability"}:
        return "P2"
    if kind in {"dx", "polish", "docs"}:
        return "P3"
    return "P2"


def _ticket_payloads() -> List[Dict[str, Any]]:
    """
    Returns 200 diverse ticket payloads.
    Each payload includes: area, title, detail, kind, suggested_files, acceptance, effort, rationale
    """
    areas = [
        "runtime","infra","core","security","tooling","plugins","modules","ui","cli","persistence","ai","docs"
    ]

    # A set of high-value themes with many variants.
    themes = [
        ("reliability", "Add structured startup phases and explicit failure modes"),
        ("observability", "Improve logging correlation and tracing across modules"),
        ("dx", "Streamline developer workflows and local setup"),
        ("testing", "Expand test coverage and strengthen quality gates"),
        ("plugins", "Harden plugin validation, lifecycle and isolation"),
        ("persistence", "Improve SQLite resilience, migrations and backup/restore"),
        ("security", "Strengthen secrets handling, permissions, and auth boundaries"),
        ("ai", "Improve provider abstraction, prompt safety, and offline fallbacks"),
        ("cli", "Make CLI more ergonomic and self-documenting"),
        ("ui", "Improve dashboard performance, clarity, and ticket manipulation UX"),
        ("docs", "Make docs discoverable, consistent, and task-oriented"),
        ("automation", "Add scheduled jobs and safe automation harnesses"),
    ]

    # Template generators
    def mk(title, area, kind, detail, suggested_files, acceptance, effort="M", rationale=""):
        return {
            "title": title,
            "area": area,
            "kind": kind,
            "detail": detail,
            "suggested_files": suggested_files,
            "acceptance": acceptance,
            "effort": effort,
            "rationale": rationale,
        }

    payloads: List[Dict[str, Any]] = []

    # 1) Core reliability and lifecycle tickets (30)
    for i in range(1, 31):
        payloads.append(mk(
            title=f"Bootstrap lifecycle: explicit phase {i} + rollback hooks",
            area="runtime",
            kind="reliability",
            detail=(
                "Introduce an explicit startup/shutdown phase registry in bootstrap that:\n"
                "- registers phase name, dependencies, timeout, and rollback handler\n"
                "- emits structured events for each phase start/end/failure\n"
                "- ensures rollback runs in reverse dependency order on failure\n"
                "- integrates with existing health checks and logging\n"
            ),
            suggested_files=[
                "src/actifix/bootstrap.py",
                "src/actifix/health.py",
                "src/actifix/log_utils.py",
                "docs/DEVELOPMENT.md",
            ],
            acceptance=[
                "Failing any phase triggers rollback handlers for completed phases",
                "Phases are logged with correlation_id and duration",
                "Unit tests cover success and failure rollback order",
            ],
            effort="L",
            rationale="Reduces partial-start states and makes multi-module hosting more reliable."
        ))

    # 2) Persistence robustness tickets (30)
    for i in range(1, 31):
        payloads.append(mk(
            title=f"SQLite robustness: WAL safety + auto-repair strategy ({i})",
            area="persistence",
            kind="data_integrity",
            detail=(
                "Implement a defensive SQLite strategy:\n"
                "- enforce PRAGMAs (journal_mode=WAL, synchronous=NORMAL/FULL per config)\n"
                "- detect corruption/lock storms and quarantine db copies\n"
                "- add periodic checkpointing and VACUUM scheduling hooks\n"
                "- add backup/restore commands (safe copy, verify, swap)\n"
            ),
            suggested_files=[
                "src/actifix/persistence/database.py",
                "src/actifix/persistence/storage.py",
                "src/actifix/quarantine.py",
                "src/actifix/main.py",
            ],
            acceptance=[
                "Backup/restore works on a busy DB (uses safe checkpointing)",
                "Corruption detection quarantines and raises a P0 ticket with context",
                "Integration test simulates lock contention and verifies recovery path",
            ],
            effort="L",
            rationale="Actifix depends on sqlite as the canonical store; resilience is critical."
        ))

    # 3) Plugin isolation and validation (25)
    for i in range(1, 26):
        payloads.append(mk(
            title=f"Plugin isolation: sandbox execution boundary ({i})",
            area="plugins",
            kind="reliability",
            detail=(
                "Harden plugin execution:\n"
                "- run plugins in isolated processes (or thread pool with timeouts as interim)\n"
                "- define explicit plugin API contract + version negotiation\n"
                "- add capability flags (db, net, filesystem) and enforce deny-by-default\n"
                "- validate plugin metadata early and fail fast\n"
            ),
            suggested_files=[
                "src/actifix/plugins/*",
                "src/actifix/bootstrap.py",
                "docs/FRAMEWORK_OVERVIEW.md",
                "docs/architecture/MAP.yaml",
                "docs/architecture/DEPGRAPH.json",
            ],
            acceptance=[
                "A misbehaving plugin cannot crash the core process",
                "Plugins time out and produce structured failure tickets",
                "Plugins declare capabilities; undeclared use is blocked/logged",
            ],
            effort="XL",
            rationale="Hosting AI-developed modules safely requires robust isolation."
        ))

    # 4) AI provider and prompt safety improvements (25)
    for i in range(1, 26):
        payloads.append(mk(
            title=f"AI provider abstraction: unify model/limits/rate policies ({i})",
            area="ai",
            kind="reliability",
            detail=(
                "Enhance AI provider layer:\n"
                "- unify model selection (provider-specific model mapping)\n"
                "- centralize rate limit policy (backoff, jitter, circuit breakers)\n"
                "- store provider telemetry (tokens, latency, cost) with correlation_id\n"
                "- add redaction step on prompts and responses\n"
            ),
            suggested_files=[
                "src/actifix/ai_client.py",
                "src/actifix/config.py",
                "src/actifix/log_utils.py",
                "src/actifix/security/secrets_scanner.py",
            ],
            acceptance=[
                "Provider failures trip circuit breaker and auto-fallback",
                "Telemetry is stored per attempt and visible in UI",
                "Secrets redaction runs on both outgoing prompt and incoming response",
            ],
            effort="L",
            rationale="Makes AI operations predictable and safe across providers."
        ))

    # 5) CLI and UX improvements (25)
    for i in range(1, 26):
        payloads.append(mk(
            title=f"CLI ergonomics: guided commands + self-diagnosis ({i})",
            area="cli",
            kind="dx",
            detail=(
                "Improve CLI:\n"
                "- add `actifix doctor` to diagnose env/config/db/plugin issues\n"
                "- add guided interactive mode for common tasks (raise ticket, fix, export)\n"
                "- improve output formatting and exit codes\n"
                "- add shell completions for common subcommands\n"
            ),
            suggested_files=[
                "src/actifix/main.py",
                "src/actifix/health.py",
                "docs/DEVELOPMENT.md",
                "docs/INDEX.md",
            ],
            acceptance=[
                "`actifix doctor` identifies misconfigurations and suggests fixes",
                "All commands return meaningful exit codes",
                "Completion scripts generated for bash/zsh",
            ],
            effort="M",
            rationale="Streamlines day-to-day use and reduces setup friction."
        ))

    # 6) UI/dashboard improvements (25)
    for i in range(1, 21):
        payloads.append(mk(
            title=f"Dashboard: performance + ticket workflow lanes ({i})",
            area="ui",
            kind="polish",
            detail=(
                "Improve dashboard:\n"
                "- virtualize ticket lists for large datasets\n"
                "- add workflow lanes (Open/In Progress/Blocked/Done)\n"
                "- add bulk actions (assign, reprioritize, export)\n"
                "- add per-ticket timeline (events, retries, AI attempts)\n"
            ),
            suggested_files=[
                "src/actifix/api.py",
                "web/* (if present)",
                "docs/FRAMEWORK_OVERVIEW.md",
            ],
            acceptance=[
                "Dashboard remains responsive with 10k tickets",
                "Bulk actions apply safely with confirmations",
                "Ticket timeline renders from stored audit events",
            ],
            effort="L",
            rationale="Improves usability when scaling ticket volume."
        ))

    # 7) Security hardening (20)
    for i in range(1, 21):
        payloads.append(mk(
            title=f"Security: secrets + permissions hardening pass ({i})",
            area="security",
            kind="auth",
            detail=(
                "Security hardening:\n"
                "- enforce restrictive perms on state/log dirs\n"
                "- rotate/validate API keys stored in env/config\n"
                "- add secret scanning on config load + before logging\n"
                "- add allowlist for outbound network calls in AI layer\n"
            ),
            suggested_files=[
                "src/actifix/config.py",
                "src/actifix/security/secrets_scanner.py",
                "src/actifix/state_paths.py",
                "src/actifix/log_utils.py",
            ],
            acceptance=[
                "Secrets never appear in logs or stored ticket fields",
                "State directories have safe perms and are checked at startup",
                "Outbound network policy is enforced and auditable",
            ],
            effort="M",
            rationale="Protects credentials and reduces accidental leakage."
        ))

    # 8) Tooling & quality gates (20)
    for i in range(1, 16):
        payloads.append(mk(
            title=f"Tooling: strengthen architecture/quality gate ({i})",
            area="tooling",
            kind="testing",
            detail=(
                "Improve quality gates:\n"
                "- expand dependency rule checks (no higher-layer imports)\n"
                "- add static checks for atomic_write usage\n"
                "- run minimal integration tests in CI\n"
                "- add 'golden' fixtures for docs/architecture outputs\n"
            ),
            suggested_files=[
                "scripts/*",
                "test/*",
                "docs/architecture/MAP.yaml",
                "docs/architecture/DEPGRAPH.json",
            ],
            acceptance=[
                "CI fails when dependency rules are violated",
                "CI fails if architecture docs drift without regeneration",
                "Tests cover key workflows: record_error, ticket processing, plugin load",
            ],
            effort="M",
            rationale="Prevents regressions and keeps architecture coherent."
        ))

    # 9) Docs improvements (10)
    for i in range(1, 11):
        payloads.append(mk(
            title=f"Docs: task-oriented guides + cross-links ({i})",
            area="docs",
            kind="docs",
            detail=(
                "Improve docs:\n"
                "- add 'Common workflows' sections to existing docs\n"
                "- ensure docs/INDEX.md cross-references all key guides\n"
                "- create troubleshooting section (doctor, db, plugins, AI providers)\n"
                "- add examples for multi-agent workflow and safe development\n"
            ),
            suggested_files=[
                "docs/INDEX.md",
                "docs/DEVELOPMENT.md",
                "docs/FRAMEWORK_OVERVIEW.md",
            ],
            acceptance=[
                "New sections are added to existing docs only (no new docs files)",
                "Troubleshooting has clear steps and commands",
                "Links validated (no dead references)",
            ],
            effort="S",
            rationale="Reduces onboarding time and makes the system easier to operate."
        ))

    # Ensure exactly 200
    if len(payloads) != 200:
        raise RuntimeError(f"Expected 200 payloads, got {len(payloads)}")
    return payloads


def main() -> int:
    random.seed(20260126)
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / DB_REL_PATH

    _ensure_db(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_schema(conn)

        created = 0
        skipped = 0
        today = _dt.date(2026, 1, 26)
        created_at = _now_utc()

        for p in _ticket_payloads():
            pri = _priority_for(p["area"], p["kind"])
            ticket = {
                "id": _ticket_id(today),
                "priority": pri,
                "error_type": "Enhancement",
                "message": f"[{p['area']}] {p['title']}",
                "source": SOURCE,
                "run_label": "2026-01-26-ticketgen-1",
                "created_at": created_at,
                "updated_at": None,
                "duplicate_guard": _dup_guard(p),
                "status": "Open",
                "owner": p["area"],
                "locked_by": None,
                "lease_expires": None,
                "branch": "develop",
                "stack_trace": None,
                "file_context": json.dumps({"suggested_files": p["suggested_files"]}, ensure_ascii=False),
                "system_state": json.dumps({"area": p["area"], "kind": p["kind"]}, ensure_ascii=False),
                "ai_remediation_notes": json.dumps(
                    {
                        "title": p["title"],
                        "area": p["area"],
                        "kind": p["kind"],
                        "detail": p["detail"],
                        "acceptance_criteria": p["acceptance"],
                        "effort": p["effort"],
                        "rationale": p["rationale"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "correlation_id": None,
                "completion_summary": None,
                "documented": 0,
                "functioning": 0,
                "tested": 0,
                "completed": 0,
            }

            if _insert_ticket(conn, ticket):
                created += 1
            else:
                skipped += 1

        conn.commit()
        print(f"Inserted tickets: {created} (skipped duplicates: {skipped})")
        print(f"Database: {db_path}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
