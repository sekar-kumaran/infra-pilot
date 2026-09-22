from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.enums import ProviderType, Severity, AlertStatus, RawEventProcessingStatus

class RawEventBase(BaseModel):
    integration_id: UUID
    provider: str
    event_type: str
    external_event_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    payload: Dict[str, Any]
    source: Optional[str] = None
    resource_external_id: Optional[str] = None
    resource_id: Optional[UUID] = None

class RawEventCreate(RawEventBase):
    pass

class RawEventResponse(RawEventBase):
    id: UUID
    received_at: datetime
    payload_hash: str
    processing_status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    labels: Dict[str, Any] = {}
    severity: str = Severity.UNKNOWN.value

class AlertResponse(AlertBase):
    id: UUID
    raw_event_id: UUID
    integration_id: UUID
    resource_id: Optional[UUID] = None
    provider: str
    alert_type: str
    status: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    fingerprint: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
