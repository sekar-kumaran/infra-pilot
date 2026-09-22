from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import ProviderType, IntegrationStatus
from app.integrations.models import IntegrationCapability

class IntegrationBase(BaseModel):
    name: str
    provider: ProviderType
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

class IntegrationResponse(IntegrationBase):
    id: UUID
    status: IntegrationStatus
    created_at: datetime
    updated_at: datetime
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IntegrationValidationResponse(BaseModel):
    status: IntegrationStatus
    message: str

class IntegrationCapabilitiesResponse(BaseModel):
    capabilities: IntegrationCapability
