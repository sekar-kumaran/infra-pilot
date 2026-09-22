# Automation Contract

## Purpose
Define how InfraPilot interfaces with external automation engines safely.

## Automation Safety
Every automation must eventually have:
- unique automation ID
- version
- owner
- risk level
- allowed targets
- required permissions
- timeout
- retry policy
- idempotency strategy
- rollback strategy
- verification strategy
- audit trail

## Risk Levels
- **LOW**: may be automatically executed if policy permits
- **MEDIUM**: policy-controlled, possibly approval-gated
- **HIGH**: explicit human approval
- **CRITICAL**: explicit human approval + strong safeguards

## Decisions
- Execution must run in isolated environments/processes.
- Must capture `stdout`, `stderr`, and exit codes.
- Idempotent execution only.

## Current Status
- Phase 0: Defined and Locked.
