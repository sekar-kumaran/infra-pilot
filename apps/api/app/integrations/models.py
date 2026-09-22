from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.enums import ProviderType, ResourceType, ResourceStatus

class IntegrationCapability(BaseModel):
    resource_discovery: bool = False
    resource_read: bool = False
    metrics_read: bool = False
    logs_read: bool = False
    alerts_read: bool = False
    health_check: bool = False

class DiscoveredResource(BaseModel):
    provider: ProviderType
    external_id: str
    name: str
    display_name: Optional[str] = None
    resource_type: ResourceType
    status: ResourceStatus
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
