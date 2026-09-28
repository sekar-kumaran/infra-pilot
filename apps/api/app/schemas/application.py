from typing import Optional, Dict, Any, List
from pydantic import BaseModel, UUID4, Field
from datetime import datetime

class ApplicationBase(BaseModel):
    name: str = Field(..., example="Weather App")
    description: Optional[str] = Field(None, example="Frontend, backend, and cache for the weather dashboard.")
    status: Optional[str] = Field("HEALTHY", example="HEALTHY")

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ApplicationResponse(ApplicationBase):
    id: UUID4
    tenant_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    # These will be populated in the endpoint by querying related resources
    resource_count: Optional[int] = 0
    incidents_count: Optional[int] = 0

    class Config:
        from_attributes = True
