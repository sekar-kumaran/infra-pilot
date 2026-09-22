# CI/CD Contract

## Purpose
Continuous Integration and Deployment rules.

## GitOps Technology
- **Argo CD** is the selected GitOps controller.
- Flux is NOT part of the initial architecture. Introducing Flux requires a future ADR and explicit architectural approval.

## Decisions
- Pipeline stages: Lint -> Test -> Security Scan -> Build Image -> Publish -> Deploy to Staging.
- Deployment to Production requires manual approval tag or specific branch strategy.

## Current Status
- Setup pending. Architecture Locked.
