"""
Actifix Configuration - Centralized configuration management.

Provides validated configuration with fail-fast behavior on invalid state.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from .state_paths import ActifixPaths, get_actifix_paths


def _sanitize_env_value(value: Optional[str], value_type: str = "string") -> str:
    """
    Sanitize environment variable values to prevent injection attacks.

    Args:
        value: The environment variable value to sanitize.
        value_type: Type of value - 'string', 'path', 'alphanumeric', 'numeric', 'identifier'.

    Returns:
        Sanitized value with whitespace trimmed and dangerous characters handled.
    """
    if not value:
        return ""

    # Always strip leading/trailing whitespace
    value = value.strip()

    if value_type == "path":
        # For paths: allow alphanumeric, /, \, -, _, ., ~
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x1f\x7f]', '', value)
        # Collapse multiple slashes
        value = re.sub(r'/+', '/', value)
        return value

    elif value_type == "alphanumeric":
        # Only alphanumeric, underscore, hyphen, dot
        return re.sub(r'[^a-zA-Z0-9_\-.]', '', value)

    elif value_type == "numeric":
        # Only digits (will be parsed as number later)
        return re.sub(r'[^\d\-.]', '', value)

    elif value_type == "identifier":
        # Valid Python identifiers: alphanumeric, underscore (no starting digit)
        return re.sub(r'[^a-zA-Z0-9_]', '', value)

    elif value_type == "boolean":
        # Boolean values - only accept specific words
        return value.lower() if value.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off") else ""

    else:  # "string"
        # For general strings: remove null bytes and control characters
        return re.sub(r'[\x00-\x1f\x7f]', '', value)


def _get_env_sanitized(key: str, default: str = "", value_type: str = "string") -> str:
    """
    Get environment variable value with sanitization.

    Args:
        key: Environment variable name.
        default: Default value if not found.
        value_type: Type of value for sanitization.

    Returns:
        Sanitized environment variable value.
    """
    value = os.environ.get(key, default)
    return _sanitize_env_value(value, value_type)


@dataclass
class ActifixConfig:
    """Actifix system configuration."""
    
    # Paths
    project_root: Path
    paths: ActifixPaths
    
    # Error capture
    capture_enabled: bool = True
    max_rollup_errors: int = 20
    secret_redaction_enabled: bool = True
    
    # SLA thresholds (hours)
    sla_p0_hours: int = 1
    sla_p1_hours: int = 4
    sla_p2_hours: int = 24
    sla_p3_hours: int = 72
    
    # File limits
    max_log_size_bytes: int = 10 * 1024 * 1024  # 10MB
    max_list_entries: int = 1000

    # Ticket limits
    max_ticket_message_length: int = 5000  # Characters
    max_file_context_size_bytes: int = 1 * 1024 * 1024  # 1MB
    max_open_tickets: int = 10000

    # Ticket throttling
    ticket_throttling_enabled: bool = True
    max_p2_tickets_per_hour: int = 15
    max_p3_tickets_per_4h: int = 5
    max_p4_tickets_per_day: int = 2
    emergency_ticket_threshold: int = 200
    emergency_window_minutes: int = 1

    # Testing
    min_coverage_percent: float = 80.0
    test_timeout_seconds: float = 300.0
    
    # AI dispatch
    dispatch_enabled: bool = True
    max_dispatch_retries: int = 3
    dispatch_timeout_seconds: float = 600.0
    
    # Health checks
    health_check_interval_seconds: float = 60.0
    stale_lock_timeout_seconds: float = 300.0
    
    # AI Integration
    ai_provider: str = "openrouter"  # OpenRouter for Mimo 2 with thinking
    ai_api_key: str = ""  # Set your OPENROUTER_API_KEY environment variable
    ai_model: str = "xiaomi/mimo-v2-flash"  # Mimo 2 via OpenRouter with thinking support
    ollama_model: str = "codellama:7b"  # Default Ollama model
    ai_enabled: bool = True  # AI dispatch enabled by default


def _parse_bool(value: str) -> bool:
    """Parse boolean from string."""
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: str, default: int) -> int:
    """Parse integer from string with default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_float(value: str, default: float) -> float:
    """Parse float from string with default."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_config(
    project_root: Optional[Path] = None,
    config_file: Optional[Path] = None,
    fail_fast: bool = True,
) -> ActifixConfig:
    """
    Load Actifix configuration from environment and optional file.
    
    Configuration priority (highest to lowest):
    1. Environment variables (ACTIFIX_*)
    2. Config file (if provided)
    3. Defaults
    
    Args:
        project_root: Project root directory.
        config_file: Optional config file path.
        fail_fast: Raise on invalid config if True.
    
    Returns:
        Validated ActifixConfig.
    
    Raises:
        ValueError: If config is invalid and fail_fast=True.
    """
    # Determine project root
    if project_root is None:
        project_root = Path(_get_env_sanitized(
            "ACTIFIX_PROJECT_ROOT",
            os.getcwd(),
            value_type="path"
        ))
    project_root = Path(project_root).resolve()

    # Get paths
    paths = get_actifix_paths(project_root=project_root)

    # Load from environment
    config = ActifixConfig(
        project_root=project_root,
        paths=paths,

        capture_enabled=_parse_bool(
            _get_env_sanitized("ACTIFIX_CAPTURE_ENABLED", "1", value_type="boolean")
        ),
        max_rollup_errors=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_ROLLUP_ERRORS", "", value_type="numeric"), 20
        ),
        secret_redaction_enabled=_parse_bool(
            _get_env_sanitized("ACTIFIX_SECRET_REDACTION", "1", value_type="boolean")
        ),

        sla_p0_hours=_parse_int(
            _get_env_sanitized("ACTIFIX_SLA_P0_HOURS", "", value_type="numeric"), 1
        ),
        sla_p1_hours=_parse_int(
            _get_env_sanitized("ACTIFIX_SLA_P1_HOURS", "", value_type="numeric"), 4
        ),
        sla_p2_hours=_parse_int(
            _get_env_sanitized("ACTIFIX_SLA_P2_HOURS", "", value_type="numeric"), 24
        ),
        sla_p3_hours=_parse_int(
            _get_env_sanitized("ACTIFIX_SLA_P3_HOURS", "", value_type="numeric"), 72
        ),

        max_log_size_bytes=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_LOG_SIZE", "", value_type="numeric"), 10 * 1024 * 1024
        ),
        max_list_entries=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_LIST_ENTRIES", "", value_type="numeric"), 1000
        ),

        max_ticket_message_length=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_MESSAGE_LENGTH", "", value_type="numeric"), 5000
        ),
        max_file_context_size_bytes=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_FILE_CONTEXT_BYTES", "", value_type="numeric"), 1 * 1024 * 1024
        ),
        max_open_tickets=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_OPEN_TICKETS", "", value_type="numeric"), 10000
        ),
        ticket_throttling_enabled=_parse_bool(
            _get_env_sanitized("ACTIFIX_TICKET_THROTTLING_ENABLED", "1", value_type="boolean")
        ),
        max_p2_tickets_per_hour=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_P2_TICKETS_PER_HOUR", "", value_type="numeric"), 15
        ),
        max_p3_tickets_per_4h=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_P3_TICKETS_PER_4H", "", value_type="numeric"), 5
        ),
        max_p4_tickets_per_day=_parse_int(
            _get_env_sanitized("ACTIFIX_MAX_P4_TICKETS_PER_DAY", "", value_type="numeric"), 2
        ),
        emergency_ticket_threshold=_parse_int(
            _get_env_sanitized("ACTIFIX_EMERGENCY_TICKET_THRESHOLD", "", value_type="numeric"), 200
        ),
        emergency_window_minutes=_parse_int(
            _get_env_sanitized("ACTIFIX_EMERGENCY_WINDOW_MINUTES", "", value_type="numeric"), 1
        ),

        min_coverage_percent=_parse_float(
            _get_env_sanitized("ACTIFIX_MIN_COVERAGE", "", value_type="numeric"), 80.0
        ),
        test_timeout_seconds=_parse_float(
            _get_env_sanitized("ACTIFIX_TEST_TIMEOUT", "", value_type="numeric"), 300.0
        ),

        dispatch_enabled=_parse_bool(
            _get_env_sanitized("ACTIFIX_DISPATCH_ENABLED", "1", value_type="boolean")
        ),
        max_dispatch_retries=_parse_int(
            _get_env_sanitized("ACTIFIX_DISPATCH_RETRIES", "", value_type="numeric"), 3
        ),
        dispatch_timeout_seconds=_parse_float(
            _get_env_sanitized("ACTIFIX_DISPATCH_TIMEOUT", "", value_type="numeric"), 600.0
        ),

        health_check_interval_seconds=_parse_float(
            _get_env_sanitized("ACTIFIX_HEALTH_INTERVAL", "", value_type="numeric"), 60.0
        ),
        stale_lock_timeout_seconds=_parse_float(
            _get_env_sanitized("ACTIFIX_STALE_LOCK_TIMEOUT", "", value_type="numeric"), 300.0
        ),

        ai_provider=_get_env_sanitized("ACTIFIX_AI_PROVIDER", "mimo-flash-v2-free", value_type="alphanumeric"),
        ai_api_key=_get_env_sanitized("ACTIFIX_AI_API_KEY", "", value_type="string"),
        ai_model=_get_env_sanitized("ACTIFIX_AI_MODEL", "mimo-flash-v2-free", value_type="alphanumeric"),
        ollama_model=_get_env_sanitized("ACTIFIX_OLLAMA_MODEL", "codellama:7b", value_type="alphanumeric"),
        ai_enabled=_parse_bool(_get_env_sanitized("ACTIFIX_AI_ENABLED", "0", value_type="boolean")),
    )
    
    # Validate configuration
    errors = validate_config(config)
    if errors and fail_fast:
        raise ValueError(
            f"Invalid configuration:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    
    return config


def validate_config(config: ActifixConfig) -> list[str]:
    """
    Validate configuration values.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Check project root exists
    if not config.project_root.exists():
        errors.append(f"Project root does not exist: {config.project_root}")
    
    # Check SLA values are positive
    if config.sla_p0_hours <= 0:
        errors.append("SLA P0 hours must be positive")
    if config.sla_p1_hours <= 0:
        errors.append("SLA P1 hours must be positive")
    if config.sla_p2_hours <= 0:
        errors.append("SLA P2 hours must be positive")
    if config.sla_p3_hours <= 0:
        errors.append("SLA P3 hours must be positive")
    
    # Check SLA ordering
    if config.sla_p0_hours >= config.sla_p1_hours:
        errors.append("SLA P0 should be less than P1")
    if config.sla_p1_hours >= config.sla_p2_hours:
        errors.append("SLA P1 should be less than P2")
    if config.sla_p2_hours >= config.sla_p3_hours:
        errors.append("SLA P2 should be less than P3")
    
    # Check coverage is valid
    if not 0 <= config.min_coverage_percent <= 100:
        errors.append("Min coverage must be between 0 and 100")
    
    # Check sizes are positive
    if config.max_log_size_bytes <= 0:
        errors.append("Max log size must be positive")
    if config.max_list_entries <= 0:
        errors.append("Max list entries must be positive")

    # Check ticket limits are positive and reasonable
    if config.max_ticket_message_length <= 0:
        errors.append("Max ticket message length must be positive")
    if config.max_ticket_message_length > 1000000:
        errors.append("Max ticket message length must be <= 1MB")
    if config.max_file_context_size_bytes <= 0:
        errors.append("Max file context size must be positive")
    if config.max_file_context_size_bytes > 100 * 1024 * 1024:
        errors.append("Max file context size must be <= 100MB")
    if config.max_open_tickets <= 0:
        errors.append("Max open tickets must be positive")
    if config.max_p2_tickets_per_hour <= 0:
        errors.append("Max P2 tickets per hour must be positive")
    if config.max_p3_tickets_per_4h <= 0:
        errors.append("Max P3 tickets per 4 hours must be positive")
    if config.max_p4_tickets_per_day <= 0:
        errors.append("Max P4 tickets per day must be positive")
    if config.emergency_ticket_threshold <= 0:
        errors.append("Emergency ticket threshold must be positive")
    if config.emergency_window_minutes <= 0:
        errors.append("Emergency window minutes must be positive")

    # Check timeouts are positive
    if config.test_timeout_seconds <= 0:
        errors.append("Test timeout must be positive")
    if config.dispatch_timeout_seconds <= 0:
        errors.append("Dispatch timeout must be positive")
    
    return errors


# Global config instance
_config: Optional[ActifixConfig] = None


def get_config() -> ActifixConfig:
    """
    Get the global configuration instance.
    
    Loads with defaults if not explicitly initialized.
    """
    global _config
    if _config is None:
        _config = load_config(fail_fast=False)
    return _config


def set_config(config: ActifixConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to None."""
    global _config
    _config = None