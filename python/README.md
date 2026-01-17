<div align="center">

# dual-auth Application/Agent Implementation Guide

**Python Implementation Guide for Dual-Subject Authorization**

**Version 1.0.1**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for implementing dual-auth dual-subject authorization in your Python applications and AI agents.

After completing this guide, your application and agents will:

✅ Extract human identity from authenticated sessions  
✅ Request dual-subject tokens from IAM providers (Keycloak, Auth0, Okta, EntraID)  
✅ Make authenticated API calls with both agent and human authorization  
✅ Work in both in-session and out-of-session scenarios  
✅ Switch between IAM vendors by changing one configuration variable  
✅ Use cloud secrets management (AWS, GCP, Azure, Vault) for production  

**Estimated Time:** 60-90 minutes  
**Prerequisites:** Python 3.9+, IAM provider configured (see IAM Configuration Guides)  
**Skill Level:** Intermediate Python developer

<br>

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Install dual-auth Package](#step-1-install-dual-auth-package)
4. [Step 2: Configure Environment Variables](#step-2-configure-environment-variables)
5. [Step 3: Configure Secrets Management (Production)](#step-3-configure-secrets-management-production)
6. [Step 4: Implement Human Identity Extraction](#step-4-implement-human-identity-extraction)
7. [Step 5: Implement In-Session Agent](#step-5-implement-in-session-agent)
8. [Step 6: Test In-Session Flow](#step-6-test-in-session-flow)
9. [Step 7: Implement Out-of-Session Agent](#step-7-implement-out-of-session-agent)
10. [Step 8: Test Out-of-Session Flow](#step-8-test-out-of-session-flow)
11. [Step 9: Implement API Calls](#step-9-implement-api-calls)
12. [Step 10: Logging Best Practices](#step-10-logging-best-practices)
13. [Step 11: Production Deployment](#step-11-production-deployment)
14. [Troubleshooting](#troubleshooting)
15. [Reference: Complete Examples](#reference-complete-examples)

<br>

## **Prerequisites**

Before starting, ensure you have:

### **IAM Configuration**
- [ ] IAM provider configured (choose one):
  - [ ] Keycloak (see [Keycloak IAM Configuration Guide](https://www.github.com/kahalewai/dual-auth/docs/iam_guide_keycloak.md))
  - [ ] Auth0 (see [Auth0 IAM Configuration Guide](https://www.github.com/kahalewai/dual-auth/docs/iam_guide_auth0.md))
  - [ ] Okta (see [Okta IAM Configuration Guide](https://www.github.com/kahalewai/dual-auth/docs/iam_guide_okta.md))
  - [ ] EntraID (see [EntraID IAM Configuration Guide](https://www.github.com/kahalewai/dual-auth/docs/iam_guide_entraid.md))

### **Technical Requirements**
- [ ] Python 3.9 or higher installed
- [ ] pip package manager
- [ ] Text editor or IDE (VS Code, PyCharm, etc.)
- [ ] Terminal/command line access

### **IAM Credentials**
- [ ] Agent client ID (from IAM configuration)
- [ ] Agent client secret (from IAM configuration)
- [ ] Token endpoint URL (from IAM configuration)
- [ ] API audience/scope (from IAM configuration)

### **For Out-of-Session Scenarios**
- [ ] RSA key pair generated (application signing keys)
- [ ] Agent endpoint URL (where agent is hosted)

<br>

## **Architecture Overview**

### **In-Session Flow**

\`\`\`
┌──────────────────┐
│  Web Application │
│                  │
│  1. User logs in │
│  2. Session      │
│     created      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HybridSender    │
│  (extracts act)  │
└────────┬─────────┘
         │ (in-memory)
         ▼
┌──────────────────┐
│  In-Session      │
│  Agent           │
│                  │
│  3. Gets act     │
│  4. Requests     │
│     token        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Adapter     │
│  (Keycloak/      │
│   Auth0/Okta/    │
│   EntraID)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Provider    │
│                  │
│  5. Issues token │
│     with sub+act │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client      │
│                  │
│  6. Calls API    │
│     with token   │
└──────────────────┘
\`\`\`

### **Out-of-Session Flow**

\`\`\`
┌──────────────────┐
│  Web Application │
│                  │
│  1. User logs in │
│  2. Session      │
│     created      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HybridSender    │
│  (creates signed │
│   act JWT)       │
└────────┬─────────┘
         │ (HTTPS)
         ▼
┌──────────────────┐
│  Out-of-Session  │
│  Agent (remote)  │
│                  │
│  3. Receives JWT │
│  4. Verifies JWT │
│  5. Requests     │
│     token        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Provider    │
│                  │
│  6. Issues token │
│     with sub+act │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client      │
│                  │
│  7. Calls API    │
│     with token   │
└──────────────────┘
\`\`\`

<br>

## **Step 1: Install dual-auth Package**

### 1.1 Package Structure

The dual-auth package has the following structure:

\`\`\`
dual_auth/
├── __init__.py              # Main package exports
├── config.py                # Configuration with secrets management
├── adapters/
│   ├── __init__.py
│   ├── base_adapter.py      # Base adapter class
│   ├── keycloak_adapter.py  # Keycloak adapter
│   ├── auth0_adapter.py     # Auth0 adapter
│   ├── okta_adapter.py      # Okta adapter
│   └── entraid_adapter.py   # EntraID adapter
├── session/
│   ├── __init__.py
│   ├── hybrid_sender.py     # Human identity extraction
│   ├── insession_token_request.py
│   └── outofsession_token_request.py
└── api/
    ├── __init__.py
    ├── insession_api_call.py
    └── outofsession_api_call.py
\`\`\`

### 1.2 Install the Package

**Option A: Install from PyPI (recommended)**

\`\`\`bash
pip install dual-auth
\`\`\`

**Option B: Install from source**

\`\`\`bash
git clone https://github.com/kahalewai/dual-auth/python/src/dual_auth.git
cd dual_auth
pip install .
\`\`\`

**Option C: Install as editable package**

\`\`\`bash
git clone https://github.com/kahalewai/dual-auth/python/src/dual_auth.git
cd dual-auth
pip install -e .
\`\`\`

### 1.3 Install Required Dependencies

\`\`\`bash
pip install pyjwt[crypto]>=2.8.0 requests>=2.31.0 cryptography>=41.0.0
\`\`\`

**For cloud secrets management (optional, choose as needed):**

\`\`\`bash
# AWS Secrets Manager
pip install boto3

# GCP Secret Manager
pip install google-cloud-secret-manager

# Azure Key Vault
pip install azure-identity azure-keyvault-secrets

# HashiCorp Vault
pip install hvac
\`\`\`

### 1.4 Verify Installation

\`\`\`bash
python3 -c "
from dual_auth import (
    __version__,
    get_config,
    get_vendor,
    get_secrets_backend_type,
    KeycloakAdapter,
    Auth0Adapter,
    OktaAdapter,
    EntraIDAdapter,
    HybridSender,
    UserSession,
    InSessionTokenRequest,
    OutOfSessionTokenRequest,
    InSessionAPICall,
    OutOfSessionAPICall
)
print(f'✅ dual-auth v{__version__} installed successfully')
"
\`\`\`

**Expected output:**
\`\`\`
✅ dual-auth v1.0.1 installed successfully
\`\`\`

<br>

## **Step 2: Configure Environment Variables**

### 2.1 Create Environment File (Development/Testing)

Create a \`.env\` file in your project root:

\`\`\`bash
touch .env
\`\`\`

**⚠️ Security:** Add \`.env\` to \`.gitignore\` to prevent committing secrets:

\`\`\`bash
echo ".env" >> .gitignore
\`\`\`

### 2.2 Configure for Your IAM Vendor

**Choose your IAM provider and configure accordingly:**

#### **Option A: Keycloak**

\`\`\`bash
# Vendor Selection
DUAL_AUTH_VENDOR=keycloak

# Keycloak Configuration
KEYCLOAK_TOKEN_URL=https://your-keycloak-domain/realms/your-realm/protocol/openid-connect/token
AGENT_CLIENT_ID=finance-agent
AGENT_CLIENT_SECRET=your-client-secret-from-keycloak

# API Configuration
API_URL=https://api.example.com/finance/report
\`\`\`

#### **Option B: Auth0**

\`\`\`bash
# Vendor Selection
DUAL_AUTH_VENDOR=auth0

# Auth0 Configuration
AUTH0_TOKEN_URL=https://your-tenant.auth0.com/oauth/token
AGENT_CLIENT_ID=your-m2m-app-client-id
AGENT_CLIENT_SECRET=your-client-secret-from-auth0
API_AUDIENCE=https://api.example.com

# API Configuration
API_URL=https://api.example.com/finance/report
\`\`\`

#### **Option C: Okta**

\`\`\`bash
# Vendor Selection
DUAL_AUTH_VENDOR=okta

# Okta Configuration
OKTA_TOKEN_URL=https://dev-123.okta.com/oauth2/aus123abc/v1/token
AGENT_CLIENT_ID=your-service-app-client-id
AGENT_CLIENT_SECRET=your-client-secret-from-okta
API_AUDIENCE=https://api.example.com

# API Configuration
API_URL=https://api.example.com/finance/report
\`\`\`

#### **Option D: EntraID**

\`\`\`bash
# Vendor Selection
DUAL_AUTH_VENDOR=entraid

# EntraID Configuration
ENTRAID_TOKEN_URL=https://login.microsoftonline.com/your-tenant-id/oauth2/v2.0/token
AGENT_CLIENT_ID=your-app-registration-id
AGENT_CLIENT_SECRET=your-client-secret-from-entraid
API_SCOPE=https://api.example.com/.default
API_AUDIENCE=https://api.example.com

# EntraID Hybrid Approach Keys (path to private key file)
APP_PRIVATE_KEY_PATH=/path/to/app-private-key.pem
APP_ID=https://your-app-identifier

# API Configuration
API_URL=https://api.example.com/finance/report
\`\`\`

### 2.3 Load Configuration in Your Application

\`\`\`python
# your_app.py
from dual_auth import get_config, ConfigurationError, KeycloakAdapter
import sys

def main():
    # Load configuration from environment variables
    try:
        config = get_config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create adapter with config
    adapter = KeycloakAdapter(config)
    
    print(f"Configuration loaded successfully")
    print(f"Token URL: {config['token_url']}")
    print(f"Client ID: {config['client_id']}")

if __name__ == '__main__':
    main()
\`\`\`

### 2.4 Configuration Patterns

#### **Pattern 1: Auto-detect vendor (Recommended)**

\`\`\`python
from dual_auth import get_config

# Auto-detects vendor from DUAL_AUTH_VENDOR env var
config = get_config()
\`\`\`

#### **Pattern 2: Explicit vendor**

\`\`\`python
from dual_auth import get_config

# Override vendor (ignores DUAL_AUTH_VENDOR env var)
config = get_config(vendor='auth0')
\`\`\`

#### **Pattern 3: With error handling**

\`\`\`python
from dual_auth import get_config, ConfigurationError, SecretsBackendError
import logging
import sys

logger = logging.getLogger(__name__)

try:
    config = get_config()
except SecretsBackendError as e:
    logger.error(f"Secrets backend error ({e.backend}): {e}")
    sys.exit(1)
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
\`\`\`

### 2.5 Configuration Dictionary by Vendor

**Keycloak:**
\`\`\`python
{
    'token_url': 'https://keycloak.example.com/realms/prod/protocol/openid-connect/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': None  # Auto-derived from token_url
}
\`\`\`

**Auth0:**
\`\`\`python
{
    'token_url': 'https://tenant.auth0.com/oauth/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': 'https://api.example.com'
}
\`\`\`

**Okta:**
\`\`\`python
{
    'token_url': 'https://dev-123.okta.com/oauth2/aus123/v1/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': 'https://api.example.com'
}
\`\`\`

**EntraID:**
\`\`\`python
{
    'token_url': 'https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'scope': 'https://api.example.com/.default',
    'app_private_key_path': '/keys/app_private_key.pem',
    'app_id': 'https://app.example.com',
    'act_audience': 'https://api.example.com'
}
\`\`\`

<br>

## **Step 3: Configure Secrets Management (Production)**

**⚠️ For production deployments, use cloud secrets management instead of environment variables.**

dual-auth v1.0.1 supports five secrets backends:

| Backend | Use Case | Environment Variable |
|---------|----------|---------------------|
| \`env\` | Development/Testing | \`DUAL_AUTH_SECRETS_BACKEND=env\` |
| \`aws\` | AWS deployments | \`DUAL_AUTH_SECRETS_BACKEND=aws\` |
| \`gcp\` | GCP deployments | \`DUAL_AUTH_SECRETS_BACKEND=gcp\` |
| \`azure\` | Azure deployments | \`DUAL_AUTH_SECRETS_BACKEND=azure\` |
| \`vault\` | Multi-cloud/on-premises | \`DUAL_AUTH_SECRETS_BACKEND=vault\` |

### 3.1 AWS Secrets Manager

**Install:**
\`\`\`bash
pip install boto3
\`\`\`

**Configure:**
\`\`\`bash
export DUAL_AUTH_SECRETS_BACKEND=aws
export DUAL_AUTH_AWS_REGION=us-west-2
export DUAL_AUTH_AWS_SECRET_PREFIX=dual-auth/
\`\`\`

**Create secrets in AWS:**
\`\`\`bash
aws secretsmanager create-secret --name dual-auth/AGENT_CLIENT_ID --secret-string "finance-agent"
aws secretsmanager create-secret --name dual-auth/AGENT_CLIENT_SECRET --secret-string "your-secret"
aws secretsmanager create-secret --name dual-auth/KEYCLOAK_TOKEN_URL --secret-string "https://..."
\`\`\`

**Use in application:**
\`\`\`python
from dual_auth import get_config

# Automatically uses AWS Secrets Manager
config = get_config()
\`\`\`

### 3.2 GCP Secret Manager

**Install:**
\`\`\`bash
pip install google-cloud-secret-manager
\`\`\`

**Configure:**
\`\`\`bash
export DUAL_AUTH_SECRETS_BACKEND=gcp
export DUAL_AUTH_GCP_PROJECT=your-project-id
export DUAL_AUTH_GCP_SECRET_PREFIX=dual-auth-
\`\`\`

**Create secrets in GCP:**
\`\`\`bash
echo -n "finance-agent" | gcloud secrets create dual-auth-agent-client-id --data-file=-
echo -n "your-secret" | gcloud secrets create dual-auth-agent-client-secret --data-file=-
echo -n "https://..." | gcloud secrets create dual-auth-keycloak-token-url --data-file=-
\`\`\`

### 3.3 Azure Key Vault

**Install:**
\`\`\`bash
pip install azure-identity azure-keyvault-secrets
\`\`\`

**Configure:**
\`\`\`bash
export DUAL_AUTH_SECRETS_BACKEND=azure
export DUAL_AUTH_AZURE_VAULT_URL=https://your-vault.vault.azure.net/
export DUAL_AUTH_AZURE_SECRET_PREFIX=dual-auth-
\`\`\`

**Create secrets in Azure:**
\`\`\`bash
az keyvault secret set --vault-name your-vault --name dual-auth-agent-client-id --value "finance-agent"
az keyvault secret set --vault-name your-vault --name dual-auth-agent-client-secret --value "your-secret"
\`\`\`

### 3.4 HashiCorp Vault

**Install:**
\`\`\`bash
pip install hvac
\`\`\`

**Configure:**
\`\`\`bash
export DUAL_AUTH_SECRETS_BACKEND=vault
export VAULT_ADDR=https://vault.example.com:8200
export VAULT_TOKEN=hvs.your-token
export DUAL_AUTH_VAULT_MOUNT=secret
export DUAL_AUTH_VAULT_PATH_PREFIX=dual-auth/
\`\`\`

**Create secrets in Vault:**
\`\`\`bash
vault kv put secret/dual-auth/agent-client-id value="finance-agent"
vault kv put secret/dual-auth/agent-client-secret value="your-secret"
\`\`\`

### 3.5 Explicit Backend Selection

\`\`\`python
from dual_auth import get_config

# Override backend via parameter
config = get_config(secrets_backend='aws')

# Or combine with vendor override
config = get_config(vendor='okta', secrets_backend='vault')
\`\`\`

<br>

## **Step 4: Implement Human Identity Extraction**

### 4.1 Understanding Human Identity Extraction

The **HybridSender** extracts human identity from your application's authenticated session and formats it for dual-auth.

**What it does:**
1. Takes authenticated user data from your session
2. Formats it as an "act" claim
3. Prepares it for transmission to agents (in-memory or over network)

### 4.2 Create HybridSender Instance

\`\`\`python
from dual_auth import HybridSender

# For in-session scenarios (no keys needed)
sender = HybridSender()

# For out-of-session scenarios (requires signing key path)
sender = HybridSender(
    private_key_pem='/path/to/app-private-key.pem'
)
\`\`\`

### 4.3 Extract Act from Your Session

**Example 1: From Flask Session**

\`\`\`python
from flask import session
from dual_auth import UserSession, HybridSender

# After user authenticates via OIDC/SAML/etc.
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    # Create UserSession from Flask session
    user_session = UserSession(
        user_email=session['user']['email'],
        user_name=session['user']['name'],
        user_id=session['user'].get('id')  # IAM identifier
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # act is now ready to pass to agent
    # {'sub': 'iam-user-id', 'email': '...', 'name': '...'}
\`\`\`

**Example 2: From Django Session**

\`\`\`python
from django.contrib.auth.decorators import login_required
from dual_auth import UserSession, HybridSender

@login_required
def dashboard(request):
    # Create UserSession from Django user
    user_session = UserSession(
        user_email=request.user.email,
        user_name=request.user.get_full_name(),
        user_id=str(request.user.id)
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
\`\`\`

### 4.4 Best Practice: Extract from OIDC Token

The recommended approach is to extract user information directly from the OIDC ID token:

\`\`\`python
from flask import session
from dual_auth import UserSession, HybridSender
import jwt

@app.route('/dashboard')
def dashboard():
    if 'id_token' not in session:
        return redirect('/login')
    
    # Decode OIDC ID token (signature already verified during login)
    id_token = session['id_token']
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    
    # Extract IAM user identifier from token
    user_id = decoded['sub']  # IAM user ID (NOT email!)
    user_email = decoded.get('email', decoded.get('preferred_username'))
    user_name = decoded.get('name', '')
    
    # For EntraID, also extract object ID
    user_oid = decoded.get('oid')  # EntraID only
    
    # Create UserSession with IAM identifier
    user_session = UserSession(
        user_email=user_email,
        user_name=user_name,
        user_id=user_id  # This is the IAM user ID from OIDC token
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # act.sub will now contain the IAM user ID (pseudonymous)
\`\`\`

### 4.5 Act Claim Format

The \`act\` should be a dictionary containing the human identity:

\`\`\`python
{
    'sub': 'iam-user-id',              # Required: IAM user identifier
    'email': 'alice@corp.example.com', # Recommended: For display
    'name': 'Alice Smith',             # Recommended: For display
    'oid': 'entraid-object-id'         # Required for EntraID: Object ID
}
\`\`\`

**⚠️ Security Note:** The \`act.sub\` field should contain the user's **IAM user identifier**, not their email address:

| IAM Provider | act.sub Value | Example |
|--------------|---------------|---------|
| **Keycloak** | User ID (UUID) | \`f1234567-89ab-cdef-0123-456789abcdef\` |
| **Auth0** | User ID | \`auth0\|63f1234567890abcdef12345\` |
| **Okta** | User ID | \`00u123abc456xyz\` |
| **EntraID** | User UPN + oid | \`sub\`: UPN, \`oid\`: GUID |

**Why IAM identifier instead of email?**
- **Privacy**: IAM user ID is pseudonymous (not PII)
- **Stability**: Doesn't change if user's email changes
- **Correlation**: Perfect correlation with IAM audit logs
- **GDPR/CCPA**: Reduces PII in logs

<br>

## **Step 5: Implement In-Session Agent**

### 5.1 Understanding In-Session Agents

**In-session agents** run in the same process as your application. They:
- Receive human identity (act) in-memory
- Request tokens from IAM
- Make API calls
- No network transmission of act required

**Use case:** AI features integrated directly into your web application.

### 5.2 Configure IAM Adapter

\`\`\`python
from dual_auth import get_config, KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter

# Load configuration
config = get_config()

# Get vendor and create appropriate adapter
vendor = config.get('vendor') or os.environ.get('DUAL_AUTH_VENDOR', 'keycloak')

if vendor == 'keycloak':
    adapter = KeycloakAdapter(config)
elif vendor == 'auth0':
    adapter = Auth0Adapter(config)
elif vendor == 'okta':
    adapter = OktaAdapter(config)
elif vendor == 'entraid':
    adapter = EntraIDAdapter(config)
\`\`\`

**Simpler pattern using factory:**

\`\`\`python
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter
)

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    adapter_class = adapters.get(vendor)
    if not adapter_class:
        raise ValueError(f"Unknown vendor: {vendor}")
    
    return adapter_class(config)
\`\`\`

### 5.3 Create In-Session Token Request

\`\`\`python
from dual_auth import InSessionTokenRequest, HybridSender, UserSession

# 1. Create adapter
adapter = get_adapter()

# 2. Create token request handler
token_request = InSessionTokenRequest(adapter)

# 3. Extract human identity
user_session = UserSession(
    user_email=session['user']['email'],
    user_name=session['user']['name'],
    user_id=session['user']['id']
)

sender = HybridSender()
act = sender.extract_act_from_session(user_session)

# 4. Request token
token_response = token_request.request_token(
    agent_id=os.environ['AGENT_CLIENT_ID'],
    act=act,
    scope=['finance.read']
)

# 5. Use token
print(f"Token expires in: {token_response.expires_in} seconds")
access_token = token_response.access_token

# For EntraID (hybrid approach)
if token_response.act_assertion:
    act_assertion = token_response.act_assertion
\`\`\`

### 5.4 Complete In-Session Example

\`\`\`python
from flask import Flask, session, redirect, jsonify
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, InSessionTokenRequest
)
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

@app.route('/agent-task')
def agent_task():
    # 1. Verify user authenticated
    if 'user' not in session:
        return redirect('/login')
    
    # 2. Extract human identity
    user_session = UserSession(
        user_email=session['user']['email'],
        user_name=session['user']['name'],
        user_id=session['user']['id']
    )
    
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # 3. Create adapter and token request handler
    adapter = get_adapter()
    token_request = InSessionTokenRequest(adapter)
    
    # 4. Request token
    try:
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        
        # 5. Use token for API calls (see Step 9)
        return jsonify({
            'status': 'success',
            'token_type': token_response.token_type,
            'expires_in': token_response.expires_in
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
\`\`\`

<br>

## **Step 6: Test In-Session Flow**

### 6.1 Create Test Script

Create \`test_in_session.py\`:

\`\`\`python
import os
import logging
from dotenv import load_dotenv
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, InSessionTokenRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

def test_in_session_flow():
    print("=" * 60)
    print("dual-auth In-Session Flow Test")
    print("=" * 60)
    
    # 1. Simulate authenticated user
    print("\n1. Simulating authenticated user...")
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith",
        user_id="user_12345"
    )
    print("   ✓ User: alice@corp.example.com")
    
    # 2. Extract act
    print("\n2. Extracting human identity (act)...")
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    print(f"   ✓ Act extracted with fields: {list(act.keys())}")
    
    # 3. Configure adapter
    print("\n3. Configuring IAM adapter...")
    vendor = get_vendor()
    print(f"   Vendor: {vendor}")
    
    adapter = get_adapter()
    print(f"   ✓ Adapter created: {adapter.__class__.__name__}")
    
    # 4. Create token request handler
    print("\n4. Creating in-session token request handler...")
    token_request = InSessionTokenRequest(adapter)
    print("   ✓ Handler created")
    
    # 5. Request token
    print("\n5. Requesting dual-subject token...")
    try:
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        print("   ✓ Token received successfully")
        print(f"   Token type: {token_response.token_type}")
        print(f"   Expires in: {token_response.expires_in} seconds")
        
        if token_response.act_assertion:
            print("   ✓ Act assertion included (EntraID hybrid)")
        
        print("\n" + "=" * 60)
        print("✓ IN-SESSION FLOW TEST PASSED")
        print("=" * 60)
        
        return token_response
        
    except Exception as e:
        print(f"   ✗ Token request failed: {e}")
        print("\n" + "=" * 60)
        print("✗ IN-SESSION FLOW TEST FAILED")
        print("=" * 60)
        raise

if __name__ == '__main__':
    test_in_session_flow()
\`\`\`

### 6.2 Run Test

\`\`\`bash
python test_in_session.py
\`\`\`

### 6.3 Expected Output

\`\`\`
============================================================
dual-auth In-Session Flow Test
============================================================

1. Simulating authenticated user...
   ✓ User: alice@corp.example.com

2. Extracting human identity (act)...
   ✓ Act extracted with fields: ['sub', 'email', 'name']

3. Configuring IAM adapter...
   Vendor: keycloak
   ✓ Adapter created: KeycloakAdapter

4. Creating in-session token request handler...
   ✓ Handler created

5. Requesting dual-subject token...
   ✓ Token received successfully
   Token type: Bearer
   Expires in: 300 seconds

============================================================
✓ IN-SESSION FLOW TEST PASSED
============================================================
\`\`\`

<br>

## **Step 7: Implement Out-of-Session Agent**

### 7.1 Understanding Out-of-Session Agents

**Out-of-session agents** run in a separate process (often on different servers). They:
- Receive human identity (act) as signed JWT over HTTPS
- Verify JWT signature
- Request tokens from IAM
- Make API calls

**Use case:** Standalone AI services, microservices, remote agents.

### 7.2 Generate Application RSA Keys

**Using OpenSSL:**

\`\`\`bash
# Generate private key
openssl genrsa -out app-private-key.pem 2048

# Generate public key
openssl rsa -in app-private-key.pem -pubout -out app-public-key.pem

# Display keys
cat app-private-key.pem
cat app-public-key.pem
\`\`\`

**Using Python:**

\`\`\`python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Serialize private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Generate public key
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Save to files
with open('app-private-key.pem', 'wb') as f:
    f.write(private_pem)

with open('app-public-key.pem', 'wb') as f:
    f.write(public_pem)

print("✓ Keys generated: app-private-key.pem, app-public-key.pem")
\`\`\`

### 7.3 Application: Create and Send Act JWT

**In your web application:**

\`\`\`python
from dual_auth import HybridSender, UserSession
import requests
import os

# After user authenticates
user_session = UserSession(
    user_email=session['user']['email'],
    user_name=session['user']['name'],
    user_id=session['user']['id']
)

# Create sender with private key
sender = HybridSender(
    private_key_pem=os.environ['APP_PRIVATE_KEY_PATH']
)

# Extract act
act = sender.extract_act_from_session(user_session)

# Create signed act JWT
agent_endpoint = os.environ['AGENT_ENDPOINT']
act_jwt = sender.prepare_out_of_session_act(
    act=act,
    agent_endpoint=agent_endpoint,
    ttl_seconds=60  # JWT valid for 60 seconds
)

# Send to agent over HTTPS
response = requests.post(
    agent_endpoint,
    json={'act_jwt': act_jwt},
    headers={'Content-Type': 'application/json'},
    verify=True,  # TLS certificate verification
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print(f"Agent task completed: {result}")
else:
    print(f"Agent task failed: {response.status_code}")
\`\`\`

### 7.4 Agent: Receive and Verify Act JWT

**In your agent service:**

\`\`\`python
from flask import Flask, request, jsonify
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    OutOfSessionTokenRequest
)
import os

app = Flask(__name__)

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

@app.route('/invoke', methods=['POST'])
def invoke_agent():
    # 1. Get act JWT from request
    data = request.json
    act_jwt = data.get('act_jwt')
    
    if not act_jwt:
        return jsonify({'error': 'Missing act_jwt'}), 400
    
    try:
        # 2. Configure adapter
        adapter = get_adapter()
        
        # 3. Create out-of-session token request handler
        token_request = OutOfSessionTokenRequest(
            adapter=adapter,
            app_public_key_path=os.environ['APP_PUBLIC_KEY_PATH']
        )
        
        # 4. Verify JWT and extract act
        act = token_request.receive_and_verify_act_jwt(
            act_jwt=act_jwt,
            expected_audience=os.environ['AGENT_ENDPOINT']
        )
        
        # 5. Request token with verified act
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        
        # 6. Perform agent task with token
        # (see Step 9 for API calls)
        
        return jsonify({
            'status': 'success',
            'message': 'Agent task completed'
        })
        
    except ValueError as e:
        return jsonify({'error': f'JWT verification failed: {e}'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
\`\`\`

<br>

## **Step 8: Test Out-of-Session Flow**

### 8.1 Create Test Script

Create \`test_out_of_session.py\`:

\`\`\`python
import os
import logging
from dotenv import load_dotenv
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, OutOfSessionTokenRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

def test_out_of_session_flow():
    print("=" * 60)
    print("dual-auth Out-of-Session Flow Test")
    print("=" * 60)
    
    # Part 1: Application creates act JWT
    print("\n[APPLICATION SIDE]")
    print("1. Simulating authenticated user...")
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith",
        user_id="user_12345"
    )
    print("   ✓ User: alice@corp.example.com")
    
    print("\n2. Creating signed act JWT...")
    sender = HybridSender(
        private_key_pem=os.environ['APP_PRIVATE_KEY_PATH']
    )
    
    act = sender.extract_act_from_session(user_session)
    
    act_jwt = sender.prepare_out_of_session_act(
        act=act,
        agent_endpoint=os.environ['AGENT_ENDPOINT'],
        ttl_seconds=60
    )
    
    print(f"   ✓ Act JWT created (expires in 60 seconds)")
    
    # Part 2: Agent receives and verifies JWT
    print("\n[AGENT SIDE]")
    print("3. Configuring IAM adapter...")
    vendor = get_vendor()
    print(f"   Vendor: {vendor}")
    
    adapter = get_adapter()
    print(f"   ✓ Adapter created: {adapter.__class__.__name__}")
    
    print("\n4. Creating out-of-session token request handler...")
    token_request = OutOfSessionTokenRequest(
        adapter=adapter,
        app_public_key_path=os.environ['APP_PUBLIC_KEY_PATH']
    )
    print("   ✓ Handler created")
    
    print("\n5. Verifying act JWT...")
    try:
        act = token_request.receive_and_verify_act_jwt(
            act_jwt=act_jwt,
            expected_audience=os.environ['AGENT_ENDPOINT']
        )
        print("   ✓ JWT signature verified")
        print("   ✓ Act extracted from JWT")
        
        print("\n6. Requesting dual-subject token...")
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        print("   ✓ Token received successfully")
        print(f"   Token type: {token_response.token_type}")
        print(f"   Expires in: {token_response.expires_in} seconds")
        
        print("\n" + "=" * 60)
        print("✓ OUT-OF-SESSION FLOW TEST PASSED")
        print("=" * 60)
        
        return token_response
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        print("\n" + "=" * 60)
        print("✗ OUT-OF-SESSION FLOW TEST FAILED")
        print("=" * 60)
        raise

if __name__ == '__main__':
    test_out_of_session_flow()
\`\`\`

### 8.2 Run Test

\`\`\`bash
python test_out_of_session.py
\`\`\`

<br>

## **Step 9: Implement API Calls**

### 9.1 Understanding API Clients

The **InSessionAPICall** and **OutOfSessionAPICall** handle authenticated API calls with dual-subject tokens.

**Key features:**
- Automatically formats headers for all vendors
- EntraID: Adds \`X-Act-Assertion\` header automatically
- HTTPS enforcement
- Retry logic for transient failures
- Proper error handling

### 9.2 Create API Client

\`\`\`python
from dual_auth import InSessionAPICall

# Create client
client = InSessionAPICall(timeout=30)
\`\`\`

### 9.3 Make GET Request

\`\`\`python
# After getting token from token request
token_response = token_request.request_token(...)

# Make authenticated GET request
response = client.call_api(
    method='GET',
    api_url='https://api.example.com/finance/report/Q4-2025',
    token_response=token_response,
    params={'detail': 'full'}
)

# Handle response
if response.status_code == 200:
    data = response.json()
    print(f"Report data: {data}")
elif response.status_code == 403:
    print("Access denied - check authorization")
else:
    print(f"API error: {response.status_code}")
\`\`\`

### 9.4 Make POST Request

\`\`\`python
# Make authenticated POST request
response = client.call_api(
    method='POST',
    api_url='https://api.example.com/finance/transactions',
    token_response=token_response,
    json_data={
        'amount': 1000.00,
        'description': 'Q4 budget allocation'
    }
)

if response.status_code == 201:
    print("Transaction created")
else:
    print(f"Failed: {response.status_code}")
\`\`\`

### 9.5 Complete API Call Example

\`\`\`python
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, InSessionTokenRequest, InSessionAPICall
)
import os

def perform_agent_task():
    # 1. Extract human identity
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith",
        user_id="user_12345"
    )
    
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # 2. Get adapter and token
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    adapter = adapters[vendor](config)
    
    token_request = InSessionTokenRequest(adapter)
    token_response = token_request.request_token(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        act=act,
        scope=['finance.read', 'finance.write']
    )
    
    # 3. Create API client
    client = InSessionAPICall(timeout=30)
    
    # 4. Make API calls
    # Get financial report
    report_response = client.call_api(
        method='GET',
        api_url=os.environ['API_URL'],
        token_response=token_response,
        params={'quarter': 'Q4', 'year': '2025'}
    )
    
    if report_response.status_code == 200:
        report = report_response.json()
        
        # Process report and create summary
        summary = {
            'total_revenue': report['revenue'],
            'total_expenses': report['expenses'],
            'net_income': report['revenue'] - report['expenses']
        }
        
        # Post summary
        summary_response = client.call_api(
            method='POST',
            api_url='https://api.example.com/finance/summaries',
            token_response=token_response,
            json_data=summary
        )
        
        if summary_response.status_code == 201:
            return {'success': True, 'summary_id': summary_response.json()['id']}
    
    return {'success': False, 'error': 'API call failed'}
\`\`\`

### 9.6 EntraID-Specific Header Handling

**The API client automatically handles EntraID's two-header format:**

\`\`\`python
# For Keycloak/Auth0/Okta
# Headers sent:
# Authorization: Bearer <token>

# For EntraID
# Headers sent:
# Authorization: Bearer <entraid-token>
# X-Act-Assertion: <app-signed-jwt>

# You don't need to do anything different!
# The client automatically detects EntraID from the token_response
response = client.call_api(
    method='GET',
    api_url=api_url,
    token_response=token_response  # Contains both components for EntraID
)
\`\`\`

<br>

## **Step 10: Logging Best Practices**

### 10.1 Understanding What to Log

dual-auth uses **IAM user identifiers** (not PII) for logging, ensuring privacy compliance while maintaining audit trails.

**✅ DO: Log IAM identifiers**
\`\`\`python
import logging

logger = logging.getLogger(__name__)

# After extracting act
act = sender.extract_act_from_session(user_session)

# Log using IAM user identifier (pseudonymous)
logger.info(
    "API request initiated",
    extra={
        "agent_id": os.environ['AGENT_CLIENT_ID'],
        "human_id": act['sub'],  # IAM user ID (NOT email!)
        "action": "read",
        "resource": "/api/finance/reports"
    }
)
\`\`\`

**❌ DON'T: Log PII**
\`\`\`python
# BAD - Logs PII
logger.info(f"User {act['email']} accessed reports")  # ❌ Email is PII
logger.info(f"Name: {act['name']}")                   # ❌ Name is PII
\`\`\`

### 10.2 Why Log IAM Identifiers?

**Privacy:**
- IAM user IDs are pseudonymous (not PII)
- GDPR/CCPA compliant
- Can be used in analytics without privacy concerns

**Correlation:**
- Matches IAM audit logs perfectly
- Security investigations can correlate app logs ↔ IAM logs

**Stability:**
- User ID does not change if email changes
- Historical logs remain valid

### 10.3 Correlation with IAM Audit Logs

| IAM Provider | Audit Log Field | Your App Log Field | Correlation |
|--------------|-----------------|-------------------|-------------|
| Keycloak | \`userId\` | \`human_id\` | Match UUIDs |
| Auth0 | \`user_id\` | \`human_id\` | Match user IDs |
| Okta | \`actor.id\` | \`human_id\` | Match user IDs |
| EntraID | \`userId\` | \`human_id\` (from oid) | Match Object IDs |

<br>

## **Step 11: Production Deployment**

### 11.1 Secrets Management

**❌ DO NOT** store secrets in \`.env\` files in production.

**✅ DO** use dual-auth's built-in secrets management:

\`\`\`python
from dual_auth import get_config

# AWS Secrets Manager
config = get_config(secrets_backend='aws')

# GCP Secret Manager
config = get_config(secrets_backend='gcp')

# Azure Key Vault
config = get_config(secrets_backend='azure')

# HashiCorp Vault
config = get_config(secrets_backend='vault')
\`\`\`

See [Step 3: Configure Secrets Management](#step-3-configure-secrets-management-production) for detailed setup.

### 11.2 Logging Configuration

**Production logging with structured JSON:**

\`\`\`python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Configure root logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
\`\`\`

### 11.3 Docker Deployment

**Dockerfile:**

\`\`\`dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dual-auth package
COPY dual_auth/ ./dual_auth/

# Copy application code
COPY your_app.py .

# Run application
CMD ["python", "-u", "your_app.py"]
\`\`\`

**Build and run:**

\`\`\`bash
docker build -t dual-auth-agent .
docker run -e DUAL_AUTH_VENDOR=keycloak \
           -e DUAL_AUTH_SECRETS_BACKEND=aws \
           -e DUAL_AUTH_AWS_REGION=us-west-2 \
           dual-auth-agent
\`\`\`

### 11.4 Kubernetes Deployment

**deployment.yaml:**

\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dual-auth-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dual-auth-agent
  template:
    metadata:
      labels:
        app: dual-auth-agent
    spec:
      containers:
      - name: agent
        image: your-registry/dual-auth-agent:latest
        env:
        - name: DUAL_AUTH_VENDOR
          valueFrom:
            configMapKeyRef:
              name: dual-auth-config
              key: vendor
        - name: DUAL_AUTH_SECRETS_BACKEND
          value: "vault"
        - name: VAULT_ADDR
          value: "https://vault.example.com:8200"
        ports:
        - containerPort: 5000
\`\`\`

### 11.5 Health Checks

**Add health check endpoint:**

\`\`\`python
from flask import Flask, jsonify
from dual_auth import get_config, ConfigurationError
import os

app = Flask(__name__)

@app.route('/health')
def health():
    # Check configuration loads
    try:
        config = get_config()
        config_healthy = True
    except (ConfigurationError, Exception):
        config_healthy = False
    
    return jsonify({
        'status': 'healthy' if config_healthy else 'degraded',
        'config_loaded': config_healthy
    }), 200 if config_healthy else 503

@app.route('/ready')
def ready():
    # Check if required config available
    required_vars = ['DUAL_AUTH_VENDOR']
    ready = all(os.environ.get(var) for var in required_vars)
    
    return jsonify({
        'ready': ready
    }), 200 if ready else 503
\`\`\`

<br>

## **Troubleshooting**

### **Common Issues**

#### **Issue 1: Import Errors**

\`\`\`
ImportError: No module named 'dual_auth'
\`\`\`

**Solution:**
- Verify dual_auth directory is in your project
- Ensure \`__init__.py\` files exist in all package directories
- Check Python path: \`export PYTHONPATH="\${PYTHONPATH}:/path/to/your/project"\`

#### **Issue 2: Configuration Error**

\`\`\`
ConfigurationError: Environment variable 'AGENT_CLIENT_ID' is required
\`\`\`

**Solution:**
- Verify all required environment variables are set
- Check for typos in variable names
- Ensure \`.env\` file is being loaded

#### **Issue 3: Secrets Backend Error**

\`\`\`
SecretsBackendError: AWS secret 'dual-auth/AGENT_CLIENT_SECRET' not found
\`\`\`

**Solution:**
- Verify secret exists in secrets manager
- Check secret naming matches prefix + key name
- Verify IAM permissions for secrets access

#### **Issue 4: JWT Signature Verification Failed**

\`\`\`
ValueError: Act JWT verification failed: InvalidSignatureError
\`\`\`

**Solutions:**
- Verify \`APP_PUBLIC_KEY_PATH\` points to correct public key
- Check key matches the private key used for signing
- Ensure key format is PEM

#### **Issue 5: Token Missing Act Claim**

\`\`\`
Token received but missing 'act' claim
\`\`\`

**Solution by vendor:**

**Keycloak:**
- Verify protocol mapper is configured
- Check mapper is added to client scope

**Auth0:**
- Verify Credentials Exchange Action is deployed
- Check Action is enabled

**Okta:**
- Verify custom claim expression: \`clientAssertion.claims.act\`
- Check claim is set to include in Access Token

#### **Issue 6: EntraID Two Headers**

\`\`\`
API returns 401 even with valid token
\`\`\`

**Solution:**
- Verify resource server expects \`X-Act-Assertion\` header
- Check \`token_response.act_assertion\` is not None
- Ensure using dual-auth API client (handles headers automatically)

#### **Issue 7: HTTPS Required Error**

\`\`\`
ValueError: API URL must use HTTPS
\`\`\`

**Solution:**
- Change \`http://\` to \`https://\` in all URLs
- For local development: Use self-signed certificates or tunneling (ngrok)

<br>

## **Reference: Complete Examples**

### **Example 1: Flask Application with In-Session Agent**

\`\`\`python
from flask import Flask, session, redirect, url_for, jsonify
from dual_auth import (
    get_config, get_vendor, ConfigurationError, SecretsBackendError,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, InSessionTokenRequest, InSessionAPICall
)
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

@app.route('/api/agent/analyze-finances', methods=['POST'])
def analyze_finances():
    """Agent endpoint: Analyze user's finances."""
    
    # 1. Verify user authenticated
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # 2. Extract human identity
        user_session = UserSession(
            user_email=session['user']['email'],
            user_name=session['user']['name'],
            user_id=session['user']['id']
        )
        
        sender = HybridSender()
        act = sender.extract_act_from_session(user_session)
        
        # Log with IAM identifier (not PII)
        logger.info(
            "Finance analysis requested",
            extra={'human_id': act['sub'], 'event': 'agent_task_start'}
        )
        
        # 3. Create adapter and get token
        adapter = get_adapter()
        token_request = InSessionTokenRequest(adapter)
        
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        
        # 4. Make API calls
        client = InSessionAPICall(timeout=30)
        
        response = client.call_api(
            method='GET',
            api_url=os.environ['API_URL'],
            token_response=token_response,
            params={'user_id': session['user']['id']}
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'API call failed'}), response.status_code
        
        financial_data = response.json()
        
        # 5. Analyze with AI (agent logic)
        analysis = {
            'total_assets': sum(financial_data.get('assets', [])),
            'total_liabilities': sum(financial_data.get('liabilities', [])),
            'net_worth': sum(financial_data.get('assets', [])) - 
                         sum(financial_data.get('liabilities', []))
        }
        
        logger.info(
            "Finance analysis completed",
            extra={'human_id': act['sub'], 'event': 'agent_task_complete'}
        )
        
        return jsonify(analysis), 200
        
    except (ConfigurationError, SecretsBackendError) as e:
        logger.error(f"Configuration error: {e}")
        return jsonify({'error': 'Configuration error'}), 500
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
\`\`\`

### **Example 2: FastAPI Application**

\`\`\`python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, Auth0Adapter, OktaAdapter, EntraIDAdapter,
    HybridSender, UserSession, InSessionTokenRequest, InSessionAPICall
)
import os

app = FastAPI(title="dual-auth Agent Service")
security = HTTPBearer()

class AgentRequest(BaseModel):
    user_email: str
    user_name: str
    user_id: str
    task: str
    parameters: dict = {}

def get_adapter():
    """Get adapter for configured vendor."""
    config = get_config()
    vendor = get_vendor()
    
    adapters = {
        'keycloak': KeycloakAdapter,
        'auth0': Auth0Adapter,
        'okta': OktaAdapter,
        'entraid': EntraIDAdapter
    }
    
    return adapters[vendor](config)

@app.post("/api/agent/task")
async def execute_agent_task(
    request: AgentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Execute agent task with dual-subject authorization."""
    
    try:
        # 1. Extract act
        user_session = UserSession(
            user_email=request.user_email,
            user_name=request.user_name,
            user_id=request.user_id
        )
        
        sender = HybridSender()
        act = sender.extract_act_from_session(user_session)
        
        # 2. Create agent and get token
        adapter = get_adapter()
        token_request = InSessionTokenRequest(adapter)
        
        token_response = token_request.request_token(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            act=act,
            scope=['finance.read']
        )
        
        # 3. Execute task
        client = InSessionAPICall(timeout=30)
        result = await execute_task(
            client,
            token_response,
            request.task,
            request.parameters
        )
        
        return {
            "status": "success",
            "task": request.task,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_task(client, token_response, task, parameters):
    """Execute specific task."""
    # Implement task logic here
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
\`\`\`

<br>

## **Next Steps**

After completing this guide, you should:

1. ✅ Have dual-auth integrated into your application
2. ✅ Be able to request dual-subject tokens
3. ✅ Be able to make authorized API calls
4. ✅ Understand in-session and out-of-session flows
5. ✅ Be ready for production deployment with secrets management

**Recommended Next Actions:**

1. **Review Security:** Audit logging, secrets management, error handling
2. **Performance Testing:** Load test token requests and API calls
3. **Monitoring:** Set up alerts for token failures, API errors
4. **Documentation:** Document your specific implementation
5. **Team Training:** Train team on dual-auth concepts

<br>

## **Support Resources**

- **IAM Configuration Guides:** See individual guides for Keycloak, Auth0, Okta, EntraID
- **Code Documentation:** Review inline documentation in dual-auth source files
- **Changelog:** See \`CHANGELOG.md\` for update and change log details

<br>
<br>
