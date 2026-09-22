from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoleWithPermissionsResponse(RoleResponse):
    permissions: List[PermissionResponse]

class UserRoleResponse(BaseModel):
    user_id: UUID
    role_id: UUID
    role_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
