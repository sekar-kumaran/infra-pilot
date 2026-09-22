# ADR-006: Kubernetes and Helm for Deployment

## Status
Accepted

## Context
Staging and Production environments need high availability and robust orchestration.

## Decision
Deploy InfraPilot using Kubernetes. Package configurations as Helm charts.

## Consequences
- Staging and Prod are scalable and self-healing.
- Requires k8s clusters for higher environments.
