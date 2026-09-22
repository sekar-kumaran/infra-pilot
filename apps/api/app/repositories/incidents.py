from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from app.models.incidents import Incident, IncidentEvent

class IncidentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_incident(self, incident_data: dict) -> Incident:
        incident = Incident(**incident_data)
        self.session.add(incident)
        self.session.flush()
        return incident

    def get_incident_by_id(self, incident_id: UUID) -> Optional[Incident]:
        stmt = select(Incident).where(Incident.id == incident_id)
        return self.session.execute(stmt).scalar_one_or_none()
        
    def get_open_incident_by_correlation_key(self, correlation_key: str) -> Optional[Incident]:
        stmt = select(Incident).where(
            and_(
                Incident.correlation_key == correlation_key,
                Incident.status.notin_(["RESOLVED", "CLOSED", "SUPPRESSED"])
            )
        ).order_by(desc(Incident.created_at)).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def update_incident(self, incident: Incident, update_data: dict) -> Incident:
        for key, value in update_data.items():
            setattr(incident, key, value)
        self.session.flush()
        return incident

    def get_incidents(self, skip: int = 0, limit: int = 100, **filters) -> List[Incident]:
        stmt = select(Incident)
        
        conditions = []
        if 'status' in filters and filters['status']:
            conditions.append(Incident.status == filters['status'])
        if 'severity' in filters and filters['severity']:
            conditions.append(Incident.severity == filters['severity'])
        if 'primary_resource_id' in filters and filters['primary_resource_id']:
            conditions.append(Incident.primary_resource_id == filters['primary_resource_id'])
            
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(Incident.opened_at)).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    # IncidentEvent Methods
    def create_incident_event(self, event_data: dict) -> IncidentEvent:
        event = IncidentEvent(**event_data)
        self.session.add(event)
        self.session.flush()
        return event

    def get_incident_events(self, incident_id: UUID, skip: int = 0, limit: int = 100) -> List[IncidentEvent]:
        stmt = select(IncidentEvent).where(
            IncidentEvent.incident_id == incident_id
        ).order_by(desc(IncidentEvent.created_at)).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
