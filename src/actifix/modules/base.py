#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared module utilities (config, paths, logging, error capture, health helpers)."""

from __future__ import annotations

import os
from functools import wraps
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Callable, Any

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error, redact_secrets_from_text
from actifix.state_paths import get_actifix_paths

from .config import get_module_config


@dataclass
class ModuleAnchor:
    module_key: str
    defaults: Mapping[str, object]
    metadata: Mapping[str, object]
    project_root: Optional[Path]


class ModuleBase:
    """Minimal helper for modules that share config, logging, and error capture."""

    def __init__(
        self,
        module_key: str,
        defaults: Mapping[str, object],
        metadata: Mapping[str, object],
        *,
        project_root: Optional[str | Path] = None,
    ) -> None:
        self.anchor = ModuleAnchor(
            module_key=module_key,
            defaults=defaults,
            metadata=metadata,
            project_root=Path(project_root).resolve() if project_root else None,
        )

    @property
    def module_key(self) -> str:
        return self.anchor.module_key

    @property
    def module_id(self) -> str:
        name = str(self.anchor.metadata.get("name") or "").strip()
        if name:
            return name
        return f"modules.{self.module_key}"

    @property
    def module_defaults(self) -> Mapping[str, object]:
        return self.anchor.defaults

    @property
    def project_root(self) -> Optional[Path]:
        return self.anchor.project_root

    def resolve_host_port(
        self,
        host: str | None,
        port: int | None,
    ) -> Tuple[str, int]:
        config = get_module_config(
            self.module_key,
            self.module_defaults,
            project_root=self.project_root,
        )
        resolved_host = host or str(config.get("host", self.module_defaults.get("host", "127.0.0.1")))
        resolved_port_value = port or config.get("port", self.module_defaults.get("port", 0))
        try:
            resolved_port = int(resolved_port_value or 0)
        except (TypeError, ValueError):
            resolved_port = int(self.module_defaults.get("port") or 0)
        return resolved_host, resolved_port

    def get_paths(self):
        """Return Actifix paths for the configured project root."""
        return get_actifix_paths(project_root=self.project_root)

    def health_response(self) -> dict[str, object]:
        """Default health route helper."""
        if os.environ.get("ACTIFIX_MODULE_HEALTH_MINIMAL") == "1":
            return {"status": "ok"}
        return {
            "status": "ok",
            "module": self.module_key,
            "module_id": self.module_id,
        }

    def health_handler(self) -> Callable[[], dict[str, object]]:
        """Return a callable suitable for a /health route."""
        def _handler() -> dict[str, object]:
            return self.health_response()
        return _handler

    def error_boundary(
        self,
        *,
        source: str,
        error_type: str = "ModuleError",
        priority: TicketPriority | str = TicketPriority.P2,
        response: Optional[Callable[[Exception], Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator that wraps a handler with error capture and a safe response."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    self.record_module_error(
                        message=f"{self.module_key} handler failed: {exc}",
                        source=source,
                        error_type=error_type,
                        priority=priority,
                    )
                    if response:
                        return response(exc)
                    return {"error": str(exc)}, 500
            return wrapper
        return decorator

    def log_gui_init(
        self,
        host: str,
        port: int,
        *,
        event_name: str | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        """Log the module GUI configuration event."""
        paths = self.get_paths()
        payload = {
            "module": self.module_key,
            "module_id": self.module_id,
            "host": host,
            "port": port,
            "state_dir": str(paths.state_dir),
        }
        if extra:
            payload.update(extra)
        log_event(
            event_name or f"{self.module_key.upper()}_GUI_INIT",
            f"{self.module_key} GUI configured",
            extra=payload,
            source=f"modules.{self.module_key}:ModuleBase.log_gui_init",
        )
        # Best-effort AgentVoice (AgentThoughts) capture for review purposes.
        try:
            from actifix.agent_voice import record_agent_voice

            record_agent_voice(
                f"{self.module_id} gui init",
                agent_id=self.module_id,
                run_label=self._run_label(),
                level="INFO",
                extra=payload,
            )
        except Exception:
            # record_agent_voice already records failures via raise_af; don't block startup.
            pass

    def record_module_info(
        self,
        thought: str,
        *,
        run_label: str | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        """Record a module informational AgentVoice row (best-effort)."""
        try:
            from actifix.agent_voice import record_agent_voice

            record_agent_voice(
                redact_secrets_from_text(thought),
                agent_id=self.module_id,
                run_label=self._run_label(run_label),
                level="INFO",
                extra=dict(extra) if extra else None,
            )
        except Exception:
            pass

    def _run_label(self, override: str | None = None) -> str:
        if override:
            return override
        return f"{self.module_key}-gui"

    def record_module_error(
        self,
        message: str,
        *,
        source: str,
        run_label: str | None = None,
        error_type: str = "ModuleError",
        priority: TicketPriority | str = TicketPriority.P2,
    ) -> None:
        """Record a sanitized module error with a default run label."""
        safe_message = redact_secrets_from_text(message)
        # Best-effort AgentVoice (AgentThoughts) capture for review purposes.
        try:
            from actifix.agent_voice import record_agent_voice

            record_agent_voice(
                safe_message,
                agent_id=self.module_id,
                run_label=self._run_label(run_label),
                level="ERROR",
                extra={"source": source, "error_type": error_type},
            )
        except Exception:
            pass
        record_error(
            message=safe_message,
            source=source,
            run_label=self._run_label(run_label),
            error_type=error_type,
            priority=priority,
        )


# Port conflict handling utilities

def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available for binding."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False


def find_process_on_port(port: int) -> Optional[dict]:
    """Find the process using a specific port.
    
    Returns dict with pid, process_name, command, or None if not found.
    """
    import subprocess
    import platform
    
    try:
        system = platform.system()
        if system == "Darwin" or system == "Linux":
            # Use lsof on Unix-like systems
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    # Parse lsof output (skip header)
                    parts = lines[1].split()
                    return {
                        "pid": int(parts[1]),
                        "process_name": parts[0],
                        "command": " ".join(parts[8:]) if len(parts) > 8 else parts[0],
                    }
        elif system == "Windows":
            # Use netstat on Windows
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            return {
                                "pid": int(parts[-1]),
                                "process_name": "unknown",
                                "command": f"Process on port {port}",
                            }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, IndexError):
        pass
    
    return None


def handle_port_conflict(
    port: int,
    host: str = "127.0.0.1",
    module_name: str = "unknown",
    auto_kill: bool = False
) -> tuple[bool, Optional[str]]:
    """Handle port conflict with remediation.
    
    Args:
        port: Port number to check
        host: Host address
        module_name: Name of module trying to bind
        auto_kill: If True, attempt to kill conflicting process
    
    Returns:
        (success: bool, message: Optional[str])
    """
    if check_port_available(port, host):
        return True, None
    
    # Port is in use - find the process
    process_info = find_process_on_port(port)
    
    if process_info:
        message = (
            f"Port {port} is already in use by {process_info['process_name']} "
            f"(PID: {process_info['pid']})"
        )
        
        record_error(
            message=f"{module_name}: {message}",
            source=f"modules/{module_name}/port_conflict",
            error_type="PortConflict",
            priority=TicketPriority.P2,
        )
        
        if auto_kill:
            try:
                import os
                import signal
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(process_info["pid"])], check=True)
                else:
                    os.kill(process_info["pid"], signal.SIGTERM)
                
                # Wait a moment and check if port is now available
                import time
                time.sleep(0.5)
                
                if check_port_available(port, host):
                    return True, f"Killed conflicting process {process_info['pid']}"
                else:
                    return False, f"{message}. Failed to free port after killing process."
            except Exception as e:
                return False, f"{message}. Failed to kill process: {e}"
        else:
            remediation = (
                f"\n\nRemediation options:\n"
                f"1. Kill the process: kill {process_info['pid']}\n"
                f"2. Use a different port via config\n"
                f"3. Stop the conflicting service"
            )
            return False, message + remediation
    else:
        message = f"Port {port} is already in use (could not identify process)"
        record_error(
            message=f"{module_name}: {message}",
            source=f"modules/{module_name}/port_conflict",
            error_type="PortConflict",
            priority=TicketPriority.P2,
        )
        remediation = (
            f"\n\nRemediation options:\n"
            f"1. Check running processes manually: lsof -i :{port}\n"
            f"2. Use a different port via config"
        )
        return False, message + remediation
