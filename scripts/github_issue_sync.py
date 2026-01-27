#!/usr/bin/env python3
"""
GitHub issue sync helper for Actifix tickets.

This script can be used to publish selected tickets into a GitHub repository
so that the broader engineering organization can track critical issues in
their existing workflows. It uses the configured GitHub token / repository
and writes metadata back into the ticket once the issue is created.

Usage:
    ACTIFIX_CHANGE_ORIGIN=raise_af python3 scripts/github_issue_sync.py \
        --repo gmanldn/actifix --ticket ACT-20260125-33E91

Command-line options allow you to filter tickets by run label or specify
custom templates, labels, and assignees. The script is idempotent and will
skip tickets that already reported a GitHub issue unless --force is used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Iterable, List, Mapping, Optional, Sequence

from actifix.raise_af import TicketPriority, record_error
from actifix.persistence.ticket_repo import TicketFilter, get_ticket_repository
from actifix.security.credentials import get_credential_manager
from actifix.state_paths import get_actifix_paths, init_actifix_files


DEFAULT_TITLE_TEMPLATE = "{ticket_id}: {message_line}"
DEFAULT_BODY_TEMPLATE = textwrap.dedent(
    """
    ## Actifix ticket {ticket_id}
    {message}

    - **Priority:** {priority}
    - **Run label:** {run_label}
    - **Source:** {source}
    - **Status:** {status}
    - **Stack trace:** `{stack_trace}`\n
    """
).strip()


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize selected Actifix tickets with GitHub issues."
    )
    parser.add_argument(
        "--tickets",
        "-t",
        nargs="+",
        help="Ticket IDs to publish (can be repeated).",
        dest="ticket_ids",
        default=[],
    )
    parser.add_argument(
        "--run-label",
        "-r",
        help="Publish all open tickets with this run label.",
    )
    parser.add_argument(
        "--repo",
        "-R",
        help="GitHub repository in owner/repo format. Falls back to ACTIFIX_GITHUB_REPO.",
    )
    parser.add_argument(
        "--labels",
        "-l",
        action="append",
        help="Comma-separated list of labels to add to the GitHub issue.",
    )
    parser.add_argument(
        "--assignees",
        "-a",
        action="append",
        help="Comma-separated list of GitHub usernames to assign.",
    )
    parser.add_argument(
        "--title-template",
        help="Template for the GitHub issue title (Python format).",
        default=DEFAULT_TITLE_TEMPLATE,
    )
    parser.add_argument(
        "--body-template",
        help="Template for the GitHub issue body (Python format).",
        default=DEFAULT_BODY_TEMPLATE,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the payload without creating GitHub issues.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-sync tickets even if they already have a GitHub issue recorded.",
    )
    return parser.parse_args(argv)


def _ensure_paths() -> None:
    paths = get_actifix_paths()
    init_actifix_files(paths)


def _flatten_comma_values(raw: Optional[List[str]]) -> List[str]:
    if not raw:
        return []
    values: List[str] = []
    for entry in raw:
        values.extend(part.strip() for part in entry.split(",") if part.strip())
    return values


def _escape_for_template(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.replace("{", "{{").replace("}", "}}")


def _build_context(ticket: Mapping[str, object]) -> Mapping[str, str]:
    message = str(ticket.get("message") or "").strip()
    first_line = message.splitlines()[0][:120] if message else ""
    stack = str(ticket.get("stack_trace") or "").strip()
    return {
        "ticket_id": ticket.get("id") or "unknown",
        "priority": ticket.get("priority") or "unknown",
        "run_label": ticket.get("run_label") or "n/a",
        "source": ticket.get("source") or "unknown",
        "status": ticket.get("status") or "Open",
        "message": _escape_for_template(message),
        "message_line": _escape_for_template(first_line),
        "stack_trace": _escape_for_template(stack or "none"),
    }


def _collect_tickets(
    repo,
    ticket_ids: Sequence[str],
    run_label: Optional[str],
    force: bool,
) -> List[Mapping[str, object]]:
    selected: List[Mapping[str, object]] = []
    seen: set[str] = set()

    def _add(record: Mapping[str, object]) -> None:
        ticket_id = str(record.get("id"))
        if ticket_id in seen:
            return
        if not force and record.get("github_issue_url"):
            return
        seen.add(ticket_id)
        selected.append(record)

    for ticket_id in ticket_ids:
        record = repo.get_ticket(ticket_id)
        if record:
            _add(record)

    if run_label:
        open_tickets = repo.get_tickets(TicketFilter(status="Open"))
        for ticket in open_tickets:
            if ticket.get("run_label") == run_label:
                _add(ticket)

    return selected


def _load_github_token() -> Optional[str]:
    env_token = os.environ.get("ACTIFIX_GITHUB_TOKEN")
    if env_token:
        return env_token
    manager = get_credential_manager()
    try:
        return manager.retrieve_credential("github_token")
    except Exception:
        return None


def _create_issue_payload(
    ticket: Mapping[str, object],
    title_template: str,
    body_template: str,
    labels: List[str],
    assignees: List[str],
) -> dict:
    context = _build_context(ticket)
    title = title_template.format_map(context)
    body = body_template.format_map(context)
    payload = {
        "title": title,
        "body": body,
    }
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees
    return payload


def _post_issue(repo_slug: str, token: str, payload: dict) -> dict:
    url = f"https://api.github.com/repos/{repo_slug}/issues"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Actifix/GitHubSync",
    }
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))


def _update_ticket_sync_state(
    repo,
    ticket_id: str,
    state: str,
    message: Optional[str] = None,
    issue_number: Optional[int] = None,
    issue_url: Optional[str] = None,
) -> None:
    updates = {
        "github_sync_state": state,
        "github_sync_message": message,
    }
    if issue_number is not None:
        updates["github_issue_number"] = issue_number
    if issue_url:
        updates["github_issue_url"] = issue_url
    repo.update_ticket(ticket_id, updates)


def _record_sync_error(ticket_id: str, message: str) -> None:
    error_message = f"GitHub sync failed for {ticket_id}: {message}"
    record_error(
        message=error_message,
        source="scripts/github_issue_sync.py:_record_sync_error",
        priority=TicketPriority.P2,
        error_type="GitHubSyncError",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    _ensure_paths()
    repo_slug = args.repo or os.environ.get("ACTIFIX_GITHUB_REPO")
    if not repo_slug:
        print("ERROR: GitHub repository is required (--repo or ACTIFIX_GITHUB_REPO).", file=sys.stderr)
        return 1

    token = _load_github_token()
    if not token:
        print("ERROR: GitHub token is required (ACTIFIX_GITHUB_TOKEN or credential 'github_token').", file=sys.stderr)
        return 1

    repo = get_ticket_repository()
    tickets = _collect_tickets(repo, args.ticket_ids, args.run_label, args.force)

    if not tickets:
        print("No tickets matched the selection criteria.")
        return 0

    labels = _flatten_comma_values(args.labels)
    assignees = _flatten_comma_values(args.assignees)

    for ticket in tickets:
        ticket_id = str(ticket.get("id"))
        payload = _create_issue_payload(
            ticket,
            args.title_template,
            args.body_template,
            labels,
            assignees,
        )
        if args.dry_run:
            print(f"[DRY-RUN] {ticket_id} -> {json.dumps(payload, indent=2)}")
            continue

        try:
            issue = _post_issue(repo_slug, token, payload)
            issue_number = issue.get("number")
            issue_url = issue.get("html_url")
            _update_ticket_sync_state(
                repo,
                ticket_id,
                state="synced",
                message=f"Synced at {datetime.now(timezone.utc).isoformat()}",
                issue_number=issue_number,
                issue_url=issue_url,
            )
            print(f"Created GitHub issue #{issue_number} for {ticket_id}: {issue_url}")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            _update_ticket_sync_state(
                repo,
                ticket_id,
                state="failed",
                message=f"{exc.code} {exc.reason}: {error_body}",
            )
            _record_sync_error(ticket_id, f"{exc.code} {exc.reason}")
            print(f"FAILED to create issue for {ticket_id}: {exc.code} {exc.reason}", file=sys.stderr)
        except Exception as exc:
            _update_ticket_sync_state(
                repo,
                ticket_id,
                state="failed",
                message=str(exc),
            )
            _record_sync_error(ticket_id, str(exc))
            print(f"FAILED to create issue for {ticket_id}: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
