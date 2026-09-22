# Security Rules

## Purpose
Define mandatory security practices for InfraPilot.

## Scope
- Secrets management, Authentication, Authorization, Auditing.

## Decisions
- All dangerous actions require Policy Engine approval.
- High-risk operations require human approval.
- RBAC is enforced at the API layer.
- Dependencies must be scanned.

## Security Considerations
- Never commit secrets.
- Use Kubernetes Secrets or Vault for production credentials.

## Current Status
- Enforced by design.
