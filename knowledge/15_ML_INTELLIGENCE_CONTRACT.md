# ML Intelligence Contract

## Purpose
Rules for the intelligence layer and AI safety.

## Scope
- Root cause analysis, correlation, remediation suggestions.

## AI Safety & Responsibilities
- **AI/ML must NOT directly execute infrastructure commands.**
- AI may generate: diagnosis, evidence ranking, anomaly score, probable root cause, recommended runbook, confidence score, explanation.
- AI may NOT directly: execute shell commands, run Terraform apply, modify Kubernetes, restart services, modify Puppet state, execute Ansible.
- The Policy Engine strictly controls execution. Destructive operations must never be automatically authorized by an AI recommendation alone.

## Architecture Flow
```text
Evidence
   ↓
Intelligence
   ↓
Diagnosis
   ↓
Recommendation
   ↓
Risk Assessment
   ↓
Policy Engine
   ↓
Approval if required
   ↓
Automation Engine
   ↓
Verification
```

## Current Status
- Phase 0: Defined and Locked.
