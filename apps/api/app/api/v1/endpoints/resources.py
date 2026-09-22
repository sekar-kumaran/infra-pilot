from typing import Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db, require_permission, get_current_user
from app.models.user import User
from app.schemas.inventory import (
    InfrastructureResourceCreate,
    InfrastructureResourceUpdate,
    InfrastructureResourceResponse,
    ResourceListResponse,
    ResourceRelationshipCreate,
    ResourceRelationshipResponse,
    RelationshipListResponse
)
from app.services.resources import ResourceService
from app.models.enums import ResourceType, ProviderType, ResourceStatus

router = APIRouter()

# --- Resource Endpoints ---

@router.post(
    "/",
    response_model=InfrastructureResourceResponse,
    status_code=201,
    dependencies=[Depends(require_permission("resources:create"))]
)
def create_resource(
    *,
    db = Depends(get_db),
    resource_in: InfrastructureResourceCreate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    resource = service.create_resource(resource_in, current_user=current_user, request_id=request_id)
    db.commit()
    return resource

@router.get(
    "/",
    response_model=ResourceListResponse,
    dependencies=[Depends(require_permission("resources:read"))]
)
def list_resources(
    *,
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    resource_type: Optional[ResourceType] = None,
    provider: Optional[ProviderType] = None,
    environment_id: Optional[UUID] = None,
    status: Optional[ResourceStatus] = None,
    name: Optional[str] = None,
    external_id: Optional[str] = None
) -> Any:
    service = ResourceService(db)
    items, total = service.list_resources(
        page=page, page_size=page_size,
        resource_type=resource_type, provider=provider,
        environment_id=environment_id, status=status,
        name=name, external_id=external_id
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get(
    "/{resource_id}",
    response_model=InfrastructureResourceResponse,
    dependencies=[Depends(require_permission("resources:read"))]
)
def get_resource(
    *,
    db = Depends(get_db),
    resource_id: UUID
) -> Any:
    service = ResourceService(db)
    return service.get_resource(resource_id)

@router.patch(
    "/{resource_id}",
    response_model=InfrastructureResourceResponse,
    dependencies=[Depends(require_permission("resources:update"))]
)
def update_resource(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    resource_in: InfrastructureResourceUpdate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    resource = service.update_resource(resource_id, resource_in, current_user=current_user, request_id=request_id)
    db.commit()
    return resource

# --- Relationship Endpoints ---

@router.post(
    "/{resource_id}/relationships",
    response_model=ResourceRelationshipResponse,
    status_code=201,
    dependencies=[Depends(require_permission("relationships:create"))]
)
def create_relationship(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    relationship_in: ResourceRelationshipCreate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    rel = service.create_relationship(resource_id, relationship_in, current_user=current_user, request_id=request_id)
    db.commit()
    return rel

@router.get(
    "/{resource_id}/relationships",
    response_model=RelationshipListResponse,
    dependencies=[Depends(require_permission("relationships:read"))]
)
def list_relationships(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
) -> Any:
    service = ResourceService(db)
    items, total = service.list_relationships(resource_id, page=page, page_size=page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
