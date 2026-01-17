"""
dual-auth Configuration Module

Centralized configuration loading for all IAM vendors with pluggable secrets backends.
This module provides a simple interface to load dual-auth configuration from multiple
secrets management sources, supporting both development (environment variables) and
production (cloud secrets managers) scenarios.

Supported Secrets Backends:
- Environment Variables (default, for development/testing)
- AWS Secrets Manager (for AWS production deployments)
- GCP Secret Manager (for GCP production deployments)
- Azure Key Vault (for Azure production deployments)
- HashiCorp Vault (for multi-cloud/on-premises production deployments)

Supported IAM Vendors:
- Keycloak
- Auth0
- Okta
- Microsoft EntraID (Azure AD)

Security Features:
- All secrets loaded from configured backend (never hardcoded)
- HTTPS validation for all URLs
- URL format validation
- File existence and permission validation
- Comprehensive input validation
- Structured error messages with examples
- Secrets cached in memory only (never written to disk)

Author: kahalewai (https://www.github.com/kahalewai)
License: Apache 2.0
Version: 1.0.1
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from urllib.parse import urlparse

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ConfigurationError(Exception):
    """
    Exception raised when configuration is invalid or incomplete.
    
    This specific exception type distinguishes configuration errors from other
    types of errors, enabling precise error handling in applications.
    """
    pass


class SecretsBackendError(Exception):
    """
    Exception raised when secrets backend operations fail.
    
    This exception wraps underlying backend errors (AWS, GCP, Azure, Vault)
    to provide consistent error handling across all backends.
    """
    def __init__(self, message: str, backend: str, original_error: Exception = None):
        super().__init__(message)
        self.backend = backend
        self.original_error = original_error


# =============================================================================
# SECRETS BACKEND ABSTRACT BASE CLASS
# =============================================================================

class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""
    
    @abstractmethod
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Retrieve a secret value by key."""
        pass
    
    @abstractmethod
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Retrieve a secret value as JSON/dictionary."""
        pass
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of this backend for logging/error messages."""
        pass


# =============================================================================
# ENVIRONMENT VARIABLES BACKEND (Default)
# =============================================================================

class EnvironmentSecretsBackend(SecretsBackend):
    """
    Secrets backend that reads from environment variables.
    
    This is the default backend, suitable for development, testing, and
    simple deployments.
    """
    
    @property
    def backend_name(self) -> str:
        return "environment"
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Get secret from environment variable."""
        value = os.getenv(key, '').strip()
        
        if not value:
            if required:
                raise SecretsBackendError(
                    f"Environment variable '{key}' is required but not set or empty. "
                    f"Example: export {key}=your-value-here",
                    backend=self.backend_name
                )
            return None
        
        return value
    
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Get secret from environment variable and parse as JSON."""
        value = self.get_secret(key, required)
        
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise SecretsBackendError(
                f"Environment variable '{key}' contains invalid JSON: {e}",
                backend=self.backend_name,
                original_error=e
            )


# =============================================================================
# AWS SECRETS MANAGER BACKEND
# =============================================================================

class AWSSecretsBackend(SecretsBackend):
    """
    Secrets backend that reads from AWS Secrets Manager.
    
    Requires boto3: pip install boto3
    
    Configuration Environment Variables:
        DUAL_AUTH_AWS_REGION: AWS region (default: us-east-1)
        DUAL_AUTH_AWS_SECRET_PREFIX: Prefix for secret names (default: dual-auth/)
    """
    
    def __init__(self):
        """Initialize AWS Secrets Manager client."""
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
            self._boto3 = boto3
            self._BotoCoreError = BotoCoreError
            self._ClientError = ClientError
        except ImportError:
            raise SecretsBackendError(
                "AWS Secrets Manager backend requires boto3. "
                "Install with: pip install boto3",
                backend="aws"
            )
        
        self._region = os.getenv('DUAL_AUTH_AWS_REGION', 'us-east-1')
        self._prefix = os.getenv('DUAL_AUTH_AWS_SECRET_PREFIX', 'dual-auth/')
        
        try:
            self._client = boto3.client('secretsmanager', region_name=self._region)
            logger.info("AWS Secrets Manager backend initialized",
                       extra={'region': self._region, 'prefix': self._prefix})
        except Exception as e:
            raise SecretsBackendError(
                f"Failed to initialize AWS Secrets Manager client: {e}",
                backend="aws", original_error=e
            )
    
    @property
    def backend_name(self) -> str:
        return "aws"
    
    def _get_secret_name(self, key: str) -> str:
        """Build full secret name with prefix."""
        if key.startswith(self._prefix):
            return key
        return f"{self._prefix}{key}"
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        secret_name = self._get_secret_name(key)
        
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                return response['SecretString']
            else:
                import base64
                return base64.b64decode(response['SecretBinary']).decode('utf-8')
                
        except self._ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            if error_code == 'ResourceNotFoundException':
                if required:
                    raise SecretsBackendError(
                        f"AWS secret '{secret_name}' not found in region '{self._region}'.",
                        backend=self.backend_name, original_error=e
                    )
                return None
            elif error_code == 'AccessDeniedException':
                raise SecretsBackendError(
                    f"Access denied to AWS secret '{secret_name}'.",
                    backend=self.backend_name, original_error=e
                )
            else:
                raise SecretsBackendError(
                    f"AWS Secrets Manager error: {error_code}",
                    backend=self.backend_name, original_error=e
                )
        except self._BotoCoreError as e:
            raise SecretsBackendError(
                f"AWS connection error: {e}",
                backend=self.backend_name, original_error=e
            )
    
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Get secret from AWS Secrets Manager and parse as JSON."""
        value = self.get_secret(key, required)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise SecretsBackendError(
                f"AWS secret '{key}' contains invalid JSON: {e}",
                backend=self.backend_name, original_error=e
            )


# =============================================================================
# GCP SECRET MANAGER BACKEND
# =============================================================================

class GCPSecretsBackend(SecretsBackend):
    """
    Secrets backend that reads from Google Cloud Secret Manager.
    
    Requires: pip install google-cloud-secret-manager
    
    Configuration Environment Variables:
        DUAL_AUTH_GCP_PROJECT: GCP project ID (required)
        DUAL_AUTH_GCP_SECRET_PREFIX: Prefix for secret names (default: dual-auth-)
    """
    
    def __init__(self):
        """Initialize GCP Secret Manager client."""
        try:
            from google.cloud import secretmanager
            from google.api_core import exceptions as gcp_exceptions
            self._secretmanager = secretmanager
            self._gcp_exceptions = gcp_exceptions
        except ImportError:
            raise SecretsBackendError(
                "GCP Secret Manager backend requires google-cloud-secret-manager. "
                "Install with: pip install google-cloud-secret-manager",
                backend="gcp"
            )
        
        self._project = os.getenv('DUAL_AUTH_GCP_PROJECT', '').strip()
        self._prefix = os.getenv('DUAL_AUTH_GCP_SECRET_PREFIX', 'dual-auth-')
        
        if not self._project:
            raise SecretsBackendError(
                "DUAL_AUTH_GCP_PROJECT environment variable is required for GCP backend.",
                backend="gcp"
            )
        
        try:
            self._client = secretmanager.SecretManagerServiceClient()
            logger.info("GCP Secret Manager backend initialized",
                       extra={'project': self._project, 'prefix': self._prefix})
        except Exception as e:
            raise SecretsBackendError(
                f"Failed to initialize GCP Secret Manager client: {e}",
                backend="gcp", original_error=e
            )
    
    @property
    def backend_name(self) -> str:
        return "gcp"
    
    def _normalize_secret_name(self, key: str) -> str:
        """Normalize key to valid GCP secret name."""
        normalized = key.replace('_', '-').lower()
        if not normalized.startswith(self._prefix.lower()):
            normalized = f"{self._prefix}{normalized}"
        return normalized
    
    def _build_secret_path(self, secret_name: str, version: str = "latest") -> str:
        """Build full secret resource path."""
        return f"projects/{self._project}/secrets/{secret_name}/versions/{version}"
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Get secret from GCP Secret Manager."""
        secret_name = self._normalize_secret_name(key)
        secret_path = self._build_secret_path(secret_name)
        
        try:
            response = self._client.access_secret_version(name=secret_path)
            return response.payload.data.decode('utf-8')
        except self._gcp_exceptions.NotFound:
            if required:
                raise SecretsBackendError(
                    f"GCP secret '{secret_name}' not found in project '{self._project}'.",
                    backend=self.backend_name
                )
            return None
        except self._gcp_exceptions.PermissionDenied as e:
            raise SecretsBackendError(
                f"Permission denied accessing GCP secret '{secret_name}'.",
                backend=self.backend_name, original_error=e
            )
        except Exception as e:
            raise SecretsBackendError(
                f"GCP Secret Manager error: {e}",
                backend=self.backend_name, original_error=e
            )
    
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Get secret from GCP Secret Manager and parse as JSON."""
        value = self.get_secret(key, required)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise SecretsBackendError(
                f"GCP secret '{key}' contains invalid JSON: {e}",
                backend=self.backend_name, original_error=e
            )


# =============================================================================
# AZURE KEY VAULT BACKEND
# =============================================================================

class AzureSecretsBackend(SecretsBackend):
    """
    Secrets backend that reads from Azure Key Vault.
    
    Requires: pip install azure-identity azure-keyvault-secrets
    
    Configuration Environment Variables:
        DUAL_AUTH_AZURE_VAULT_URL: Key Vault URL (required)
        DUAL_AUTH_AZURE_SECRET_PREFIX: Prefix for secret names (default: dual-auth-)
    """
    
    def __init__(self):
        """Initialize Azure Key Vault client."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            from azure.core.exceptions import (
                ResourceNotFoundError, ClientAuthenticationError, HttpResponseError
            )
            self._DefaultAzureCredential = DefaultAzureCredential
            self._SecretClient = SecretClient
            self._ResourceNotFoundError = ResourceNotFoundError
            self._ClientAuthenticationError = ClientAuthenticationError
            self._HttpResponseError = HttpResponseError
        except ImportError:
            raise SecretsBackendError(
                "Azure Key Vault backend requires azure-identity and azure-keyvault-secrets. "
                "Install with: pip install azure-identity azure-keyvault-secrets",
                backend="azure"
            )
        
        self._vault_url = os.getenv('DUAL_AUTH_AZURE_VAULT_URL', '').strip()
        self._prefix = os.getenv('DUAL_AUTH_AZURE_SECRET_PREFIX', 'dual-auth-')
        
        if not self._vault_url:
            raise SecretsBackendError(
                "DUAL_AUTH_AZURE_VAULT_URL environment variable is required for Azure backend.",
                backend="azure"
            )
        
        try:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self._vault_url, credential=credential)
            logger.info("Azure Key Vault backend initialized",
                       extra={'vault_url': self._vault_url, 'prefix': self._prefix})
        except self._ClientAuthenticationError as e:
            raise SecretsBackendError(
                f"Azure authentication failed: {e}",
                backend="azure", original_error=e
            )
        except Exception as e:
            raise SecretsBackendError(
                f"Failed to initialize Azure Key Vault client: {e}",
                backend="azure", original_error=e
            )
    
    @property
    def backend_name(self) -> str:
        return "azure"
    
    def _normalize_secret_name(self, key: str) -> str:
        """Normalize key to valid Azure Key Vault secret name."""
        normalized = key.replace('_', '-').lower()
        if not normalized.startswith(self._prefix.lower()):
            normalized = f"{self._prefix}{normalized}"
        return normalized
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Get secret from Azure Key Vault."""
        secret_name = self._normalize_secret_name(key)
        
        try:
            secret = self._client.get_secret(secret_name)
            return secret.value
        except self._ResourceNotFoundError:
            if required:
                raise SecretsBackendError(
                    f"Azure Key Vault secret '{secret_name}' not found.",
                    backend=self.backend_name
                )
            return None
        except self._ClientAuthenticationError as e:
            raise SecretsBackendError(
                f"Azure authentication failed accessing secret '{secret_name}'.",
                backend=self.backend_name, original_error=e
            )
        except self._HttpResponseError as e:
            raise SecretsBackendError(
                f"Azure Key Vault error: {e.message}",
                backend=self.backend_name, original_error=e
            )
        except Exception as e:
            raise SecretsBackendError(
                f"Azure Key Vault error: {e}",
                backend=self.backend_name, original_error=e
            )
    
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Get secret from Azure Key Vault and parse as JSON."""
        value = self.get_secret(key, required)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise SecretsBackendError(
                f"Azure secret '{key}' contains invalid JSON: {e}",
                backend=self.backend_name, original_error=e
            )


# =============================================================================
# HASHICORP VAULT BACKEND
# =============================================================================

class VaultSecretsBackend(SecretsBackend):
    """
    Secrets backend that reads from HashiCorp Vault.
    
    Requires: pip install hvac
    
    Configuration Environment Variables:
        VAULT_ADDR: Vault server URL (required)
        VAULT_TOKEN: Authentication token (for token auth)
        VAULT_ROLE_ID: AppRole role ID (for AppRole auth)
        VAULT_SECRET_ID: AppRole secret ID (for AppRole auth)
        VAULT_NAMESPACE: Vault namespace (for Vault Enterprise)
        DUAL_AUTH_VAULT_MOUNT: Secrets engine mount point (default: secret)
        DUAL_AUTH_VAULT_PATH_PREFIX: Path prefix for secrets (default: dual-auth/)
    """
    
    def __init__(self):
        """Initialize HashiCorp Vault client."""
        try:
            import hvac
            self._hvac = hvac
        except ImportError:
            raise SecretsBackendError(
                "HashiCorp Vault backend requires hvac. "
                "Install with: pip install hvac",
                backend="vault"
            )
        
        self._vault_addr = os.getenv('VAULT_ADDR', '').strip()
        self._namespace = os.getenv('VAULT_NAMESPACE', '').strip() or None
        self._mount = os.getenv('DUAL_AUTH_VAULT_MOUNT', 'secret')
        self._prefix = os.getenv('DUAL_AUTH_VAULT_PATH_PREFIX', 'dual-auth/')
        
        if not self._vault_addr:
            raise SecretsBackendError(
                "VAULT_ADDR environment variable is required for Vault backend.",
                backend="vault"
            )
        
        try:
            self._client = hvac.Client(url=self._vault_addr, namespace=self._namespace)
            self._authenticate()
            
            if not self._client.is_authenticated():
                raise SecretsBackendError(
                    "Vault authentication failed. Check credentials.",
                    backend="vault"
                )
            
            logger.info("HashiCorp Vault backend initialized",
                       extra={'vault_addr': self._vault_addr, 'mount': self._mount})
        except SecretsBackendError:
            raise
        except Exception as e:
            raise SecretsBackendError(
                f"Failed to initialize Vault client: {e}",
                backend="vault", original_error=e
            )
    
    def _authenticate(self):
        """Authenticate to Vault using available credentials."""
        # Method 1: Token authentication
        token = os.getenv('VAULT_TOKEN', '').strip()
        if token:
            self._client.token = token
            logger.debug("Vault: Using token authentication")
            return
        
        # Method 2: AppRole authentication
        role_id = os.getenv('VAULT_ROLE_ID', '').strip()
        secret_id = os.getenv('VAULT_SECRET_ID', '').strip()
        if role_id and secret_id:
            try:
                response = self._client.auth.approle.login(role_id=role_id, secret_id=secret_id)
                self._client.token = response['auth']['client_token']
                logger.debug("Vault: Using AppRole authentication")
                return
            except Exception as e:
                raise SecretsBackendError(
                    f"Vault AppRole authentication failed: {e}",
                    backend="vault", original_error=e
                )
        
        # Method 3: Kubernetes authentication (auto-detect)
        k8s_token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        if os.path.exists(k8s_token_path):
            try:
                with open(k8s_token_path, 'r') as f:
                    jwt = f.read()
                role = os.getenv('VAULT_K8S_ROLE', 'dual-auth')
                response = self._client.auth.kubernetes.login(role=role, jwt=jwt)
                self._client.token = response['auth']['client_token']
                logger.debug("Vault: Using Kubernetes authentication")
                return
            except Exception as e:
                logger.debug(f"Vault: Kubernetes auth failed: {e}")
        
        raise SecretsBackendError(
            "No Vault authentication credentials found. Set VAULT_TOKEN, "
            "or VAULT_ROLE_ID and VAULT_SECRET_ID, or run in Kubernetes.",
            backend="vault"
        )
    
    @property
    def backend_name(self) -> str:
        return "vault"
    
    def _normalize_secret_path(self, key: str) -> str:
        """Normalize key to Vault path format."""
        normalized = key.replace('_', '-').lower()
        if not normalized.startswith(self._prefix.lower().rstrip('/')):
            normalized = f"{self._prefix}{normalized}"
        return normalized
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        secret_path = self._normalize_secret_path(key)
        
        try:
            # Try KV v2 first
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    path=secret_path, mount_point=self._mount
                )
                data = response['data']['data']
                if 'value' in data and len(data) == 1:
                    return data['value']
                return json.dumps(data)
            except self._hvac.exceptions.InvalidPath:
                # Try KV v1
                response = self._client.secrets.kv.v1.read_secret(
                    path=secret_path, mount_point=self._mount
                )
                data = response['data']
                if 'value' in data and len(data) == 1:
                    return data['value']
                return json.dumps(data)
                
        except self._hvac.exceptions.InvalidPath:
            if required:
                raise SecretsBackendError(
                    f"Vault secret '{secret_path}' not found at mount '{self._mount}'.",
                    backend=self.backend_name
                )
            return None
        except self._hvac.exceptions.Forbidden as e:
            raise SecretsBackendError(
                f"Permission denied accessing Vault secret '{secret_path}'.",
                backend=self.backend_name, original_error=e
            )
        except Exception as e:
            raise SecretsBackendError(
                f"Vault error retrieving '{secret_path}': {e}",
                backend=self.backend_name, original_error=e
            )
    
    def get_json_secret(self, key: str, required: bool = True) -> Optional[Dict]:
        """Get secret from Vault and return as dictionary."""
        secret_path = self._normalize_secret_path(key)
        
        try:
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    path=secret_path, mount_point=self._mount
                )
                return response['data']['data']
            except self._hvac.exceptions.InvalidPath:
                response = self._client.secrets.kv.v1.read_secret(
                    path=secret_path, mount_point=self._mount
                )
                return response['data']
        except self._hvac.exceptions.InvalidPath:
            if required:
                raise SecretsBackendError(
                    f"Vault secret '{secret_path}' not found.",
                    backend=self.backend_name
                )
            return None
        except self._hvac.exceptions.Forbidden as e:
            raise SecretsBackendError(
                f"Permission denied accessing Vault secret '{secret_path}'.",
                backend=self.backend_name, original_error=e
            )
        except Exception as e:
            raise SecretsBackendError(
                f"Vault error: {e}",
                backend=self.backend_name, original_error=e
            )


# =============================================================================
# BACKEND FACTORY
# =============================================================================

def _get_secrets_backend(backend_type: Optional[str] = None) -> SecretsBackend:
    """
    Factory function to create the appropriate secrets backend.
    
    Args:
        backend_type: Backend type (env, aws, gcp, azure, vault).
                     If None, reads from DUAL_AUTH_SECRETS_BACKEND env var.
    
    Returns:
        Initialized SecretsBackend instance
    """
    if backend_type is None:
        backend_type = os.getenv('DUAL_AUTH_SECRETS_BACKEND', 'env').lower().strip()
    else:
        backend_type = backend_type.lower().strip()
    
    backends = {
        'env': EnvironmentSecretsBackend,
        'environment': EnvironmentSecretsBackend,
        'aws': AWSSecretsBackend,
        'gcp': GCPSecretsBackend,
        'azure': AzureSecretsBackend,
        'vault': VaultSecretsBackend,
        'hashicorp': VaultSecretsBackend,
    }
    
    if backend_type not in backends:
        valid_backends = ['env', 'aws', 'gcp', 'azure', 'vault']
        raise ConfigurationError(
            f"Invalid secrets backend: '{backend_type}'. "
            f"Must be one of: {', '.join(valid_backends)}"
        )
    
    logger.info("Initializing secrets backend", extra={'backend_type': backend_type})
    
    try:
        return backends[backend_type]()
    except SecretsBackendError:
        raise
    except Exception as e:
        raise SecretsBackendError(
            f"Failed to initialize {backend_type} secrets backend: {e}",
            backend=backend_type, original_error=e
        )


# =============================================================================
# URL VALIDATION HELPERS
# =============================================================================

def _validate_https_url(url: str, field_name: str) -> None:
    """Validate that URL uses HTTPS protocol."""
    if not url:
        raise ConfigurationError(f"{field_name} cannot be empty")
    
    if not url.startswith('https://'):
        if '://' in url:
            scheme = url.split('://')[0]
            raise ConfigurationError(
                f"{field_name} must use HTTPS for security. Got scheme: {scheme}"
            )
        else:
            raise ConfigurationError(
                f"{field_name} must use HTTPS. Example: https://example.com/path"
            )


def _validate_url_format(url: str, field_name: str) -> None:
    """Validate URL has correct format with required components."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            raise ConfigurationError(f"{field_name} missing URL scheme")
        if not parsed.netloc:
            raise ConfigurationError(f"{field_name} missing hostname")
        if parsed.netloc == 'localhost' or parsed.netloc.startswith('127.'):
            logger.warning("%s uses localhost. This should only be used in development.", field_name)
    except Exception as e:
        raise ConfigurationError(f"{field_name} has invalid URL format: {e}") from e


def _validate_file_exists(file_path: str, field_name: str) -> None:
    """Validate that file exists and is readable."""
    if not file_path:
        raise ConfigurationError(f"{field_name} cannot be empty")
    if not os.path.exists(file_path):
        raise ConfigurationError(f"{field_name} file does not exist: {file_path}")
    if not os.path.isfile(file_path):
        raise ConfigurationError(f"{field_name} path is not a file: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise ConfigurationError(f"{field_name} file is not readable: {file_path}")
    try:
        if os.stat(file_path).st_mode & 0o004:
            logger.warning("%s file is world-readable. Consider: chmod 600 %s", field_name, file_path)
    except OSError:
        pass


# =============================================================================
# VENDOR-SPECIFIC CONFIGURATION LOADERS
# =============================================================================

def _get_keycloak_config(backend: SecretsBackend) -> Dict:
    """Load Keycloak-specific configuration from secrets backend."""
    return {
        'token_url': backend.get_secret('KEYCLOAK_TOKEN_URL'),
        'client_id': backend.get_secret('AGENT_CLIENT_ID'),
        'client_secret': backend.get_secret('AGENT_CLIENT_SECRET'),
        'audience': None  # Keycloak auto-derives audience from token_url
    }


def _get_auth0_config(backend: SecretsBackend) -> Dict:
    """Load Auth0-specific configuration from secrets backend."""
    return {
        'token_url': backend.get_secret('AUTH0_TOKEN_URL'),
        'client_id': backend.get_secret('AGENT_CLIENT_ID'),
        'client_secret': backend.get_secret('AGENT_CLIENT_SECRET'),
        'audience': backend.get_secret('API_AUDIENCE')
    }


def _get_okta_config(backend: SecretsBackend) -> Dict:
    """Load Okta-specific configuration from secrets backend."""
    return {
        'token_url': backend.get_secret('OKTA_TOKEN_URL'),
        'client_id': backend.get_secret('AGENT_CLIENT_ID'),
        'client_secret': backend.get_secret('AGENT_CLIENT_SECRET'),
        'audience': backend.get_secret('API_AUDIENCE')
    }


def _get_entraid_config(backend: SecretsBackend) -> Dict:
    """Load EntraID-specific configuration from secrets backend."""
    app_private_key_path = backend.get_secret('APP_PRIVATE_KEY_PATH')
    _validate_file_exists(app_private_key_path, 'APP_PRIVATE_KEY_PATH')
    
    scope = backend.get_secret('API_SCOPE')
    if not scope.endswith('/.default'):
        logger.warning("API_SCOPE for EntraID typically ends with '/.default'. Got: %s", scope)
    
    return {
        'token_url': backend.get_secret('ENTRAID_TOKEN_URL'),
        'client_id': backend.get_secret('AGENT_CLIENT_ID'),
        'client_secret': backend.get_secret('AGENT_CLIENT_SECRET'),
        'scope': scope,
        'app_private_key_path': app_private_key_path,
        'app_id': backend.get_secret('APP_ID'),
        'act_audience': backend.get_secret('API_AUDIENCE')
    }


# =============================================================================
# MAIN PUBLIC API
# =============================================================================

def get_config(
    vendor: Optional[str] = None,
    secrets_backend: Optional[str] = None
) -> Dict:
    """
    Load dual-auth configuration from the configured secrets backend.
    
    Args:
        vendor: IAM vendor name (keycloak, auth0, okta, entraid).
                If None, reads from DUAL_AUTH_VENDOR env var (default: keycloak)
        secrets_backend: Secrets backend type (env, aws, gcp, azure, vault).
                        If None, reads from DUAL_AUTH_SECRETS_BACKEND env var (default: env)
    
    Returns:
        Dictionary containing validated configuration for the selected vendor.
    
    Raises:
        ConfigurationError: If configuration is invalid
        SecretsBackendError: If secrets backend operations fail
    
    Examples:
        # Using environment variables (default)
        config = get_config()
        
        # Using AWS Secrets Manager
        config = get_config(secrets_backend='aws')
        
        # Using HashiCorp Vault for Okta
        config = get_config(vendor='okta', secrets_backend='vault')
    """
    try:
        # Initialize secrets backend
        backend = _get_secrets_backend(secrets_backend)
        
        # Get vendor
        if vendor is None:
            try:
                vendor = backend.get_secret('DUAL_AUTH_VENDOR', required=False)
            except SecretsBackendError:
                vendor = None
            if not vendor:
                vendor = os.getenv('DUAL_AUTH_VENDOR', 'keycloak')
        
        vendor = vendor.lower().strip()
        
        # Validate vendor
        valid_vendors = ['keycloak', 'auth0', 'okta', 'entraid']
        if vendor not in valid_vendors:
            raise ConfigurationError(
                f"Invalid vendor: '{vendor}'. Must be one of: {', '.join(valid_vendors)}"
            )
        
        # Load vendor-specific configuration
        if vendor == 'keycloak':
            config = _get_keycloak_config(backend)
        elif vendor == 'auth0':
            config = _get_auth0_config(backend)
        elif vendor == 'okta':
            config = _get_okta_config(backend)
        elif vendor == 'entraid':
            config = _get_entraid_config(backend)
        else:
            raise ConfigurationError(f"Unsupported vendor: {vendor}")
        
        # Validate common fields
        _validate_https_url(config['token_url'], 'token_url')
        _validate_url_format(config['token_url'], 'token_url')
        
        logger.info("Configuration loaded successfully",
                   extra={'vendor': vendor, 'backend': backend.backend_name})
        
        return config
        
    except (ConfigurationError, SecretsBackendError):
        raise
    except Exception as e:
        logger.error("Unexpected error loading configuration", extra={'error_type': e.__class__.__name__})
        raise ConfigurationError(f"Unexpected error: {e.__class__.__name__}: {str(e)}") from e


def get_vendor() -> str:
    """Get configured vendor name from environment."""
    return os.getenv('DUAL_AUTH_VENDOR', 'keycloak').lower().strip()


def get_secrets_backend_type() -> str:
    """Get configured secrets backend type from environment."""
    return os.getenv('DUAL_AUTH_SECRETS_BACKEND', 'env').lower().strip()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    'get_config',
    'get_vendor',
    'get_secrets_backend_type',
    'ConfigurationError',
    'SecretsBackendError',
    'SecretsBackend',
    'EnvironmentSecretsBackend',
    'AWSSecretsBackend',
    'GCPSecretsBackend',
    'AzureSecretsBackend',
    'VaultSecretsBackend',
]
