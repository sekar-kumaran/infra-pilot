# ADR-007: GitOps CI/CD Direction

## Status
Accepted

## Context
We need secure and auditable deployments.

## Decision
Use GitHub Actions for CI (build, test, container image). Use Argo CD (or Flux) in Kubernetes to pull those images and helm charts into the cluster.

## Consequences
- No direct push from CI to Production Kubernetes.
- Changes to production state require a git commit.
