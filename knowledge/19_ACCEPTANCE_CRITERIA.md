# Acceptance Criteria

## Purpose
Guidelines on when a story or task is considered acceptable.

## Phase 0 Acceptance Gates

### Architecture
- [x] Backend architecture locked
- [x] REST API locked
- [x] Modular monolith locked
- [x] Worker architecture locked
- [x] RabbitMQ/Celery locked
- [x] PostgreSQL responsibility locked
- [x] Observability responsibility locked
- [x] AI safety boundary locked
- [x] GitOps controller locked

### Contracts
- [x] Canonical RawEvent defined
- [x] Canonical Alert defined
- [x] Canonical Incident defined
- [x] IncidentEvent defined
- [x] State transitions defined
- [x] Provider adapter contract defined
- [x] Idempotency defined
- [x] Deduplication defined
- [x] Correlation contract defined

### Engineering
- [x] Knowledge index created
- [x] Current project state created
- [x] ADRs complete
- [x] No premature features
- [x] No fake integrations
- [x] No unresolved architecture alternatives

Phase 0 is accepted only when all required architectural gates are satisfied.

## General Implementation Examples
- API endpoint has unit and integration tests.
- Database migration downgrades successfully.
- Failure states are explicitly handled and logged.
- Audit records are generated for all state changes.
- Role-based authorization is enforced.
- Real integrations are verified against a live/test target.

## Current Status
- Phase 0 Gates Locked.
- Phase 1.1 (Runtime Foundation) Locked.
- Phase 1.2 (PostgreSQL Foundation) Locked.
- Phase 1.3 (Identity & Authentication) Locked.
- Phase 1.4 (RBAC, Authorization, Audit Foundation) Locked.
