<div align="center">

# Dual Auth Secrets Management Guide
Recommended for Production Implementations

</div>

<br>
<br>

## Overview

Dual Auth v1.0.1 introduces pluggable secrets management backends, allowing you to choose the most appropriate secrets storage for your environment:

| Backend | Use Case | Required Package |
|---------|----------|------------------|
| **env** (default) | Development, testing, simple deployments | None |
| **aws** | AWS production deployments | `boto3` |
| **gcp** | GCP production deployments | `google-cloud-secret-manager` |
| **azure** | Azure production deployments | `azure-identity`, `azure-keyvault-secrets` |
| **vault** | Multi-cloud, on-premises, enterprise | `hvac` |

<br>

## How Users Choose Their Approach

### Method 1: Environment Variable (Recommended for Automation)

Set the `DUAL_AUTH_SECRETS_BACKEND` environment variable:

```bash
# For development (default - no need to set)
export DUAL_AUTH_SECRETS_BACKEND=env

# For AWS
export DUAL_AUTH_SECRETS_BACKEND=aws

# For GCP
export DUAL_AUTH_SECRETS_BACKEND=gcp

# For Azure
export DUAL_AUTH_SECRETS_BACKEND=azure

# For HashiCorp Vault
export DUAL_AUTH_SECRETS_BACKEND=vault
```

### Method 2: Code Parameter (For Explicit Control)

Pass the backend directly to `get_config()`:

```python
from dual_auth import get_config

# Use environment variables
config = get_config(secrets_backend='env')

# Use AWS Secrets Manager
config = get_config(secrets_backend='aws')

# Use GCP Secret Manager
config = get_config(secrets_backend='gcp')

# Use Azure Key Vault
config = get_config(secrets_backend='azure')

# Use HashiCorp Vault
config = get_config(secrets_backend='vault')
```

**Note:** The `secrets_backend` parameter overrides the `DUAL_AUTH_SECRETS_BACKEND` environment variable.

<br>

## Backend Configuration Details

### 1. Environment Variables Backend (Default)

**Best for:** Development, testing, CI/CD pipelines, simple deployments

**Setup:** No additional configuration required.

**Required Environment Variables by Vendor:**

| Vendor | Environment Variables |
|--------|----------------------|
| Keycloak | `KEYCLOAK_TOKEN_URL`, `AGENT_CLIENT_ID`, `AGENT_CLIENT_SECRET` |
| Auth0 | `AUTH0_TOKEN_URL`, `AGENT_CLIENT_ID`, `AGENT_CLIENT_SECRET`, `API_AUDIENCE` |
| Okta | `OKTA_TOKEN_URL`, `AGENT_CLIENT_ID`, `AGENT_CLIENT_SECRET`, `API_AUDIENCE` |
| EntraID | `ENTRAID_TOKEN_URL`, `AGENT_CLIENT_ID`, `AGENT_CLIENT_SECRET`, `API_SCOPE`, `APP_PRIVATE_KEY_PATH`, `APP_ID`, `API_AUDIENCE` |

**Example (Keycloak):**
```bash
export DUAL_AUTH_VENDOR=keycloak
export AGENT_CLIENT_ID=finance-agent
export AGENT_CLIENT_SECRET=your-secret-here
export KEYCLOAK_TOKEN_URL=https://keycloak.example.com/realms/prod/protocol/openid-connect/token
```

<br>

### 2. AWS Secrets Manager Backend

**Best for:** AWS deployments (EC2, ECS, Lambda, EKS)

**Install:** `pip install boto3`

**Backend Configuration:**

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `DUAL_AUTH_AWS_REGION` | No | `us-east-1` | AWS region |
| `DUAL_AUTH_AWS_SECRET_PREFIX` | No | `dual-auth/` | Prefix for secret names |

**Authentication:** Uses boto3's credential chain:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- Shared credential file (`~/.aws/credentials`)
- IAM role (EC2, ECS, Lambda)

**Secret Naming Convention:**
```
{prefix}{KEY_NAME}
Example: dual-auth/AGENT_CLIENT_SECRET
```

**Creating Secrets in AWS:**
```bash
# Create individual secrets
aws secretsmanager create-secret \
  --name dual-auth/AGENT_CLIENT_ID \
  --secret-string "finance-agent"

aws secretsmanager create-secret \
  --name dual-auth/AGENT_CLIENT_SECRET \
  --secret-string "your-secret-here"

aws secretsmanager create-secret \
  --name dual-auth/KEYCLOAK_TOKEN_URL \
  --secret-string "https://keycloak.example.com/realms/prod/protocol/openid-connect/token"
```

**Example Usage:**
```bash
export DUAL_AUTH_SECRETS_BACKEND=aws
export DUAL_AUTH_AWS_REGION=us-west-2
export DUAL_AUTH_VENDOR=keycloak
```

```python
from dual_auth import get_config
config = get_config()  # Automatically uses AWS
```

<br>

### 3. GCP Secret Manager Backend

**Best for:** GCP deployments (Compute Engine, Cloud Run, GKE)

**Install:** `pip install google-cloud-secret-manager`

**Backend Configuration:**

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `DUAL_AUTH_GCP_PROJECT` | **Yes** | - | GCP project ID |
| `DUAL_AUTH_GCP_SECRET_PREFIX` | No | `dual-auth-` | Prefix for secret names |

**Authentication:** Uses Application Default Credentials:
- `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- `gcloud auth application-default login`
- Service account on GCP

**Secret Naming Convention:**
```
{prefix}{key-name-lowercase-with-hyphens}
Example: AGENT_CLIENT_SECRET -> dual-auth-agent-client-secret
```

**Creating Secrets in GCP:**
```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "finance-agent" | gcloud secrets create dual-auth-agent-client-id --data-file=-
echo -n "your-secret" | gcloud secrets create dual-auth-agent-client-secret --data-file=-
echo -n "https://keycloak.example.com/..." | gcloud secrets create dual-auth-keycloak-token-url --data-file=-
```

**Example Usage:**
```bash
export DUAL_AUTH_SECRETS_BACKEND=gcp
export DUAL_AUTH_GCP_PROJECT=my-project-id
export DUAL_AUTH_VENDOR=keycloak
```

<br>

### 4. Azure Key Vault Backend

**Best for:** Azure deployments (VMs, App Service, Functions, AKS)

**Install:** `pip install azure-identity azure-keyvault-secrets`

**Backend Configuration:**

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `DUAL_AUTH_AZURE_VAULT_URL` | **Yes** | - | Key Vault URL |
| `DUAL_AUTH_AZURE_SECRET_PREFIX` | No | `dual-auth-` | Prefix for secret names |

**Authentication:** Uses DefaultAzureCredential:
- Environment variables (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
- Managed Identity
- Azure CLI (`az login`)

**Secret Naming Convention:**
```
{prefix}{key-name-lowercase-with-hyphens}
Example: AGENT_CLIENT_SECRET -> dual-auth-agent-client-secret
```

**Creating Secrets in Azure:**
```bash
# Create Key Vault (if needed)
az keyvault create --name my-dual-auth-vault --resource-group my-rg --location eastus

# Create secrets
az keyvault secret set --vault-name my-dual-auth-vault \
  --name dual-auth-agent-client-id --value "finance-agent"

az keyvault secret set --vault-name my-dual-auth-vault \
  --name dual-auth-agent-client-secret --value "your-secret"

az keyvault secret set --vault-name my-dual-auth-vault \
  --name dual-auth-keycloak-token-url --value "https://keycloak.example.com/..."
```

**Example Usage:**
```bash
export DUAL_AUTH_SECRETS_BACKEND=azure
export DUAL_AUTH_AZURE_VAULT_URL=https://my-dual-auth-vault.vault.azure.net/
export DUAL_AUTH_VENDOR=keycloak
```

<br>

### 5. HashiCorp Vault Backend

**Best for:** Multi-cloud, on-premises, enterprise with centralized secrets management

**Install:** `pip install hvac`

**Backend Configuration:**

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `VAULT_ADDR` | **Yes** | - | Vault server URL |
| `VAULT_TOKEN` | * | - | Auth token (Method 1) |
| `VAULT_ROLE_ID` | * | - | AppRole role ID (Method 2) |
| `VAULT_SECRET_ID` | * | - | AppRole secret ID (Method 2) |
| `VAULT_K8S_ROLE` | * | `dual-auth` | K8s auth role (Method 3) |
| `VAULT_NAMESPACE` | No | - | Vault Enterprise namespace |
| `DUAL_AUTH_VAULT_MOUNT` | No | `secret` | Secrets engine mount |
| `DUAL_AUTH_VAULT_PATH_PREFIX` | No | `dual-auth/` | Path prefix |

*At least one authentication method required

**Authentication Methods (tried in order):**
1. Token (`VAULT_TOKEN`)
2. AppRole (`VAULT_ROLE_ID` + `VAULT_SECRET_ID`)
3. Kubernetes (auto-detected in K8s pods)

**Secret Naming Convention:**
```
{mount}/data/{prefix}{key-name-lowercase-with-hyphens}
Example: secret/data/dual-auth/agent-client-secret
```

**Creating Secrets in Vault:**
```bash
# Using KV v2 (recommended)
vault kv put secret/dual-auth/agent-client-id value="finance-agent"
vault kv put secret/dual-auth/agent-client-secret value="your-secret"
vault kv put secret/dual-auth/keycloak-token-url value="https://keycloak.example.com/..."

# Or store all in one secret (JSON)
vault kv put secret/dual-auth/config \
  AGENT_CLIENT_ID="finance-agent" \
  AGENT_CLIENT_SECRET="your-secret" \
  KEYCLOAK_TOKEN_URL="https://keycloak.example.com/..."
```

**Example Usage:**
```bash
export DUAL_AUTH_SECRETS_BACKEND=vault
export VAULT_ADDR=https://vault.example.com:8200
export VAULT_TOKEN=hvs.your-token-here
export DUAL_AUTH_VENDOR=keycloak
```

<br>

## Complete Configuration Reference

### Control Variables (Always Environment Variables)

These variables control dual-auth behavior and are always read from environment variables:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `DUAL_AUTH_SECRETS_BACKEND` | `env`, `aws`, `gcp`, `azure`, `vault` | `env` | Secrets backend to use |
| `DUAL_AUTH_VENDOR` | `keycloak`, `auth0`, `okta`, `entraid` | `keycloak` | IAM vendor |

### Secrets by Vendor

These are the secrets that must be stored in your chosen backend:

**Keycloak:**
- `KEYCLOAK_TOKEN_URL` - Token endpoint URL
- `AGENT_CLIENT_ID` - Agent's client ID
- `AGENT_CLIENT_SECRET` - Agent's client secret

**Auth0:**
- `AUTH0_TOKEN_URL` - Token endpoint URL
- `AGENT_CLIENT_ID` - Agent's client ID
- `AGENT_CLIENT_SECRET` - Agent's client secret
- `API_AUDIENCE` - API audience/identifier

**Okta:**
- `OKTA_TOKEN_URL` - Token endpoint URL
- `AGENT_CLIENT_ID` - Agent's client ID
- `AGENT_CLIENT_SECRET` - Agent's client secret
- `API_AUDIENCE` - API audience

**EntraID:**
- `ENTRAID_TOKEN_URL` - Token endpoint URL
- `AGENT_CLIENT_ID` - Agent's client ID
- `AGENT_CLIENT_SECRET` - Agent's client secret
- `API_SCOPE` - API scope (e.g., `https://api.example.com/.default`)
- `APP_PRIVATE_KEY_PATH` - Path to RSA private key file
- `APP_ID` - Application identifier
- `API_AUDIENCE` - API audience for act assertions

<br>

## Migration Guide

### From Environment Variables to Cloud Secrets Manager

1. **Create secrets in your cloud provider** using the naming conventions above

2. **Install required package:**
   ```bash
   # AWS
   pip install boto3
   
   # GCP
   pip install google-cloud-secret-manager
   
   # Azure
   pip install azure-identity azure-keyvault-secrets
   
   # Vault
   pip install hvac
   ```

3. **Update environment variables:**
   ```bash
   # Remove secret values
   unset AGENT_CLIENT_SECRET
   
   # Set backend
   export DUAL_AUTH_SECRETS_BACKEND=aws  # or gcp, azure, vault
   
   # Set backend-specific config
   export DUAL_AUTH_AWS_REGION=us-west-2  # AWS example
   ```

4. **No code changes required** - `get_config()` automatically uses the new backend

<br>

## Error Handling

```python
from dual_auth import get_config, ConfigurationError, SecretsBackendError

try:
    config = get_config()
except SecretsBackendError as e:
    print(f"Secrets backend error ({e.backend}): {e}")
    # Handle missing secrets, auth failures, etc.
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Handle invalid vendor, invalid backend, etc.
```

<br>

## Security Best Practices

1. **Use environment variables only for development** - Switch to a secrets manager for production

2. **Use IAM roles over access keys** - Let AWS/GCP/Azure handle authentication via instance roles

3. **Rotate secrets regularly** - All backends support secret versioning/rotation

4. **Audit access** - All cloud secrets managers provide audit logging

5. **Least privilege** - Grant only the permissions needed to read specific secrets
