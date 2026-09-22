# Event Contract

## Purpose
Rules for asynchronous event publishing, consumption, and the canonical incident lifecycle.

## Canonical Lifecycle
```text
External Signal
      ↓
Raw Event
      ↓
Normalized Alert
      ↓
Correlation
      ↓
Incident
      ↓
Diagnosis
      ↓
Recommendation
      ↓
Policy Decision
      ↓
Approval
      ↓
Automation Execution
      ↓
Verification
      ↓
Incident Resolution / Escalation
```

## Canonical Entities

### RawEvent
Represents the original payload received from an external integration.
- `event_id`
- `source`
- `source_type`
- `received_at`
- `occurred_at`
- `raw_payload`
- `correlation metadata`
- `deduplication metadata`
*(Original payload must be retained safely for troubleshooting/audit).*

### Alert
Represents a normalized operational signal. The schema must be provider-neutral.
- `alert_id`
- `source`
- `source_event_id`
- `severity`
- `status`
- `title`
- `description`
- `service`
- `host`
- `environment`
- `labels`
- `annotations`
- `occurred_at`
- `received_at`
- `fingerprint`
- `deduplication_key`

### Incident
Represents the operational problem rather than an individual alert.
- `incident_id`
- `title`
- `description`
- `severity`
- `status`
- `priority`
- `environment`
- `affected_resources`
- `related_alerts`
- `owner/team`
- `started_at`
- `acknowledged_at`
- `resolved_at`
- `correlation_reason`
- `root_cause_status`
- `remediation_status`

Valid lifecycle states: `OPEN`, `ACKNOWLEDGED`, `INVESTIGATING`, `DIAGNOSED`, `AWAITING_APPROVAL`, `REMEDIATING`, `VERIFYING`, `RESOLVED`, `ESCALATED`, `CLOSED`.
*(Invalid transitions must be rejected).*

### IncidentEvent
An append-only timeline model representing everything that happens to an incident (e.g., alert attached, correlation decision, diagnosis generated, approval requested, automation started, verification passed, incident resolved).

## Idempotency and Deduplication
- **Event idempotency**: The same external event must not create duplicate internal events.
- **Alert deduplication**: Repeated copies of the same alert must resolve to the same logical alert/fingerprint where appropriate.
- **Incident correlation**: Multiple related alerts may belong to one incident. (Rule-based for Phase 0; ML correlation later).

## Current Status
- Phase 0: Defined and Locked.
