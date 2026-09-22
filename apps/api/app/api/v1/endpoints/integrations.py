import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_permission
from app.models.user import User
from app.services.integrations import IntegrationService
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationUpdate,
    IntegrationResponse,
    IntegrationValidationResponse,
    IntegrationCapabilitiesResponse
)
from app.models.enums import IntegrationStatus
from app.workers.integration_tasks import validate_integration_task, discover_resources_task
from app.integrations.exceptions import ProviderError, ProviderNotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("integrations:create"))])
def create_integration(
    *,
    db: Session = Depends(get_db),
    integration_in: IntegrationCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    try:
        integration = service.create(integration_in=integration_in, current_user=current_user)
        return integration
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[IntegrationResponse], dependencies=[Depends(require_permission("integrations:read"))])
def list_integrations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    service = IntegrationService(db)
    return service.get_all(skip=skip, limit=limit)

@router.get("/{integration_id}", response_model=IntegrationResponse, dependencies=[Depends(require_permission("integrations:read"))])
def get_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration

@router.patch("/{integration_id}", response_model=IntegrationResponse, dependencies=[Depends(require_permission("integrations:update"))])
def update_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    integration_in: IntegrationUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return service.update(integration, integration_in, current_user=current_user)

@router.post("/{integration_id}/enable", response_model=IntegrationResponse, dependencies=[Depends(require_permission("integrations:enable"))])
def enable_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return service.enable(integration, current_user=current_user)

@router.post("/{integration_id}/disable", response_model=IntegrationResponse, dependencies=[Depends(require_permission("integrations:disable"))])
def disable_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return service.disable(integration, current_user=current_user)

@router.post("/{integration_id}/validate", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_permission("integrations:validate"))])
def validate_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    # Trigger Celery Task
    validate_integration_task.delay(str(integration_id))
    return {"message": "Validation task triggered"}

@router.get("/{integration_id}/capabilities", response_model=IntegrationCapabilitiesResponse, dependencies=[Depends(require_permission("integrations:read"))])
def get_capabilities(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    try:
        capabilities = service.get_capabilities(integration)
        return {"capabilities": capabilities}
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{integration_id}/discover", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_permission("integrations:discover"))])
def discover_resources(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    # Trigger Celery Task
    discover_resources_task.delay(str(integration_id))
    return {"message": "Discovery task triggered"}
