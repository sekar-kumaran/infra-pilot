import pytest
import uuid
from app.services.incidents import ALLOWED_INCIDENT_TRANSITIONS
from app.models.enums import IncidentStatus

def test_incident_status_transitions():
    assert IncidentStatus.REMEDIATION_PENDING.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.OPEN.value]
    assert IncidentStatus.APPROVAL_REQUIRED.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.REMEDIATION_PENDING.value]
    assert IncidentStatus.REMEDIATION_RUNNING.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.APPROVAL_REQUIRED.value]
    assert IncidentStatus.VERIFYING.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.REMEDIATION_RUNNING.value]
    assert IncidentStatus.RECOVERED.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.VERIFYING.value]
    assert IncidentStatus.RESOLVED.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.RECOVERED.value]

def test_incident_failure_transitions():
    assert IncidentStatus.FAILED.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.REMEDIATION_RUNNING.value]
    assert IncidentStatus.ESCALATED.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.FAILED.value]
    assert IncidentStatus.REMEDIATION_PENDING.value in ALLOWED_INCIDENT_TRANSITIONS[IncidentStatus.FAILED.value]
