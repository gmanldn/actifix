"""
Actifix Configuration - Centralized configuration management.

Provides validated configuration with fail-fast behavior on invalid state.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from .state_paths import ActifixPaths, get_actifix_paths


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
    ai_provider: str = "openai"  # openai, anthropic, google, openrouter, ollama
    ai_api_key: str = ""
    ai_model: str = ""  # e.g., gpt-4, claude-3-sonnet, gemini-pro
    ai_enabled: bool = False


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
        project_root = Path(os.environ.get(
            "ACTIFIX_PROJECT_ROOT",
            os.getcwd()
        ))
    project_root = Path(project_root).resolve()
    
    # Get paths
    paths = get_actifix_paths(project_root=project_root)
    
    # Load from environment
    config = ActifixConfig(
        project_root=project_root,
        paths=paths,
        
        capture_enabled=_parse_bool(
            os.environ.get("ACTIFIX_CAPTURE_ENABLED", "1")
        ),
        max_rollup_errors=_parse_int(
            os.environ.get("ACTIFIX_MAX_ROLLUP_ERRORS", ""), 20
        ),
        secret_redaction_enabled=_parse_bool(
            os.environ.get("ACTIFIX_SECRET_REDACTION", "1")
        ),
        
        sla_p0_hours=_parse_int(
            os.environ.get("ACTIFIX_SLA_P0_HOURS", ""), 1
        ),
        sla_p1_hours=_parse_int(
            os.environ.get("ACTIFIX_SLA_P1_HOURS", ""), 4
        ),
        sla_p2_hours=_parse_int(
            os.environ.get("ACTIFIX_SLA_P2_HOURS", ""), 24
        ),
        sla_p3_hours=_parse_int(
            os.environ.get("ACTIFIX_SLA_P3_HOURS", ""), 72
        ),
        
        max_log_size_bytes=_parse_int(
            os.environ.get("ACTIFIX_MAX_LOG_SIZE", ""), 10 * 1024 * 1024
        ),
        max_list_entries=_parse_int(
            os.environ.get("ACTIFIX_MAX_LIST_ENTRIES", ""), 1000
        ),
        
        min_coverage_percent=_parse_float(
            os.environ.get("ACTIFIX_MIN_COVERAGE", ""), 80.0
        ),
        test_timeout_seconds=_parse_float(
            os.environ.get("ACTIFIX_TEST_TIMEOUT", ""), 300.0
        ),
        
        dispatch_enabled=_parse_bool(
            os.environ.get("ACTIFIX_DISPATCH_ENABLED", "1")
        ),
        max_dispatch_retries=_parse_int(
            os.environ.get("ACTIFIX_DISPATCH_RETRIES", ""), 3
        ),
        dispatch_timeout_seconds=_parse_float(
            os.environ.get("ACTIFIX_DISPATCH_TIMEOUT", ""), 600.0
        ),
        
        health_check_interval_seconds=_parse_float(
            os.environ.get("ACTIFIX_HEALTH_INTERVAL", ""), 60.0
        ),
        stale_lock_timeout_seconds=_parse_float(
            os.environ.get("ACTIFIX_STALE_LOCK_TIMEOUT", ""), 300.0
        ),
        
        ai_provider=os.environ.get("ACTIFIX_AI_PROVIDER", "openai"),
        ai_api_key=os.environ.get("ACTIFIX_AI_API_KEY", ""),
        ai_model=os.environ.get("ACTIFIX_AI_MODEL", ""),
        ai_enabled=_parse_bool(os.environ.get("ACTIFIX_AI_ENABLED", "0")),
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
