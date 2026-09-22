# Knowledge Index

The `knowledge/` directory is the project's architectural memory and source of truth.
Knowledge describes the intended architecture and confirmed state. Source code is the authority for actual implementation state. Tests are the authority for verified behavior.

If documentation and source code disagree:
1. identify the discrepancy
2. do not silently rewrite either
3. report it
4. resolve it through an explicit change

## How to consume the knowledge base

To prevent repeated full-repository analysis and unnecessary context consumption, follow this read order:

**ALWAYS READ:**
- 00_PROJECT_CHARTER.md
- 03_ENGINEERING_RULES.md
- 18_PHASE_ROADMAP.md
- phase-status/CURRENT_STATE.md

**THEN READ ONLY THE CONTRACTS RELEVANT TO THE CURRENT TASK.**

For example:

### Database task
Read:
- 06_DATABASE_CONTRACT.md
- 07_API_CONTRACT.md
- 13_TESTING_CONTRACT.md
- 05_SECURITY_RULES.md

### Alert ingestion task
Read:
- 08_EVENT_CONTRACT.md
- 10_INTEGRATION_CONTRACT.md
- 06_DATABASE_CONTRACT.md
- 14_OBSERVABILITY_CONTRACT.md
- 13_TESTING_CONTRACT.md

### Automation task
Read:
- 09_AUTOMATION_CONTRACT.md
- 10_INTEGRATION_CONTRACT.md
- 05_SECURITY_RULES.md
- 14_OBSERVABILITY_CONTRACT.md
- 13_TESTING_CONTRACT.md
