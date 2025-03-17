"""
Authentication configuration system for web scraping.
Provides secure credential storage and flexible authentication handlers.
"""

from .config import (
    AuthConfig,
    BasicAuthConfig,
    FormAuthConfig,
    TokenAuthConfig,
    AuthConfigManager
)
from .handlers import (
    AuthHandler,
    BasicAuthHandler,
    FormAuthHandler,
    TokenAuthHandler,
    create_auth_handler
)
from .storage import CredentialManager
from .utils import (
    extract_csrf_token,
    verify_ssl_cert,
    extract_form_fields,
    parse_token_response,
    validate_auth_response,
    sanitize_auth_data
)

__all__ = [
    # Config classes
    'AuthConfig',
    'BasicAuthConfig',
    'FormAuthConfig',
    'TokenAuthConfig',
    'AuthConfigManager',
    
    # Handler classes
    'AuthHandler',
    'BasicAuthHandler',
    'FormAuthHandler',
    'TokenAuthHandler',
    'create_auth_handler',
    
    # Storage
    'CredentialManager',
    
    # Utilities
    'extract_csrf_token',
    'verify_ssl_cert',
    'extract_form_fields',
    'parse_token_response',
    'validate_auth_response',
    'sanitize_auth_data'
]

__version__ = '0.1.0'
