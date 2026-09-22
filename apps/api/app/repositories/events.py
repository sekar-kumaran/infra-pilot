from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc

from app.models.events import RawEvent, Alert
from app.schemas.events import RawEventCreate

class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_raw_event(self, raw_event_data: dict, payload_hash: str) -> RawEvent:
        event = RawEvent(
            **raw_event_data,
            payload_hash=payload_hash
        )
        self.session.add(event)
        self.session.flush()
        return event

    def get_raw_event_by_hash(self, payload_hash: str) -> Optional[RawEvent]:
        stmt = select(RawEvent).where(RawEvent.payload_hash == payload_hash)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result
    
    def get_raw_event_by_id(self, event_id: UUID) -> Optional[RawEvent]:
        stmt = select(RawEvent).where(RawEvent.id == event_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def get_raw_events(self, skip: int = 0, limit: int = 100) -> List[RawEvent]:
        stmt = select(RawEvent).order_by(desc(RawEvent.created_at)).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def update_raw_event_status(self, event_id: UUID, status: str) -> Optional[RawEvent]:
        event = self.get_raw_event_by_id(event_id)
        if event:
            event.processing_status = status
            self.session.flush()
        return event

    # Alert Methods
    def create_alert(self, alert_data: dict) -> Alert:
        alert = Alert(**alert_data)
        self.session.add(alert)
        self.session.flush()
        return alert

    def get_alert_by_fingerprint(self, fingerprint: str) -> Optional[Alert]:
        stmt = select(Alert).where(Alert.fingerprint == fingerprint)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_alert_by_id(self, alert_id: UUID) -> Optional[Alert]:
        stmt = select(Alert).where(Alert.id == alert_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def update_alert(self, alert: Alert, update_data: dict) -> Alert:
        for key, value in update_data.items():
            setattr(alert, key, value)
        self.session.flush()
        return alert

    def get_alerts(self, skip: int = 0, limit: int = 100, **filters) -> List[Alert]:
        stmt = select(Alert)
        
        conditions = []
        if 'status' in filters and filters['status']:
            conditions.append(Alert.status == filters['status'])
        if 'severity' in filters and filters['severity']:
            conditions.append(Alert.severity == filters['severity'])
        if 'resource_id' in filters and filters['resource_id']:
            conditions.append(Alert.resource_id == filters['resource_id'])
            
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(Alert.created_at)).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
