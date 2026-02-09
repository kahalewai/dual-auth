<div align="center">

<img width="369" height="418" alt="dual-auth1" src="https://github.com/user-attachments/assets/4009184b-720e-4cfe-8725-e864d58e3cde" />

<br>

[![AGBAC](https://img.shields.io/badge/AGBAC-v1.0.0-blue)](https://github.com/kahalewai/agbac)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-red.svg)](https://github.com/kahalewai/dual-auth)


</div>

<br>

## Intro

Dual-Auth is the v1 reference implementation of AGent Based Access Control for system/application layer implementation of dual-subject authorization for AI agents and humans. The goal of dual-auth v1 is to demonstrate that dual-subject security capabilities can be implemented today using existing enterprise IAM platforms without external policy engines or new IAM infrastructure. While v1 is a sub-set of the full AGBAC specification, it is production ready to implement dual-subject control. Each IAM Configuration Guide shows how dual-subject authorization can be implemented using native configuration features of a specific identity provider. Applications and Agents are updated to become dual-subject aware (human AND agent identities).

Dual-Auth is intended to:
* Make dual-subject authorization tangible and adoptable
* Enforce dual-subject authorization (human + agent)
* Apply at the system/application boundary
* Provide clear, auditable attribution
* Show compatibility with existing IAM investments
* Support production deployments with cloud secrets management
* Provide a starting point for future implementations
* Encourage experimentation and feedback

<br>

## How dual-auth Works

Implementing dual-subject authorization requires that your Application/Agent becomes dual-subject aware AND your existing IAM Solution is configured to support AGBAC. The dual-auth library is used to make your Application/Agent dual-subject aware. The IAM Configuration Guides will walk you through configuring your IAM Solution. Each implementation enforces the same core requirement:

<br>

> An AI agent may access a system on behalf of a human user only if both agent and human are independently authorized.

<br>

The concept of dual-auth focuses on system-level access control, showing that:

* AI agents can be represented as first-class identities
* Human principals remain the source of authority
* Tokens can carry dual-subject identity
* Access decisions can require independent authorization
* Delegation is explicit, not implicit
* Agents can become aware of the associated human user
* Authorization is enforced before system access
* Audit records reflect both subjects

<br>

**Key Characteristics**

| Aspect              | Scope                               |
| ------------------  | ----------------------------------- |
| Access granularity  | System/application level            |
| Identity types      | Human + agent                       |
| Authorization       | Role-based intersection             |
| Delegation          | Explicit                            |
| Enforcement         | Existing IAM mechanisms             |
| IAM Code required   | None or minimal configuration logic |
| Agent Code required | Minimal to moderate updates to code |

<br>

**Conceptual Flow**

```
Human → AI Agent → Identity Platform → Target System
   |         |            |
   |         |            +-- Issues dual-subject token
   |         |
   |         +-- Receives human identity; requests token
   |
   +-- Authenticates to application; initiates agentic workflow
```

Access is permitted only when both subjects are authorized.

<br>

## Quick Start

### Installation

```bash
# Install Dual-Auth
pip install dual-auth

# Optional: Install cloud secrets management
pip install boto3                          # AWS
pip install google-cloud-secret-manager    # GCP
pip install azure-identity azure-keyvault-secrets  # Azure
pip install hvac                           # HashiCorp Vault
```

### Basic Usage

```python
from dual_auth import (
    get_config, get_vendor,
    KeycloakAdapter, HybridSender, UserSession,
    InSessionTokenRequest, InSessionAPICall
)

# 1. Load configuration (auto-detects secrets backend)
config = get_config()

# 2. Create adapter for your IAM vendor
adapter = KeycloakAdapter(config)

# 3. Extract human identity from session
user_session = UserSession(
    user_email="alice@example.com",
    user_name="Alice Smith",
    user_id="iam-user-id-12345"
)
sender = HybridSender()
act = sender.extract_act_from_session(user_session)

# 4. Request dual-subject token
token_request = InSessionTokenRequest(adapter)
token_response = token_request.request_token(
    agent_id="finance-agent",
    act=act,
    scope=["finance.read"]
)

# 5. Make API calls
client = InSessionAPICall()
response = client.call_api(
    method="GET",
    api_url="https://api.example.com/data",
    token_response=token_response
)
```

For complete setup instructions, see the [Python Implementation Guide](https://github.com/kahalewai/dual-auth/blob/main/python/README.md).

<br>

## Package Structure

```
dual_auth/
├── __init__.py              # Main exports
├── config.py                # Configuration with secrets backends
├── adapters/
│   ├── base_adapter.py      # Base adapter class
│   ├── keycloak_adapter.py  # Keycloak support
│   ├── auth0_adapter.py     # Auth0 support
│   ├── okta_adapter.py      # Okta support
│   └── entraid_adapter.py   # Microsoft EntraID support
├── session/
│   ├── hybrid_sender.py     # Human identity extraction
│   ├── insession_token_request.py
│   └── outofsession_token_request.py
└── api/
    ├── insession_api_call.py
    └── outofsession_api_call.py
```

<br>

## Secrets Management

dual-auth includes built-in support for cloud secrets management:

| Backend | Use Case | Configuration |
|---------|----------|---------------|
| `env` | Development/Testing | `DUAL_AUTH_SECRETS_BACKEND=env` (default) |
| `aws` | AWS deployments | `DUAL_AUTH_SECRETS_BACKEND=aws` |
| `gcp` | GCP deployments | `DUAL_AUTH_SECRETS_BACKEND=gcp` |
| `azure` | Azure deployments | `DUAL_AUTH_SECRETS_BACKEND=azure` |
| `vault` | Multi-cloud/on-premises | `DUAL_AUTH_SECRETS_BACKEND=vault` |

```python
from dual_auth import get_config

# Development (environment variables)
config = get_config()

# Production (AWS Secrets Manager)
config = get_config(secrets_backend='aws')

# Production (HashiCorp Vault)
config = get_config(secrets_backend='vault')
```

See the [Python Implementation Guide](https://github.com/kahalewai/dual-auth/blob/main/python/README.md) for detailed setup.

<br>

## Available IAM Configuration Guides

IAM Configuration Guides explain how to configure a specific IAM vendor to support dual-auth:

* **Keycloak**: [Keycloak IAM Configuration Guide](https://github.com/kahalewai/dual-auth/blob/main/docs/iam_guide_keycloak.md)
* **Auth0**: [Auth0 IAM Configuration Guide](https://github.com/kahalewai/dual-auth/blob/main/docs/iam_guide_auth0.md)
* **Okta**: [Okta IAM Configuration Guide](https://github.com/kahalewai/dual-auth/blob/main/docs/iam_guide_okta.md)
* **EntraID**: [EntraID IAM Configuration Guide](https://github.com/kahalewai/dual-auth/blob/main/docs/iam_guide_entraid.md)

IAM Guides and their resulting implementations are independent and do not depend on each other. If your organization uses multiple IAM platforms, dual-auth can be implemented in parallel while preserving consistent security semantics.

<br>

## Implementation Guide

The Implementation Guide provides step-by-step instructions for integrating dual-auth into your applications and agents:

* **Python**: [Python Implementation Guide](https://github.com/kahalewai/dual-auth/blob/main/python/README.md)
* **TypeScript**: (Coming Soon)
* **Java**: (Coming Soon)

<br>

## Works with Your Existing Enterprise IAM Solution

dual-auth was designed to work with your existing enterprise IAM solution:

* Follow best practices; implement into non-prod first to test and validate
* Configure your IAM solution to support dual-auth (follow the IAM guides)
* Use existing organizational authorization approval workflows
* Configure system/application access policies once approved
* Your existing IAM solution will process/log requests for humans and agents (dual-subject)
* Update your application and agent code to become dual-subject aware (follow the implementation guide)
* Works with single or multi-agent systems for most providers

<br>

| Agent Authorized | Human Authorized | Result |
| ---------------- | ---------------- | ------ |
| ✅               | ✅               | ALLOW  |
| ❌               | ✅               | DENY   |
| ✅               | ❌               | DENY   |
| ❌               | ❌               | DENY   |

<br>

* This will not interfere with or impact existing authorizations for humans only (different tokens)
* You will be able to log agent requests on behalf of human users (security attribution)
* Dual-subject authorizations are maintained the same way as traditional human-only authorizations

<br>

## Multi-Agent and Out-of-Session Scenarios

dual-auth supports multi-agent workflows, out-of-session agents, and async execution with all supported providers. The dual-auth package provides:

* **In-Session**: Agent runs in same process as application; act passed in-memory
* **Out-of-Session**: Agent runs remotely; act passed as signed JWT over HTTPS

```python
# Out-of-session: Application creates signed JWT
sender = HybridSender(private_key_pem='/path/to/private-key.pem')
act_jwt = sender.prepare_out_of_session_act(
    act=act,
    agent_endpoint="https://agent.example.com/invoke",
    ttl_seconds=60
)

# Out-of-session: Agent verifies JWT and requests token
token_request = OutOfSessionTokenRequest(
    adapter=adapter,
    app_public_key_path='/path/to/public-key.pem',
    expected_issuer='your-app',
    expected_audience='https://agent.example.com/invoke'
)
token_response = token_request.request_token_from_jwt(act_jwt, agent_id, scope)
```

See the [Implementation Guide](./dual_auth_implementation_guide.md#step-7-implement-out-of-session-agent) for complete out-of-session setup.

<br>

## Out of Scope v1.0.1

dual-auth does not:
* Provide object-level authorization
* Introduce centralized policy engines
* Perform RFC 8693 token exchange
* Support dynamic delegation
* Provide automated IAM provisioning

These capabilities are planned for v2.0.0

<br>

## Version History

| Version | Changes |
|---------|---------|
| 1.0.1 | Added cloud secrets management (AWS, GCP, Azure, Vault) |
| 1.0.0 | Initial release with Keycloak, Auth0, Okta, EntraID support |

<br>
<br>
