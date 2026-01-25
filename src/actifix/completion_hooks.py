"""
Completion hooks for running custom scripts after ticket completion.

Provides safe execution of user-defined scripts with timeout and error handling.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from .log_utils import log_event
from .config import get_config


def _prepare_hook_env(ticket: Dict[str, Any]) -> Dict[str, str]:
    """
    Prepare environment variables for hook execution.

    Args:
        ticket: Ticket data to pass to hook.

    Returns:
        Environment dictionary with ticket data.
    """
    # Start with current environment
    env = os.environ.copy()

    # Add ticket data as environment variables
    env["ACTIFIX_TICKET_ID"] = ticket.get("id", "")
    env["ACTIFIX_TICKET_PRIORITY"] = ticket.get("priority", "")
    env["ACTIFIX_TICKET_ERROR_TYPE"] = ticket.get("error_type", "")
    env["ACTIFIX_TICKET_SOURCE"] = ticket.get("source", "")
    env["ACTIFIX_TICKET_STATUS"] = ticket.get("status", "")

    # Add full ticket as JSON (truncated if too large)
    ticket_json = json.dumps(ticket, default=str)
    if len(ticket_json) > 10000:
        ticket_json = ticket_json[:10000] + "..."
    env["ACTIFIX_TICKET_JSON"] = ticket_json

    return env


def _execute_hook(
    script_path: str,
    ticket: Dict[str, Any],
    timeout_seconds: int = 30,
) -> tuple[bool, str, str]:
    """
    Execute a single completion hook script.

    Args:
        script_path: Path to the script to execute.
        ticket: Ticket data to pass to script.
        timeout_seconds: Maximum execution time in seconds.

    Returns:
        Tuple of (success, stdout, stderr).
    """
    path = Path(script_path).expanduser().resolve()

    # Security: script must exist and be executable
    if not path.exists():
        return False, "", f"Script not found: {script_path}"

    if not os.access(path, os.X_OK):
        return False, "", f"Script not executable: {script_path}"

    # Prepare environment
    env = _prepare_hook_env(ticket)

    try:
        # Execute script with timeout
        result = subprocess.run(
            [str(path)],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,  # Don't raise on non-zero exit
        )

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", f"Script exceeded timeout of {timeout_seconds}s"
    except Exception as e:
        return False, "", f"Script execution failed: {type(e).__name__}: {e}"


def execute_completion_hooks(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute all configured completion hooks for a ticket.

    Args:
        ticket: Completed ticket data.

    Returns:
        Dictionary summarizing hook execution results.
    """
    config = get_config()
    hook_scripts_str = config.completion_hook_scripts.strip()

    if not hook_scripts_str:
        # No hooks configured
        return {"hooks_run": 0, "hooks_succeeded": 0, "hooks_failed": 0}

    # Parse hook scripts (comma-separated)
    hook_scripts = [
        script.strip()
        for script in hook_scripts_str.split(",")
        if script.strip()
    ]

    if not hook_scripts:
        return {"hooks_run": 0, "hooks_succeeded": 0, "hooks_failed": 0}

    results = {
        "hooks_run": 0,
        "hooks_succeeded": 0,
        "hooks_failed": 0,
        "failures": [],
    }

    for script_path in hook_scripts:
        results["hooks_run"] += 1

        log_event(
            "COMPLETION_HOOK_START",
            f"Executing completion hook: {script_path}",
            extra={
                "ticket_id": ticket.get("id", ""),
                "script_path": script_path,
            },
        )

        success, stdout, stderr = _execute_hook(script_path, ticket)

        if success:
            results["hooks_succeeded"] += 1
            log_event(
                "COMPLETION_HOOK_SUCCESS",
                f"Completion hook succeeded: {script_path}",
                extra={
                    "ticket_id": ticket.get("id", ""),
                    "script_path": script_path,
                    "stdout_preview": stdout[:200] if stdout else None,
                },
            )
        else:
            results["hooks_failed"] += 1
            results["failures"].append({
                "script": script_path,
                "stderr": stderr[:500] if stderr else "",
            })
            log_event(
                "COMPLETION_HOOK_FAILURE",
                f"Completion hook failed: {script_path}",
                extra={
                    "ticket_id": ticket.get("id", ""),
                    "script_path": script_path,
                    "stderr_preview": stderr[:200] if stderr else None,
                },
            )

    return results
