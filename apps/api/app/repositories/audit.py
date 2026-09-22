from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

def create_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    result: str,
    actor_user_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        request_id=request_id,
        metadata_=metadata
    )
    db.add(event)
    db.flush()
    return event

def get_audit_events(
    db: Session,
    actor_user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    result: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50
):
    query = db.query(AuditEvent)
    
    if actor_user_id is not None:
        query = query.filter(AuditEvent.actor_user_id == actor_user_id)
    if action is not None:
        query = query.filter(AuditEvent.action == action)
    if resource_type is not None:
        query = query.filter(AuditEvent.resource_type == resource_type)
    if resource_id is not None:
        query = query.filter(AuditEvent.resource_id == resource_id)
    if result is not None:
        query = query.filter(AuditEvent.result == result)
    if request_id is not None:
        query = query.filter(AuditEvent.request_id == request_id)
    if start_time is not None:
        query = query.filter(AuditEvent.timestamp >= start_time)
    if end_time is not None:
        query = query.filter(AuditEvent.timestamp <= end_time)
        
    query = query.order_by(AuditEvent.timestamp.desc())
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return items, total
