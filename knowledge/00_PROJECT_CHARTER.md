# InfraPilot Project Charter

## Purpose
InfraPilot is an independent infrastructure operations control plane designed to unify infrastructure inventory, observability, alert ingestion, incident management, and automated remediation.

## Scope
- Centralized ingestion and normalization of alerts.
- Correlation of incidents across various monitoring platforms.
- Policy-controlled automation with human approvals.
- Full closed-loop resolution including verification and auditing.
- It is NOT a replacement for underlying DevOps execution tools (Terraform, Ansible, Kubernetes), but rather an orchestration layer above them.

## Decisions
- Unified web interface for human operators.
- Modular monolith pattern for backend API with asynchronous task workers.
- Strict policy enforcement layer.

## Constraints
- No direct execution by AI layer; policies always dictate safety constraints.
- Real-time communication via WebSockets for operators.

## Current Status
- Phase 0: Foundation Setup.
