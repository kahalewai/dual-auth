"""
dual-auth Adapters

IAM vendor adapters for dual-subject token requests.

Author: dual-auth Project
License: Apache 2.0
Version: 1.0.1
"""

from .base_adapter import BaseAdapter, TokenResponse, TokenRequestError, validate_adapter_config
from .keycloak_adapter import KeycloakAdapter
from .auth0_adapter import Auth0Adapter
from .okta_adapter import OktaAdapter
from .entraid_adapter import EntraIDAdapter

__all__ = [
    'BaseAdapter',
    'TokenResponse',
    'TokenRequestError',
    'validate_adapter_config',
    'KeycloakAdapter',
    'Auth0Adapter',
    'OktaAdapter',
    'EntraIDAdapter'
]
