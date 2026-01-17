# dual-auth Changelog

All notable changes to the dual-auth project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<br>

## [1.0.1] - 2026-01-17

### Added

#### Core Functionality
- **UserSession dataclass** with `user_id` field for storing IAM user identifiers
  - Enables pseudonymous logging instead of PII
  - Supports privacy compliance (GDPR/CCPA)
  - Located in: `dual_auth/session/hybrid_sender.py`

- **IAM Identifier Logging** throughout all adapters and modules
  - New `_prepare_act_for_logging()` method in BaseAdapter
  - Logs IAM user IDs instead of email addresses
  - Perfect correlation with IAM provider audit logs
  - Affected files: All 5 adapter files, HybridSender

- **Production-Grade Configuration Module** (`dual_auth/config.py`)
  - Custom `ConfigurationError` exception for precise error handling
  - Comprehensive input validation (empty strings, types, lengths)
  - URL validation with HTTPS enforcement
  - File validation (existence, permissions, security warnings)
  - Vendor-specific validation (scope formats, audience checks)
  - Structured logging with audit-friendly fields
  - 930 lines of robust configuration management

#### Cloud Secrets Management
- **Pluggable secrets backends** in `dual_auth/config.py`
  - `EnvironmentSecretsBackend` - Environment variables (default, for development)
  - `AWSSecretsBackend` - AWS Secrets Manager integration
  - `GCPSecretsBackend` - GCP Secret Manager integration
  - `AzureSecretsBackend` - Azure Key Vault integration
  - `VaultSecretsBackend` - HashiCorp Vault integration (token, AppRole, Kubernetes auth)

- **Backend selection** via environment variable or parameter
  - `DUAL_AUTH_SECRETS_BACKEND` environment variable
  - `get_config(secrets_backend='aws')` parameter override

- **New exports** in `dual_auth/__init__.py`
  - `get_secrets_backend_type()` - Returns current backend type
  - `SecretsBackendError` - Exception for backend failures

- **Backend Configuration Variables**
  - AWS: `DUAL_AUTH_AWS_REGION`, `DUAL_AUTH_AWS_SECRET_PREFIX`
  - GCP: `DUAL_AUTH_GCP_PROJECT`, `DUAL_AUTH_GCP_SECRET_PREFIX`
  - Azure: `DUAL_AUTH_AZURE_VAULT_URL`, `DUAL_AUTH_AZURE_SECRET_PREFIX`
  - Vault: `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_ROLE_ID`, `VAULT_SECRET_ID`, `VAULT_NAMESPACE`, `DUAL_AUTH_VAULT_MOUNT`, `DUAL_AUTH_VAULT_PATH_PREFIX`

#### Security Enhancements
- HTTPS validation for all URLs (token endpoints, API endpoints)
- File permission validation with security warnings
- World-readable file detection for private keys
- Short secret length warnings
- Input sanitization and validation throughout

#### Documentation
- **IAM Identifier Guidance** added to all 4 IAM guides
  - Step-by-step extraction from OIDC tokens
  - Vendor-specific identifier format tables
  - Correlation with IAM audit logs documentation
  - Privacy and GDPR compliance explanations

- **Logging Best Practices** sections in all guides
  - What to log (IAM identifiers) vs what NOT to log (PII)
  - Structured logging examples
  - Audit log correlation queries

- **Troubleshooting Sections** for IAM identifiers
  - Common mistakes and solutions
  - OIDC token extraction guidance
  - EntraID Object ID handling

- **Secrets Management Guide** (`SECRETS_MANAGEMENT_GUIDE.md`)
  - Comprehensive documentation for all 5 backends
  - Secret naming conventions per backend
  - Migration guide from environment variables

### Changed

#### Breaking Changes
- **Project renamed** from AGBAC-Min to dual-auth
  - Package: `agbac-min` → `dual_auth`
  - Environment variable: `AGBAC_VENDOR` → `DUAL_AUTH_VENDOR`

- **Package restructured** with new directory layout
  - `adapters/` → `dual_auth/adapters/`
  - `sender/` → `dual_auth/session/`
  - `phase1/` → `dual_auth/session/` and `dual_auth/api/`
  - `phase2/` → `dual_auth/session/` and `dual_auth/api/`
  - `agbac_config.py` → `dual_auth/config.py`

- **File naming updated**
  - `hybrid_sender.py` (unchanged, new location)
  - `in_session_token_request.py` → `insession_token_request.py`
  - `out_of_session_token_request.py` → `outofsession_token_request.py`
  - `in_session_api_call.py` → `insession_api_call.py`
  - `out_of_session_api_call.py` → `outofsession_api_call.py`

- **UserSession** now requires `user_id` parameter
  - Previously optional, now expected to contain IAM user identifier
  - Applications must extract user ID from OIDC `sub` claim
  - Migration: Update `UserSession` calls to include `user_id=oidc_token['sub']`

- **act.sub Field** now contains IAM user identifier (not email)
  - Keycloak: UUID format (e.g., `f1234567-89ab-cdef-0123-456789abcdef`)
  - Auth0: User ID with prefix (e.g., `auth0|63f1234567890abcdef12345`)
  - Okta: User ID starting with 00u (e.g., `00u123abc456xyz`)
  - EntraID: UPN in `sub` + Object ID in `oid` (dual identifiers)
  - Migration: Update application code to use `oidc_token['sub']` not `user.email`

#### Non-Breaking Changes
- **All adapter modules** updated with enhanced error handling
  - More descriptive error messages
  - Better exception wrapping
  - Improved logging context

- **Configuration loading** now uses environment variable pattern
  - Applications load config via `get_config()` function
  - No direct `os.environ` access in library code
  - Makes testing easier and deployment more flexible

- **Documentation terminology** improved
  - "PII-free logging" → "IAM identifier logging" (more accurate)
  - Consistent use of "IAM user identifier" throughout
  - Vendor-specific terminology where appropriate

- **Secrets management** backward compatible
  - Default backend is `env` (environment variables)
  - Existing code using environment variables works unchanged
  - `get_config()` signature extended with optional `secrets_backend` parameter

### Fixed
- Package `__init__.py` files added to all directories
  - `dual_auth/__init__.py`
  - `dual_auth/adapters/__init__.py`
  - `dual_auth/session/__init__.py`
  - `dual_auth/api/__init__.py`
  - Ensures proper Python package imports

### Security
- **Enhanced privacy protection**
  - IAM identifiers (pseudonymous) logged instead of email/name (PII)
  - GDPR/CCPA compliant logging practices
  - Correlation with IAM audit logs maintained

- **Validation improvements**
  - All URLs validated for HTTPS
  - File permissions checked before use
  - Input validation prevents common configuration errors

- **Secrets management security**
  - Secrets never logged
  - Each backend uses platform-native authentication (IAM roles, managed identity, etc.)
  - Support for Vault namespaces and AppRole authentication

### Documentation
- **4 IAM guides updated** with v1.0.1 features:
  - `iam_guide_keycloak.md`
  - `iam_guide_auth0.md`
  - `iam_guide_okta.md`
  - `iam_guide_entraid.md`

- **Implementation guide updated**:
  - `dual_auth_implementation_guide.md` (~2,100 lines)

- **New documentation**:
  - `README.md` - Project overview with quick start
  - `SECRETS_MANAGEMENT_GUIDE.md` - Cloud secrets backend documentation

- **New sections in all guides:**
  - "Get User ID" / "Get Object ID" (IAM identifier extraction)
  - "Logging Best Practices" (pseudonymous logging)
  - "Troubleshooting" (IAM identifier issues)
  - "Secrets Management" (production deployment)
  - Field explanation tables with IAM identifier emphasis

---

## [1.0.0] - 2025-12-15 (Baseline)

### Added

#### Initial Release
- Base adapter architecture (`BaseAdapter`)
- Four IAM vendor adapters:
  - `KeycloakAdapter` - Keycloak support
  - `Auth0Adapter` - Auth0 support
  - `OktaAdapter` - Okta support
  - `EntraIDAdapter` - EntraID (Azure AD) support with hybrid approach

- Human identity extraction (`HybridSender`)
- In-session agent flows
  - `InSessionTokenRequest`
  - `InSessionAPICall`

- Out-of-session agent flows
  - `OutOfSessionTokenRequest` with JWT verification
  - `OutOfSessionAPICall`

- Basic configuration loading
- Environment variable support for all vendors

#### Documentation
- Initial IAM Configuration Guides (4 guides)
- Initial Application/Agent Implementation Guide
- Architecture documentation
- Flow diagrams and examples

<br>

## Migration Guide (v1.0.0 → v1.0.1)

### Code Changes Required

#### 1. Update Imports
```python
# OLD (v1.0.0)
from adapters import KeycloakAdapter
from sender import HybridSender, UserSession
from phase1.in_session_token_request import InSessionTokenRequest
from agbac_config import get_config

# NEW (v1.0.1)
from dual_auth import (
    KeycloakAdapter,
    HybridSender,
    UserSession,
    InSessionTokenRequest,
    get_config
)
```

#### 2. Update Environment Variables
```bash
# OLD (v1.0.0)
export AGBAC_VENDOR=keycloak

# NEW (v1.0.1)
export DUAL_AUTH_VENDOR=keycloak
```

#### 3. Update UserSession Calls
```python
# OLD (v1.0.0)
user_session = UserSession(
    user_email=session['email'],
    user_name=session['name']
)

# NEW (v1.0.1) - Add user_id from OIDC token
id_token = session['id_token']
decoded = jwt.decode(id_token, options={"verify_signature": False})

user_session = UserSession(
    user_email=session['email'],
    user_name=session['name'],
    user_id=decoded['sub']  # IAM user identifier
)
```

#### 4. Update Logging Code
```python
# OLD (v1.0.0) - Logged PII
logger.info(f"User {act['email']} accessed resource")

# NEW (v1.0.1) - Log IAM identifier
logger.info(
    "Resource accessed",
    extra={
        "human_id": act['sub'],  # IAM user ID (pseudonymous)
        "action": "read",
        "resource": "/api/data"
    }
)
```

#### 5. Update act Claim Expectations
```python
# OLD (v1.0.0) - Email in act.sub
act = {
    'sub': 'alice@corp.example.com',  # Email
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}

# NEW (v1.0.1) - IAM user ID in act.sub
act = {
    'sub': 'f1234567-89ab-cdef-0123-456789abcdef',  # Keycloak user ID
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

#### 6. Optional: Use Cloud Secrets Management
```python
# Development (environment variables - works same as v1.0.0)
config = get_config()

# Production with AWS Secrets Manager
export DUAL_AUTH_SECRETS_BACKEND=aws
export DUAL_AUTH_AWS_REGION=us-west-2
config = get_config()  # Automatically uses AWS

# Or explicit backend selection
config = get_config(secrets_backend='vault')
```

### No Changes Required

- IAM provider configurations (no changes needed)
- Token request flows (work the same)
- API call methods (work the same)
- Adapter interface (backward compatible)

### Recommended Actions

1. **Update imports** to use new `dual_auth` package
2. **Update environment variables** from `AGBAC_` to `DUAL_AUTH_`
3. **Update logging** to use IAM identifiers for privacy compliance
4. **Store OIDC ID token** in session for user ID extraction
5. **Review audit log correlation** using new IAM identifiers
6. **Consider cloud secrets management** for production deployments

<br>

## Version History Summary

| Version | Date | Key Changes | Files Changed |
|---------|------|-------------|---------------|
| 1.0.1 | 2026-01-17 | Renamed to dual-auth, new package structure, IAM identifier logging, UserSession.user_id, production config, cloud secrets management | 11 Python + 6 Docs |
| 1.0.0 | 2025-12-15 | Initial release | 11 Python + 5 Docs |

<br>

## Deprecation Notices

### v1.0.1
- **AGBAC_VENDOR** - Use `DUAL_AUTH_VENDOR` instead
- **Old import paths** - Use `from dual_auth import ...` instead

### Future Versions
- No additional deprecations planned
- Backward compatibility commitment maintained

<br>

## Upgrade Path

```
v1.0.0 → v1.0.1: Update imports, rename env vars, use IAM identifiers, optional cloud secrets
```

<br>

## Contributors

- kahalewai

<br>

## License

Apache License 2.0

<br>
