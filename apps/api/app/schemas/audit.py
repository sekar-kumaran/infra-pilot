from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AuditEventResponse(BaseModel):
    id: UUID
    actor_user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    result: str
    timestamp: datetime
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata_")

    model_config = ConfigDict(from_attributes=True)
