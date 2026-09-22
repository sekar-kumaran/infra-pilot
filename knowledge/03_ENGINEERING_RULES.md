# Engineering Rules

## Purpose
Mandatory rules for all code in InfraPilot.

## Scope
- Applies to all agents and engineers.

## Decisions
1. **Rule A - No Fake Functionality**: Never mock outside of tests. Never return success for failed operations.
2. **Rule B - No Premature Completion**: Feature includes implementation, tests, error handling, security, verification.
3. **Rule C - Contract First**: Define responsibility, inputs, outputs before coding.
4. **Rule D - No Giant Files**: Maintain cohesive modules. Split large files.
5. **Rule E - Real Error Handling**: No broad silent exceptions. Execution requires audit logs and ID.
6. **Rule F - Security by Default**: No hardcoded secrets. Use env vars.
7. **Rule G - AI Safety**: AI cannot directly execute unapproved changes.
8. **Rule H - Idempotency**: Automation must be idempotent.
9. **Rule I - Verification**: Every automated remediation requires a post-execution health check.
10. **Rule J - Document Decisions**: ADRs required for architecture changes.

## Current Status
- Enforced on all new pull requests and commits.
