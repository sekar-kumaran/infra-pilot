# Kubernetes Integration

## Purpose
Manage k8s resources and observe cluster state.

## Scope
- Using k8s client library to read events, restart pods, scale deployments.

## Contracts
- Uses RBAC limited service accounts.
- Direct API interaction, not just wrapping `kubectl`.
