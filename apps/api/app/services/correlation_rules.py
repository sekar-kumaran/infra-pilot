from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.events import Alert
from app.models.incidents import Incident
from app.repositories.incidents import IncidentRepository
from app.core.config import settings

CORRELATION_WINDOW_MINUTES = 15

class CorrelationResult:
    def __init__(self, incident: Optional[Incident], reason: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.incident = incident
        self.reason = reason
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_reason": self.reason,
            "matched_incident_id": str(self.incident.id) if self.incident else None,
            "time_window_seconds": CORRELATION_WINDOW_MINUTES * 60,
            **self.metadata
        }

class CorrelationRule(ABC):
    @abstractmethod
    def evaluate(self, alert: Alert, incident_repo: IncidentRepository, db: Session) -> CorrelationResult:
        """
        Evaluate if the alert should be correlated with an existing incident.
        Returns a CorrelationResult. If incident is None, no correlation was found.
        """
        pass

class SameResourceRule(CorrelationRule):
    def evaluate(self, alert: Alert, incident_repo: IncidentRepository, db: Session) -> CorrelationResult:
        if not alert.resource_id:
            return CorrelationResult(None)
            
        correlation_key = f"resource_{alert.resource_id}"
        incident = incident_repo.get_open_incident_by_correlation_key(correlation_key)
        
        if incident:
            time_diff = datetime.now(timezone.utc) - incident.updated_at
            if time_diff <= timedelta(minutes=CORRELATION_WINDOW_MINUTES):
                return CorrelationResult(
                    incident=incident,
                    reason="SAME_RESOURCE",
                    metadata={"matched_resource_id": str(alert.resource_id), "correlation_key": correlation_key}
                )
                
        return CorrelationResult(None)

class GlobalAlertRule(CorrelationRule):
    def evaluate(self, alert: Alert, incident_repo: IncidentRepository, db: Session) -> CorrelationResult:
        if alert.resource_id:
            return CorrelationResult(None)
            
        correlation_key = f"global_alert_{alert.integration_id}_{alert.alert_type}"
        incident = incident_repo.get_open_incident_by_correlation_key(correlation_key)
        
        if incident:
            time_diff = datetime.now(timezone.utc) - incident.updated_at
            if time_diff <= timedelta(minutes=CORRELATION_WINDOW_MINUTES):
                return CorrelationResult(
                    incident=incident,
                    reason="SAME_CORRELATION_KEY",
                    metadata={"correlation_key": correlation_key}
                )
                
        return CorrelationResult(None)

class FingerprintRule(CorrelationRule):
    def evaluate(self, alert: Alert, incident_repo: IncidentRepository, db: Session) -> CorrelationResult:
        # If an incident exists with the same fingerprint in the time window
        # (This is more advanced, currently we don't store fingerprint on incident unless we add it)
        return CorrelationResult(None)

from app.models.resource import InfrastructureResource

class ApplicationRule(CorrelationRule):
    def evaluate(self, alert: Alert, incident_repo: IncidentRepository, db: Session) -> CorrelationResult:
        if not alert.resource_id:
            return CorrelationResult(None)
            
        # 1. Find if this resource belongs to an application
        resource = db.query(InfrastructureResource).filter(InfrastructureResource.id == alert.resource_id).first()
        if not resource or not resource.application_id:
            return CorrelationResult(None)
            
        application_id = resource.application_id
        
        # 2. See if there is an OPEN incident whose primary resource belongs to this application
        # To do this efficiently, we find open incidents created in the time window
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=CORRELATION_WINDOW_MINUTES)
        
        # Get open incidents within time window
        open_incidents = db.query(Incident).filter(
            Incident.status == "OPEN",
            Incident.updated_at >= recent_cutoff
        ).all()
        
        for inc in open_incidents:
            if not inc.primary_resource_id:
                continue
            # Check if the primary resource of the incident belongs to the SAME application
            inc_resource = db.query(InfrastructureResource).filter(InfrastructureResource.id == inc.primary_resource_id).first()
            if inc_resource and inc_resource.application_id == application_id:
                return CorrelationResult(
                    incident=inc,
                    reason="SAME_APPLICATION",
                    metadata={
                        "matched_application_id": str(application_id),
                        "triggering_resource_id": str(alert.resource_id),
                        "incident_primary_resource_id": str(inc.primary_resource_id)
                    }
                )
                
        return CorrelationResult(None)


class CorrelationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        # Sequence matters! Try Application first to group macro-level, then Resource, then Global.
        self.rules = [
            ApplicationRule(),
            SameResourceRule(),
            GlobalAlertRule()
        ]
        
    def find_correlation(self, alert: Alert) -> CorrelationResult:
        for rule in self.rules:
            result = rule.evaluate(alert, self.incident_repo, self.db)
            if result.incident:
                return result
        
        # If no rule matched, determine default correlation key for new incident creation
        correlation_key = f"resource_{alert.resource_id}" if alert.resource_id else f"global_alert_{alert.integration_id}_{alert.alert_type}"
        return CorrelationResult(None, reason="NO_MATCH", metadata={"correlation_key": correlation_key})
