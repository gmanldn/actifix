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

from .ticket_throttler import (
    TicketThrottler,
    TicketThrottleError,
    ThrottleConfig,
    get_ticket_throttler,
    reset_ticket_throttler,
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

from .credentials import (
    CredentialType,
    Credential,
    CredentialStorageError,
    CredentialRetrievalError,
    MacOSKeychain,
    WindowsCredentialManager,
    FileSystemCredentialStore,
    CredentialManager,
    get_credential_manager,
    export_github_deploy_key,
    reset_credential_manager,
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
    'TicketThrottler',
    'TicketThrottleError',
    'ThrottleConfig',
    'get_ticket_throttler',
    'reset_ticket_throttler',
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
    'CredentialType',
    'Credential',
    'CredentialStorageError',
    'CredentialRetrievalError',
    'MacOSKeychain',
    'WindowsCredentialManager',
    'FileSystemCredentialStore',
    'CredentialManager',
    'get_credential_manager',
    'export_github_deploy_key',
    'reset_credential_manager',
]
