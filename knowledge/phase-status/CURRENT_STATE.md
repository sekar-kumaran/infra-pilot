# InfraPilot Current State

## Current Phase
Phase 1 — Core Platform

## Phase Status
PHASE_1.15_IMPLEMENTED

## Completed
- Repository architecture
- Knowledge base
- Engineering contracts
- Security rules
- Architecture ADRs
- Docker development strategy
- CI foundation
- Event contract
- Provider adapter contract
- Argo CD GitOps decision
- Phase 1.1: Runtime & Configuration Foundation (FastAPI, Docker, Healthchecks)
- Phase 1.2: PostgreSQL + SQLAlchemy + Alembic Foundation
- Phase 1.3: Identity & Authentication (Argon2id, JWT)
- Phase 1.4: RBAC, Authorization, Audit Foundation
- Phase 1.5: Infrastructure Resource & Inventory Foundation
- Phase 1.6: Integration Adapter & Provider Framework
- Phase 1.7: Event Ingestion & Normalization
- Phase 1.8: Incident Engine & State Machine
- Phase 1.9: Notification & Operational Intelligence Foundation
- Phase 1.10: Automation, Playbooks & Policy Engine Foundation
- Phase 1.11: Frontend Operations Console & Full Backend Integration
- Phase 1.12: Prometheus Integration & Provider Framework Hardening
- Phase 1.13: Nagios Integration
- Phase 1.14: Real Ansible Automation Provider
- Phase 1.15: Real Kubernetes Automation Provider

## Phase 1.15 Details
- **Kubernetes is a REAL provider**: Interacts with Kubernetes API directly via REST instead of kubectl or mocked responses.
- **k3s Test Environment**: A real disposable k3s cluster is used in E2E tests for verification.
- **Strict Verification Logic**: High risk automation actions on Kubernetes are mandated to undergo policy and risk validation, and the execution relies on bounded polling to verify success.
- **Frontend Integration**: Kubernetes specific resources and details are visible in the executions panel.

## Not Yet Implemented
- Complete system E2E testing framework

## Current Architecture
InfraPilot is a FastAPI modular monolith serving a Next.js web UI via REST. Background operations and integrations run in isolated RabbitMQ + Celery workers. PostgreSQL stores application state. It orchestrates external systems (Prometheus, Nagios, Terraform, etc.) without replacing their specialized roles. Argo CD drives Kubernetes deployments. AI recommendations are strictly gated by a Policy Engine.

## Next Phase
Phase 2.0 — Launch Preparation

## Blocking Issues
None

## Architectural Decisions
- ADR-001: Monorepo Architecture
- ADR-002: Modular Monolith Plus Workers
- ADR-003: PostgreSQL as Application Database
- ADR-004: RabbitMQ and Celery
- ADR-005: Docker Compose for Development
- ADR-006: Kubernetes and Helm for Deployment
- ADR-007: GitOps CI/CD Direction
- ADR-008: Argo CD GitOps

## Last Updated
2026-09-23
