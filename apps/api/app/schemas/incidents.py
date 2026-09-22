from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.enums import IncidentStatus, IncidentPriority, Severity

class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = Severity.UNKNOWN.value
    priority: Optional[str] = None

class IncidentResponse(IncidentBase):
    id: UUID
    status: str
    primary_resource_id: Optional[UUID] = None
    source: Optional[str] = None
    correlation_key: Optional[str] = None
    opened_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IncidentEventResponse(BaseModel):
    id: UUID
    incident_id: UUID
    event_type: str
    actor_user_id: Optional[UUID] = None
    source: Optional[str] = None
    message: Optional[str] = None
    event_metadata: Dict[str, Any] = {}
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IncidentStatusUpdate(BaseModel):
    status: str
    message: Optional[str] = None
