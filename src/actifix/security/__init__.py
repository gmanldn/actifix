"""Security utilities for Actifix."""

from .secrets_scanner import (
    SecretsScanner,
    SecretMatch,
    scan_git_staged_files,
    format_scan_results,
)

from .rate_limiter import (
    RateLimiter,
    RateLimitError,
    RateLimitConfig,
    APICall,
    get_rate_limiter,
    reset_rate_limiter,
)

from .auth import (
    AuthRole,
    AuthUser,
    AuthToken,
    AuthenticationError,
    AuthorizationError,
    TokenManager,
    UserManager,
    AuthorizationManager,
    get_token_manager,
    get_user_manager,
    get_authorization_manager,
    reset_auth_managers,
)

__all__ = [
    'SecretsScanner',
    'SecretMatch',
    'scan_git_staged_files',
    'format_scan_results',
    'RateLimiter',
    'RateLimitError',
    'RateLimitConfig',
    'APICall',
    'get_rate_limiter',
    'reset_rate_limiter',
    'AuthRole',
    'AuthUser',
    'AuthToken',
    'AuthenticationError',
    'AuthorizationError',
    'TokenManager',
    'UserManager',
    'AuthorizationManager',
    'get_token_manager',
    'get_user_manager',
    'get_authorization_manager',
    'reset_auth_managers',
]
