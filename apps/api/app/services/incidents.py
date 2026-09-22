from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.incidents import Incident, IncidentEvent
from app.models.events import Alert
from app.models.enums import IncidentStatus, AlertStatus, IncidentEventType
from app.repositories.incidents import IncidentRepository
from app.repositories.events import EventRepository
from app.services.audit import log_event

# Allowed state transitions for incidents
ALLOWED_INCIDENT_TRANSITIONS = {
    IncidentStatus.OPEN.value: {IncidentStatus.INVESTIGATING.value, IncidentStatus.RESOLVED.value, IncidentStatus.SUPPRESSED.value},
    IncidentStatus.INVESTIGATING.value: {IncidentStatus.DIAGNOSED.value, IncidentStatus.REMEDIATING.value, IncidentStatus.RESOLVED.value},
    IncidentStatus.DIAGNOSED.value: {IncidentStatus.REMEDIATING.value, IncidentStatus.RESOLVED.value},
    IncidentStatus.REMEDIATING.value: {IncidentStatus.VERIFYING.value, IncidentStatus.RESOLVED.value},
    IncidentStatus.VERIFYING.value: {IncidentStatus.RESOLVED.value, IncidentStatus.INVESTIGATING.value},
    IncidentStatus.RESOLVED.value: {IncidentStatus.CLOSED.value, IncidentStatus.INVESTIGATING.value},
    IncidentStatus.CLOSED.value: set(), # Terminal state
    IncidentStatus.SUPPRESSED.value: {IncidentStatus.OPEN.value}
}

class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.event_repo = EventRepository(db)

    def _validate_transition(self, current_status: str, new_status: str):
        if new_status not in ALLOWED_INCIDENT_TRANSITIONS.get(current_status, set()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid incident state transition from {current_status} to {new_status}"
            )

    def update_incident_status(self, incident_id: UUID, new_status: str, actor_id: UUID, request_id: str, message: str = None) -> Incident:
        incident = self.incident_repo.get_incident_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        if incident.status == new_status:
            return incident

        self._validate_transition(incident.status, new_status)
        old_status = incident.status
        incident.status = new_status
        incident.updated_at = datetime.utcnow()
        
        if new_status == IncidentStatus.RESOLVED.value:
            incident.resolved_at = datetime.utcnow()
        elif new_status == IncidentStatus.CLOSED.value:
            incident.closed_at = datetime.utcnow()

        self.db.flush()

        # Add timeline event
        self.incident_repo.create_incident_event({
            "incident_id": incident.id,
            "event_type": IncidentEventType.STATUS_CHANGED.value,
            "actor_user_id": actor_id,
            "source": "api",
            "message": message or f"Incident status changed to {new_status}",
            "event_metadata": {"old_status": old_status, "new_status": new_status}
        })
        
        if new_status in [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value]:
            event_type = IncidentEventType.INCIDENT_RESOLVED.value if new_status == IncidentStatus.RESOLVED.value else IncidentEventType.INCIDENT_CLOSED.value
            self.incident_repo.create_incident_event({
                "incident_id": incident.id,
                "event_type": event_type,
                "actor_user_id": actor_id,
                "source": "api",
                "message": f"Incident {new_status.lower()}",
                "event_metadata": {}
            })
            # Also resolve all related alerts
            alerts = self.event_repo.get_alerts(resource_id=incident.primary_resource_id, status=AlertStatus.ACTIVE.value)
            for alert in alerts:
                alert.status = AlertStatus.RESOLVED.value
                alert.updated_at = datetime.utcnow()

        # Audit Log
        log_event(
            db=self.db,
            actor_user_id=actor_id,
            action=f"incident.status_changed",
            resource_type="incident",
            resource_id=str(incident.id),
            result="success",
            request_id=request_id,
            metadata={"old_status": old_status, "new_status": new_status}
        )

        self.db.commit()
        return incident

    def acknowledge_incident(self, incident_id: UUID, actor_id: UUID, request_id: str) -> Incident:
        incident = self.incident_repo.get_incident_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
            
        if incident.acknowledged_at:
            return incident # Already acknowledged
            
        incident.acknowledged_at = datetime.utcnow()
        if incident.status == IncidentStatus.OPEN.value:
            self.update_incident_status(incident_id, IncidentStatus.INVESTIGATING.value, actor_id, request_id)
            # update_incident_status will commit and refresh
            
        self.incident_repo.create_incident_event({
            "incident_id": incident.id,
            "event_type": IncidentEventType.ACKNOWLEDGED.value,
            "actor_user_id": actor_id,
            "source": "api",
            "message": "Incident acknowledged",
            "event_metadata": {}
        })

        log_event(
            db=self.db,
            actor_user_id=actor_id,
            action=f"incident.acknowledged",
            resource_type="incident",
            resource_id=str(incident.id),
            result="success",
            request_id=request_id,
            metadata={}
        )

        self.db.commit()
        return incident

    def acknowledge_alert(self, alert_id: UUID, actor_id: UUID, request_id: str) -> Alert:
        alert = self.event_repo.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.updated_at = datetime.utcnow()
        
        log_event(
            db=self.db,
            actor_user_id=actor_id,
            action=f"alert.acknowledged",
            resource_type="alert",
            resource_id=str(alert.id),
            result="success",
            request_id=request_id,
            metadata={}
        )
        self.db.commit()
        return alert
        
    def resolve_alert(self, alert_id: UUID, actor_id: UUID, request_id: str) -> Alert:
        alert = self.event_repo.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        alert.status = AlertStatus.RESOLVED.value
        alert.updated_at = datetime.utcnow()
        alert.ends_at = datetime.utcnow()
        
        log_event(
            db=self.db,
            actor_user_id=actor_id,
            action=f"alert.resolved",
            resource_type="alert",
            resource_id=str(alert.id),
            result="success",
            request_id=request_id,
            metadata={}
        )
        self.db.commit()
        return alert
