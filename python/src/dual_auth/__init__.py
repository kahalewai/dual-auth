"""
dual-auth: Dual-Subject Access Control for AI Agents

A security solution implementing dual-subject access control (AGBAC) for
AI Agents and Humans. This package provides adapters for major IAM providers
and utilities for both in-session and out-of-session agent authorization.

Supported IAM Providers:
- Keycloak
- Auth0
- Okta
- Microsoft EntraID (Azure AD)

Supported Secrets Backends:
- Environment Variables (default)
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- HashiCorp Vault

Author: dual-auth Project
License: Apache 2.0
Version: 1.0.1
"""

__version__ = "1.0.1"
__author__ = "dual-auth Project"
__license__ = "Apache 2.0"

from .config import (
    get_config,
    get_vendor,
    get_secrets_backend_type,
    ConfigurationError,
    SecretsBackendError
)

from .adapters import (
    BaseAdapter,
    TokenResponse,
    TokenRequestError,
    validate_adapter_config,
    KeycloakAdapter,
    Auth0Adapter,
    OktaAdapter,
    EntraIDAdapter
)

from .session import (
    HybridSender,
    UserSession,
    InSessionTokenRequest,
    OutOfSessionTokenRequest
)

from .api import (
    InSessionAPICall,
    OutOfSessionAPICall
)

__all__ = [
    '__version__',
    '__author__',
    '__license__',
    'get_config',
    'get_vendor',
    'get_secrets_backend_type',
    'ConfigurationError',
    'SecretsBackendError',
    'BaseAdapter',
    'TokenResponse',
    'TokenRequestError',
    'validate_adapter_config',
    'KeycloakAdapter',
    'Auth0Adapter',
    'OktaAdapter',
    'EntraIDAdapter',
    'HybridSender',
    'UserSession',
    'InSessionTokenRequest',
    'OutOfSessionTokenRequest',
    'InSessionAPICall',
    'OutOfSessionAPICall'
]
