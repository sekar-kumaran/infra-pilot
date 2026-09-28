from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class RemediationOption(BaseModel):
    strategy: str
    provider: str
    action: str
    executor: str
    risk_level: str
    requires_approval: bool
    verification: str

class RemediationPlanCreate(BaseModel):
    strategy: str
    parameters: Optional[Dict[str, Any]] = None

class RemediationPlanResponse(BaseModel):
    id: UUID
    incident_id: UUID
    strategy: str
    target_resource_id: Optional[UUID]
    selected_action: str
    provider: str
    requires_approval: bool
    risk_level: str
    approval_status: str
    execution_status: str
    verification_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
