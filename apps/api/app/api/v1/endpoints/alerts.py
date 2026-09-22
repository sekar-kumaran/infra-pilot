from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.events import AlertResponse
from app.repositories.events import EventRepository
from app.services.incidents import IncidentService
from app.models.user import User

router = APIRouter()

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    current_user: User = Depends(deps.require_permission("alerts:read")),
) -> Any:
    """
    List alerts with filtering.
    """
    repo = EventRepository(db)
    return repo.get_alerts(
        skip=skip, 
        limit=limit, 
        status=status, 
        severity=severity, 
        resource_id=resource_id
    )

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: UUID,
    current_user: User = Depends(deps.require_permission("alerts:read")),
) -> Any:
    """
    Get a specific alert by ID.
    """
    repo = EventRepository(db)
    alert = repo.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: UUID,
    current_user: User = Depends(deps.require_permission("alerts:update")),
) -> Any:
    """
    Acknowledge an alert.
    """
    incident_service = IncidentService(db)
    return incident_service.acknowledge_alert(alert_id, current_user.id, request_id="api")

@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: UUID,
    current_user: User = Depends(deps.require_permission("alerts:update")),
) -> Any:
    """
    Resolve an alert manually.
    """
    incident_service = IncidentService(db)
    return incident_service.resolve_alert(alert_id, current_user.id, request_id="api")
