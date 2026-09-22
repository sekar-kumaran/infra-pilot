from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db, require_permission, get_current_user
from app.models.user import User
from app.schemas.inventory import (
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
    EnvironmentListResponse
)
from app.services.environments import EnvironmentService

router = APIRouter()

@router.post(
    "/",
    response_model=EnvironmentResponse,
    status_code=201,
    dependencies=[Depends(require_permission("environments:create"))]
)
def create_environment(
    *,
    db = Depends(get_db),
    env_in: EnvironmentCreate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123" # Optional request context for audit
) -> Any:
    service = EnvironmentService(db)
    env = service.create(env_in, current_user=current_user, request_id=request_id)
    db.commit()
    return env

@router.get(
    "/",
    response_model=EnvironmentListResponse,
    dependencies=[Depends(require_permission("environments:read"))]
)
def list_environments(
    *,
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
) -> Any:
    service = EnvironmentService(db)
    items, total = service.list(page=page, page_size=page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get(
    "/{environment_id}",
    response_model=EnvironmentResponse,
    dependencies=[Depends(require_permission("environments:read"))]
)
def get_environment(
    *,
    db = Depends(get_db),
    environment_id: UUID
) -> Any:
    service = EnvironmentService(db)
    return service.get_by_id(environment_id)

@router.patch(
    "/{environment_id}",
    response_model=EnvironmentResponse,
    dependencies=[Depends(require_permission("environments:update"))]
)
def update_environment(
    *,
    db = Depends(get_db),
    environment_id: UUID,
    env_in: EnvironmentUpdate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123" # Optional request context for audit
) -> Any:
    service = EnvironmentService(db)
    env = service.update(environment_id, env_in, current_user=current_user, request_id=request_id)
    db.commit()
    return env
