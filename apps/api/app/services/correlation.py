import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from app.models.events import RawEvent, Alert
from app.models.incidents import Incident, IncidentEvent
from app.models.enums import Severity, IncidentStatus, AlertStatus, IncidentEventType
from app.repositories.events import EventRepository
from app.repositories.incidents import IncidentRepository
from app.core.config import settings
from app.services.audit import log_event

logger = logging.getLogger(__name__)

# Configurable 15 minute window default
CORRELATION_WINDOW_MINUTES = getattr(settings, "INCIDENT_CORRELATION_WINDOW_MINUTES", 15)

SEVERITY_WEIGHT = {
    Severity.INFO.value: 1,
    Severity.UNKNOWN.value: 2,
    Severity.WARNING.value: 3,
    Severity.CRITICAL.value: 4
}

class CorrelationService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.incident_repo = IncidentRepository(db)

    def _canonicalize_labels(self, labels: Dict[str, Any]) -> str:
        return json.dumps(labels, sort_keys=True, separators=(',', ':'))

    def _generate_fingerprint(self, provider: str, integration_id: str, resource_id: str, alert_type: str, labels: Dict[str, Any]) -> str:
        """
        Alert fingerprinting MUST be deterministic.
        Hash inputs: provider + integration_id + resource_id + alert_type + normalized labels
        """
        canonical_labels = self._canonicalize_labels(labels)
        r_id = resource_id or ""
        raw_string = f"{provider}|{integration_id}|{r_id}|{alert_type}|{canonical_labels}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def _calculate_severity(self, current_sev: str, new_sev: str) -> str:
        """ Returns the highest severity between the two """
        w_current = SEVERITY_WEIGHT.get(current_sev, 2)
        w_new = SEVERITY_WEIGHT.get(new_sev, 2)
        return new_sev if w_new > w_current else current_sev

    def normalize_event(self, raw_event: RawEvent) -> Alert:
        """
        Phase 1.7 / 1.8: Normalization.
        Normally this uses the AdapterRegistry. For Phase 1.8, we emulate the test provider normalization.
        """
        # In a real setup, we would do:
        # adapter = AdapterRegistry.get_adapter(raw_event.provider)
        # return adapter.normalize(raw_event)
        
        # Simple test provider normalization
        payload = raw_event.payload
        alert_type = payload.get("alert_type", "GENERIC_ALERT")
        severity = payload.get("severity", Severity.WARNING.value)
        title = payload.get("title", f"Alert from {raw_event.provider}")
        description = payload.get("description", "")
        labels = payload.get("labels", {})
        
        fingerprint = self._generate_fingerprint(
            provider=raw_event.provider,
            integration_id=str(raw_event.integration_id),
            resource_id=str(raw_event.resource_id) if raw_event.resource_id else "",
            alert_type=alert_type,
            labels=labels
        )
        
        # Deduplicate alert
        existing_alert = self.event_repo.get_alert_by_fingerprint(fingerprint)
        if existing_alert:
            # Update existing active alert
            existing_alert.ends_at = datetime.now(timezone.utc)
            existing_alert.updated_at = datetime.now(timezone.utc)
            # Escalate severity if needed
            if SEVERITY_WEIGHT.get(severity, 2) > SEVERITY_WEIGHT.get(existing_alert.severity, 2):
                existing_alert.severity = severity
            self.db.flush()
            return existing_alert
            
        alert_data = {
            "raw_event_id": raw_event.id,
            "integration_id": raw_event.integration_id,
            "resource_id": raw_event.resource_id,
            "provider": raw_event.provider,
            "alert_type": alert_type,
            "severity": severity,
            "status": AlertStatus.ACTIVE.value,
            "title": title,
            "description": description,
            "labels": labels,
            "starts_at": datetime.now(timezone.utc),
            "fingerprint": fingerprint
        }
        
        return self.event_repo.create_alert(alert_data)

    def correlate_alert(self, alert: Alert) -> Incident:
        """
        Deterministic Rule-based Correlation
        Strategy: Same resource + Open Incident + 15m Window
        """
        if not alert.resource_id:
            # Global incident if no resource_id
            correlation_key = f"global_alert_{alert.integration_id}_{alert.alert_type}"
        else:
            correlation_key = f"resource_{alert.resource_id}"
            
        incident = self.incident_repo.get_open_incident_by_correlation_key(correlation_key)
        
        is_new_incident = False
        
        if incident:
            # Check window
            time_diff = datetime.now(timezone.utc) - incident.updated_at
            if time_diff > timedelta(minutes=CORRELATION_WINDOW_MINUTES):
                # Outside window, create new incident
                incident = None
        
        if not incident:
            # Create Incident
            incident_data = {
                "title": f"Incident: {alert.title}",
                "description": f"Automatically generated incident for alert: {alert.title}",
                "severity": alert.severity,
                "status": IncidentStatus.OPEN.value,
                "primary_resource_id": alert.resource_id,
                "source": alert.provider,
                "correlation_key": correlation_key,
                "opened_at": datetime.now(timezone.utc)
            }
            incident = self.incident_repo.create_incident(incident_data)
            is_new_incident = True
            
            # Add timeline event
            self.incident_repo.create_incident_event({
                "incident_id": incident.id,
                "event_type": IncidentEventType.INCIDENT_CREATED.value,
                "source": "system",
                "message": f"Incident created from alert {alert.id}",
                "event_metadata": {"alert_id": str(alert.id)}
            })
            
            log_event(
                db=self.db,
                actor_user_id=None,
                action="incident.created",
                resource_type="incident",
                resource_id=str(incident.id),
                result="success",
                metadata={"alert_id": str(alert.id), "correlation_key": correlation_key}
            )

        else:
            # Update Existing Incident
            old_severity = incident.severity
            new_severity = self._calculate_severity(old_severity, alert.severity)
            
            incident.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            
            # Attach timeline event
            self.incident_repo.create_incident_event({
                "incident_id": incident.id,
                "event_type": IncidentEventType.ALERT_ATTACHED.value,
                "source": "system",
                "message": f"Alert {alert.id} attached to incident",
                "event_metadata": {"alert_id": str(alert.id)}
            })
            
            if new_severity != old_severity:
                incident.severity = new_severity
                self.incident_repo.create_incident_event({
                    "incident_id": incident.id,
                    "event_type": IncidentEventType.SEVERITY_CHANGED.value,
                    "source": "system",
                    "message": f"Incident severity escalated from {old_severity} to {new_severity}",
                    "event_metadata": {"old_severity": old_severity, "new_severity": new_severity}
                })
                
                log_event(
                    db=self.db,
                    actor_user_id=None,
                    action="incident.severity_escalated",
                    resource_type="incident",
                    resource_id=str(incident.id),
                    result="success",
                    metadata={"old_severity": old_severity, "new_severity": new_severity}
                )
                
        return incident
