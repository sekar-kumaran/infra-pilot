# Deployment Contract

## Purpose
Define environments and deployment strategies.

## GitOps Strategy
- **Argo CD** is the locked GitOps controller. Flux is not allowed without an ADR.

## Decisions
- Dev: Docker Compose.
- Staging: Kubernetes.
- Prod: Kubernetes + Helm via GitOps (Argo CD).

## Current Status
- Phase 0: Defined and Locked.
