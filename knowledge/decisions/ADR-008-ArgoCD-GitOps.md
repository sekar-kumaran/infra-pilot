# ADR-008: Argo CD GitOps

## Status
Accepted

## Context
We need a concrete decision on the GitOps controller for Kubernetes deployments, previously ambiguous between Argo CD and Flux.

## Decision
InfraPilot uses Argo CD for GitOps deployment synchronization.
Flux is not part of the initial architecture.
Introducing Flux requires a future ADR and explicit architectural approval.

## Consequences
- Kubernetes-native deployment management with a strong visual operational experience.
- Clear application synchronization model.
- Argo CD must be provisioned in the cluster before application workloads are deployed.
