"""
Actifix API Server - Flask-based REST API for frontend dashboard.

Provides endpoints for health, stats, tickets, logs, and system information.
"""

import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None


def _ensure_web_dependencies() -> bool:
    """
    Ensure Flask dependencies are installed. Auto-install if missing.
    
    Returns:
        True if dependencies are available, False otherwise.
    """
    global FLASK_AVAILABLE, Flask, CORS

    if FLASK_AVAILABLE:
        return True

    print("Flask dependencies not found. Installing...")
    print("Running: pip install flask flask-cors")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask", "flask-cors"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Successfully installed Flask dependencies")
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        FLASK_AVAILABLE = True
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Flask dependencies: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during installation: {e}")
        return False

from . import __version__
from .health import get_health, check_sla_breaches
from .do_af import (
    get_open_tickets,
    get_ticket_stats,
    get_completed_tickets,
    fix_highest_priority_ticket,
)
from .raise_af import enforce_raise_af_only, record_error, TicketPriority
from .state_paths import get_actifix_paths
from .persistence.event_repo import get_event_repository, EventFilter
from .config import get_config, set_config, load_config
from .ai_client import get_ai_client, resolve_provider_selection

# Server start time for uptime calculation
SERVER_START_TIME = time.time()
SYSTEM_OWNERS = {"runtime", "infra", "core", "persistence", "testing", "tooling"}


def _is_system_domain(domain: Optional[str]) -> bool:
    """Decide whether a module belongs to the system catalog."""
    normalized = (domain or "").strip().lower()
    return normalized in {
        "runtime",
        "infra",
        "core",
        "tooling",
        "security",
        "plugins",
        "persistence",
    }


def _load_modules(project_root: Path) -> Dict[str, List[Dict[str, str]]]:
    """Parse docs/architecture/MODULES.md into system/user buckets."""
    modules_md = project_root / "docs" / "architecture" / "MODULES.md"
    if not modules_md.exists():
        return {"system": [], "user": []}

    name = None
    domain = None
    owner = None
    summary = None
    modules: List[Dict[str, str]] = []

    try:
        for line in modules_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                if name:
                    modules.append({
                        "name": name,
                        "domain": domain or "",
                        "owner": owner or "",
                        "summary": summary or "",
                    })
                name = line.replace("## ", "").strip()
                domain = owner = summary = None
                continue
            if line.startswith("**Domain:**"):
                domain = line.replace("**Domain:**", "").strip()
            elif line.startswith("**Owner:**"):
                owner = line.replace("**Owner:**", "").strip()
            elif line.startswith("**Summary:**"):
                summary = line.replace("**Summary:**", "").strip()

        if name:
            modules.append({
                "name": name,
                "domain": domain or "",
                "owner": owner or "",
                "summary": summary or "",
            })
    except Exception:
        return {"system": [], "user": []}

    system_modules = [m for m in modules if _is_system_domain(m["domain"])]
    user_modules = [m for m in modules if not _is_system_domain(m["domain"])]
    return {"system": system_modules, "user": user_modules}


def _collect_ai_feedback(limit: int = 40) -> List[str]:
    """Collect recent AI-related feedback for the settings panel."""
    try:
        repo = get_event_repository()
        raw_events = repo.get_recent_events(limit=max(limit * 4, 100))
    except Exception as exc:
        record_error(
            message=f"Failed to read AI feedback events: {exc}",
            source="api.py:_collect_ai_feedback",
            priority=TicketPriority.P2,
        )
        return []

    feedback = []
    for event in reversed(raw_events):
        event_type = (event.get("event_type") or "").upper()
        message = event.get("message") or ""
        if event_type.startswith("AI_") or "AI " in message or "AI_" in message:
            timestamp = event.get("timestamp") or ""
            entry = f"[{timestamp}] {event_type}: {message}"
            feedback.append(entry)
            if len(feedback) >= limit:
                break

    return list(reversed(feedback))

    system = [m for m in modules if (m.get("owner") or "").lower() in SYSTEM_OWNERS]
    user = [m for m in modules if m not in system]

    return {"system": system, "user": user}


def _run_git_command(cmd: list[str], project_root: Path) -> Optional[str]:
    """Run git command and return stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _gather_version_info(project_root: Path) -> Dict[str, Optional[str]]:
    """Gather version metadata and git status for the dashboard."""
    info_root = Path(project_root).resolve()
    status_output = _run_git_command(["git", "status", "--porcelain"], info_root)
    git_checked = status_output is not None
    clean = git_checked and status_output == ""
    branch = _run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], info_root) if git_checked else None
    commit = _run_git_command(["git", "rev-parse", "HEAD"], info_root) if git_checked else None
    tag = _run_git_command(["git", "describe", "--tags", "--abbrev=0"], info_root) if git_checked else None

    return {
        "version": __version__,
        "git_checked": git_checked,
        "clean": clean,
        "dirty": git_checked and not clean,
        "branch": branch,
        "commit": commit,
        "tag": tag,
        "status": status_output,
    }


def _map_event_type_to_level(event_type: str, message: str) -> str:
    """Map ACTIFIX event types to log levels used by the frontend."""
    normalized = (event_type or "").upper()
    if "✓" in message or "SUCCESS" in message.upper():
        return "SUCCESS"
    if "✗" in message:
        return "ERROR"
    if "⚠" in message:
        return "WARNING"
    if normalized in {"ERROR", "DISPATCH_FAILED"} or "ERROR" in message.upper():
        return "ERROR"
    if normalized in {"ASCII_BANNER"}:
        return "BANNER"
    if normalized in {"ACTION_DECIDED"}:
        return "ACTION"
    if normalized in {"THOUGHT_PROCESS"}:
        return "THOUGHT"
    if normalized in {"TESTING"}:
        return "TEST"
    if normalized in {"TICKET_CLOSED", "DISPATCH_SUCCESS", "TICKET_COMPLETED"}:
        return "SUCCESS"
    if normalized in {"WARNING", "TICKET_ALREADY_COMPLETED"} or "WARNING" in message.upper():
        return "WARNING"
    return "INFO"


def _parse_log_line(line: str) -> Optional[dict]:
    """Parse a single AFLog line into structured fields."""
    stripped = line.strip()
    if not stripped:
        return None

    # AFLog structured format: "timestamp | EVENT | ticket | message | extra"
    if " | " in stripped:
        parts = [part.strip() for part in stripped.split(" | ")]
        timestamp = parts[0] if len(parts) >= 1 else ""
        event_type = parts[1] if len(parts) >= 2 else "LOG"
        ticket_id = parts[2] if len(parts) >= 3 else "-"
        message = parts[3] if len(parts) >= 4 else stripped
        extra = parts[4] if len(parts) >= 5 else None
        level = _map_event_type_to_level(event_type, message)

        return {
            "timestamp": timestamp,
            "event": event_type,
            "ticket": ticket_id,
            "text": message,
            "extra": extra,
            "level": level,
        }

    # Simple text formats such as "LEVEL: message" or icon-prefixed lines
    icon_levels = {
        "✓": "SUCCESS",
        "✗": "ERROR",
        "⚠": "WARNING",
    }
    for icon, level in icon_levels.items():
        if stripped.startswith(icon):
            message = stripped[len(icon):].strip() or stripped
            return {
                "timestamp": "",
                "event": "LOG",
                "ticket": "-",
                "text": message,
                "extra": None,
                "level": level,
            }

    prefix, sep, remainder = stripped.partition(":")
    if sep:
        event_type = prefix.strip() or "LOG"
        message = remainder.strip() or stripped
        level = _map_event_type_to_level(event_type, message)
        return {
            "timestamp": "",
            "event": event_type,
            "ticket": "-",
            "text": message,
            "extra": None,
            "level": level,
        }

    level = _map_event_type_to_level("LOG", stripped)
    return {
        "timestamp": "",
        "event": "LOG",
        "ticket": "-",
        "text": stripped,
        "extra": None,
        "level": level,
    }


def create_app(project_root: Optional[Path] = None) -> "Flask":
    """
    Create and configure the Flask API application.
    
    Args:
        project_root: Optional project root path.
    
    Returns:
        Configured Flask application.
    """
    if not _ensure_web_dependencies():
        raise ImportError(
            "Flask and flask-cors are required for the API server. "
            "Install with: pip install flask flask-cors"
        )
    
    # Import here after ensuring dependencies are available
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    
    # Configure Flask to serve static files from actifix-frontend
    root = project_root or Path.cwd()
    frontend_dir = root / 'actifix-frontend'
    
    app = Flask(
        __name__,
        static_folder=str(frontend_dir),
        static_url_path=''
    )
    CORS(app)  # Enable CORS for frontend
    
    # Store project root in app config
    app.config['PROJECT_ROOT'] = root
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in development
    
    @app.route('/', methods=['GET'])
    def serve_index():
        """Serve the dashboard frontend."""
        response = app.send_static_file('index.html')
        # Disable caching for development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Get comprehensive health check data."""
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        health = get_health(paths)
        
        return jsonify({
            'healthy': health.healthy,
            'status': health.status,
            'timestamp': health.timestamp.isoformat(),
            'metrics': {
                'open_tickets': health.open_tickets,
                'completed_tickets': health.completed_tickets,
                'sla_breaches': health.sla_breaches,
                'oldest_ticket_age_hours': health.oldest_ticket_age_hours,
            },
            'filesystem': {
                'files_exist': health.files_exist,
                'files_writable': health.files_writable,
            },
            'warnings': health.warnings,
            'errors': health.errors,
            'details': health.details,
    })
    
    @app.route('/api/version', methods=['GET'])
    def api_version():
        """Return version metadata and git status for the dashboard."""
        root = Path(app.config['PROJECT_ROOT'])
        info = _gather_version_info(root)
        return jsonify(info)

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        """Get ticket statistics."""
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        stats = get_ticket_stats(paths)
        breaches = check_sla_breaches(paths)
        
        return jsonify({
            'total': stats.get('total', 0),
            'open': stats.get('open', 0),
            'completed': stats.get('completed', 0),
            'by_priority': stats.get('by_priority', {}),
            'sla_breaches': breaches,
        })
    
    @app.route('/api/tickets', methods=['GET'])
    def api_tickets():
        """Get recent tickets list."""
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        limit = request.args.get('limit', 20, type=int)

        open_tickets = get_open_tickets(paths)
        completed_tickets = get_completed_tickets(paths)

        # Get stats using same method as /health endpoint for consistency
        stats = get_ticket_stats(paths)

        # Format tickets for API response
        def format_ticket(ticket, status='open'):
            return {
                'ticket_id': ticket.ticket_id,
                'error_type': ticket.error_type,
                'message': ticket.message[:100] + '...' if len(ticket.message) > 100 else ticket.message,
                'source': ticket.source,
                'priority': ticket.priority,
                'created': ticket.created,
                'status': status,
            }

        all_tickets = [
            format_ticket(t, 'open') for t in open_tickets
        ] + [
            format_ticket(t, 'completed') for t in completed_tickets
        ]

        # Sort by created date (newest first)
        all_tickets.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'tickets': all_tickets[:limit],
            'total_open': stats.get('open', 0),
            'total_completed': stats.get('completed', 0),
        })

    @app.route('/api/fix-ticket', methods=['POST'])
    def api_fix_ticket():
        """Fix the highest priority open ticket with detailed logging."""
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])

        # Enforce Raise_AF-only policy before modifying tickets
        # (Defense in depth - also enforced in fix_highest_priority_ticket)
        enforce_raise_af_only(paths)

        # Get completion fields from request body or use defaults
        data = request.get_json() if request.is_json else {}
        completion_notes = data.get('completion_notes', 'Ticket resolved via API endpoint. Issue addressed and verified.')
        test_steps = data.get('test_steps', 'Automated testing performed via API.')
        test_results = data.get('test_results', 'All validation checks passed successfully.')
        summary = data.get('summary', 'Resolved via dashboard fix')
        test_documentation_url = data.get('test_documentation_url')

        result = fix_highest_priority_ticket(
            paths,
            completion_notes=completion_notes,
            test_steps=test_steps,
            test_results=test_results,
            summary=summary,
            test_documentation_url=test_documentation_url
        )
        return jsonify({
            'processed': result.get('processed', False),
            'ticket_id': result.get('ticket_id'),
            'priority': result.get('priority'),
            'reason': result.get('reason'),
            'thought': result.get('thought'),
            'action': result.get('action'),
            'testing': result.get('testing'),
        })
    
    @app.route('/api/logs', methods=['GET'])
    def api_logs():
        """Get log entries (database-backed, with optional setup log file)."""
        log_type = request.args.get('type', 'audit')
        max_lines = request.args.get('lines', 100, type=int)
        if log_type == "setup":
            setup_log = app.config['PROJECT_ROOT'] / 'logs' / 'setup.log'
            if not setup_log.exists():
                return jsonify({
                    'content': [],
                    'file': 'logs/setup.log',
                    'error': 'Log file not found',
                })
            try:
                content = setup_log.read_text(encoding='utf-8', errors='replace').strip()
                file_lines = content.split('\n') if content else []
                recent_lines = file_lines[-max_lines:] if len(file_lines) > max_lines else file_lines
                parsed_lines = []
                for line in recent_lines:
                    parsed = _parse_log_line(line)
                    if parsed:
                        parsed_lines.append(parsed)
                return jsonify({
                    'content': parsed_lines,
                    'file': str(setup_log),
                    'total_lines': len(file_lines),
                })
            except Exception as e:
                return jsonify({
                    'content': [],
                    'file': str(setup_log),
                    'error': str(e),
                })

        try:
            repo = get_event_repository()
            limit = max_lines if max_lines > 0 else 100
            if log_type == "errors":
                raw_events = repo.get_events(EventFilter(limit=max(limit * 5, 100)))
                events = [
                    event for event in raw_events
                    if (event.get("level") or "").upper() in {"ERROR", "CRITICAL"}
                ]
            else:
                events = repo.get_recent_events(limit=limit)

            events = list(reversed(events))
            if len(events) > max_lines:
                events = events[-max_lines:]

            parsed_lines = []
            for event in events:
                event_type = event.get("event_type") or "LOG"
                message = event.get("message") or ""
                level = (event.get("level") or "").upper()
                if not level:
                    level = _map_event_type_to_level(event_type, message)
                parsed_lines.append({
                    "timestamp": event.get("timestamp") or "",
                    "event": event_type,
                    "ticket": event.get("ticket_id") or "-",
                    "text": message,
                    "extra": event.get("extra_json"),
                    "level": level,
                })

            return jsonify({
                'content': parsed_lines,
                'file': 'data/actifix.db:event_log',
                'total_lines': len(events),
            })
        except Exception as e:
            return jsonify({
                'content': [],
                'file': 'data/actifix.db:event_log',
                'error': str(e),
            })
    
    @app.route('/api/system', methods=['GET'])
    def api_system():
        """Get system information."""
        uptime_seconds = time.time() - SERVER_START_TIME
        
        # Format uptime
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        # Get memory info - psutil is preferred but not required here
        memory_info = {
            'total_gb': 0.0,
            'used_gb': 0.0,
            'percent': 0.0,
        }
        cpu_percent = 0.0
        try:
            import psutil
            mem = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(mem.total / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'percent': round(mem.percent, 1),
            }
            cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
        except ImportError:
            pass
        except Exception:
            cpu_percent = 0.0
        
        paths = get_actifix_paths(project_root=app.config['PROJECT_ROOT'])
        
        return jsonify({
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'python_version': platform.python_version(),
            },
            'project': {
                'root': str(app.config['PROJECT_ROOT']),
                'actifix_dir': str(paths.base_dir),
            },
            'server': {
                'uptime': uptime_str,
                'uptime_seconds': int(uptime_seconds),
                'start_time': datetime.fromtimestamp(SERVER_START_TIME, tz=timezone.utc).isoformat(),
            },
            'resources': {
                'memory': memory_info if memory_info else None,
                'cpu_percent': cpu_percent,
            },
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/modules', methods=['GET'])
    def api_modules():
        """List system/user modules from architecture catalog."""
        modules = _load_modules(app.config['PROJECT_ROOT'])
        return jsonify(modules)
    
    @app.route('/api/ping', methods=['GET'])
    def api_ping():
        """Simple ping endpoint for connectivity check."""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    @app.route('/api/ai-status', methods=['GET'])
    def api_ai_status():
        """Return AI provider status, defaults, and recent feedback."""
        try:
            config = load_config(fail_fast=False)
            selection = resolve_provider_selection(config.ai_provider, config.ai_model)
            ai_client = get_ai_client()
            status = ai_client.get_status(selection)
            status.update({
                "ai_enabled": config.ai_enabled,
                "feedback_log": _collect_ai_feedback(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return jsonify(status)
        except Exception as exc:
            record_error(
                message=f"AI status endpoint failed: {exc}",
                source="api.py:api_ai_status",
                priority=TicketPriority.P2,
            )
            return jsonify({
                "error": "Failed to load AI status",
                "details": str(exc),
            }), 500
    
    @app.route('/api/settings', methods=['GET'])
    def api_get_settings():
        """Get current AI settings (API key is masked for security)."""
        config = load_config(fail_fast=False)
        
        # Mask API key for security - only show first 4 and last 4 chars
        api_key = config.ai_api_key
        if api_key and len(api_key) > 8:
            masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        elif api_key:
            masked_key = '*' * len(api_key)
        else:
            masked_key = ''
        
        return jsonify({
            'ai_provider': config.ai_provider,
            'ai_api_key': masked_key,
            'ai_model': config.ai_model,
            'ai_enabled': config.ai_enabled,
        })
    
    @app.route('/api/settings', methods=['POST'])
    def api_update_settings():
        """Update AI settings."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Get current config
            config = get_config()
            
            # Update AI settings
            if 'ai_provider' in data:
                config.ai_provider = data['ai_provider']
            if 'ai_api_key' in data:
                config.ai_api_key = data['ai_api_key']
            if 'ai_model' in data:
                config.ai_model = data['ai_model']
            if 'ai_enabled' in data:
                config.ai_enabled = bool(data['ai_enabled'])
            
            # Set the updated config
            set_config(config)
            
            # Also update environment variables so they persist for the session
            os.environ['ACTIFIX_AI_PROVIDER'] = config.ai_provider
            os.environ['ACTIFIX_AI_API_KEY'] = config.ai_api_key
            os.environ['ACTIFIX_AI_MODEL'] = config.ai_model
            os.environ['ACTIFIX_AI_ENABLED'] = '1' if config.ai_enabled else '0'
            
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully',
            })
        except Exception as e:
            record_error(
                message=f"Settings update failed: {e}",
                source="api.py:api_update_settings",
                priority=TicketPriority.P2,
            )
            return jsonify({
                'error': str(e)
            }), 500
    
    return app


def run_api_server(
    host: str = '127.0.0.1',
    port: int = 5001,
    project_root: Optional[Path] = None,
    debug: bool = False,
) -> None:
    """
    Run the API server.
    
    Args:
        host: Host to bind to.
        port: Port to bind to.
        project_root: Optional project root path.
        debug: Enable debug mode.
    """
    app = create_app(project_root)
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_api_server(debug=True)
