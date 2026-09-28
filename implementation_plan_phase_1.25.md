# Phase 1.25 Implementation Plan: Enterprise Governance, RBAC, Policy Simulation & Safe Workflow Control

## Objective
Harden InfraPilot's governance capabilities by adding resource-level Role-Based Access Control (RBAC), a safe Policy Simulation Engine, Workflow Resumption, and Concurrency Controls. This will ensure InfraPilot is a true enterprise-grade Infrastructure Operations Control Plane.

## Steps

### 1. Database Authorization Model (RBAC)
- Create `apps/api/app/models/auth.py` with models: `Role`, `Permission`, `UserRole`, `RolePermission`, `ResourceScope`.
- Add standard permissions (e.g., `resource.read`, `automation.execute`, `provider.manage`).
- Update Alembic migrations to generate the tables.

### 2. Authorization Service
- Implement `apps/api/app/services/authorization.py` to evaluate user roles, scopes, and permissions against specific `InfrastructureResource` instances.
- Integrate the authorization service into the main FastAPI dependencies.

### 3. Policy Engine Hardening & Simulation
- Enhance `PolicyEngine` (`apps/api/app/services/policy_engine.py`) to evaluate complex contextual scenarios (actor, role, risk, incident, workflow).
- Implement `POST /api/v1/policies/simulate` endpoint to dry-run operations and return explicit decisions (ALLOWED, REQUIRES_APPROVAL, DENIED).
- Create the Policy Simulator UI at `apps/web/src/app/(protected)/policies/simulator/page.tsx`.

### 4. Workflow Resumption & Concurrency Control
- Implement robust DB locking on active workflows affecting a specific resource (in `WorkflowEngine`).
- Create `POST /api/v1/workflows/executions/{execution_id}/resume` to intelligently safely resume interrupted workflows.
- Enhance UI to only show "Resume" controls on failed/paused resumable workflows.

### 5. Cross-Provider Capability & Action Validation
- Enhance `ActionRegistry` and `ProviderResolver` to enforce strict action capabilities (e.g. rejecting operations if the provider capabilities drop or the action is no longer registered).
- Dynamic declaration of `execution_provider` and `verification_provider`.

### 6. Approval & Audit Hardening
- Strengthen `Approval` lifecycle mapping, enforcing expiration and matching against material resource changes.
- Implement central redaction logic for `AuditEvent` so secrets/tokens are never persisted in the timeline.

### 7. UI Dashboards
- Create an operations Overview Dashboard at `apps/web/src/app/(protected)/dashboard/page.tsx` showing active incidents, running workflows, pending approvals, and provider health.
- Incrementally upgrade the Provider and Resource explorers to respect the new RBAC rules natively.

### 8. Testing & Documentation
- Write `scripts/e2e_test_phase_1_25.py` to cover Scenario A (Allowed), B (Approval), C (Denied), D (Conflict), E (Resume), and F (Cross-Provider).
- Produce corresponding architectural markdown documentation in `/docs`.
