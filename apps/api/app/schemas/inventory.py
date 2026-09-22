from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.models.enums import EnvironmentType, ResourceType, ResourceStatus, ProviderType, RelationshipType

# --- Environment Schemas ---
class EnvironmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    environment_type: EnvironmentType

class EnvironmentCreate(EnvironmentBase):
    pass

class EnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    environment_type: Optional[EnvironmentType] = None

class EnvironmentResponse(EnvironmentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Resource Schemas ---
class InfrastructureResourceBase(BaseModel):
    name: str = Field(..., max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    resource_type: ResourceType
    provider: ProviderType
    environment_id: Optional[UUID] = None
    external_id: Optional[str] = Field(None, max_length=255)
    status: ResourceStatus = ResourceStatus.UNKNOWN
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class InfrastructureResourceCreate(InfrastructureResourceBase):
    pass

class InfrastructureResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    environment_id: Optional[UUID] = None
    status: Optional[ResourceStatus] = None
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class InfrastructureResourceResponse(InfrastructureResourceBase):
    id: UUID
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- Resource Relationship Schemas ---
class ResourceRelationshipBase(BaseModel):
    target_resource_id: UUID
    relationship_type: RelationshipType
    metadata: Optional[Dict[str, Any]] = None

class ResourceRelationshipCreate(ResourceRelationshipBase):
    pass

class ResourceRelationshipResponse(ResourceRelationshipBase):
    id: UUID
    source_resource_id: UUID
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata_")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- Common Pagination Responses ---
class EnvironmentListResponse(BaseModel):
    items: List[EnvironmentResponse]
    total: int
    page: int
    page_size: int

class ResourceListResponse(BaseModel):
    items: List[InfrastructureResourceResponse]
    total: int
    page: int
    page_size: int

class RelationshipListResponse(BaseModel):
    items: List[ResourceRelationshipResponse]
    total: int
    page: int
    page_size: int
