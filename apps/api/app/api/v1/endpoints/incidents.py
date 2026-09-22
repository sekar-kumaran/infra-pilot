from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.incidents import IncidentResponse, IncidentEventResponse, IncidentStatusUpdate
from app.schemas.events import AlertResponse
from app.repositories.incidents import IncidentRepository
from app.repositories.events import EventRepository
from app.services.incidents import IncidentService
from app.models.user import User
from app.models.enums import IncidentStatus

router = APIRouter()

@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    primary_resource_id: Optional[UUID] = Query(None),
    current_user: User = Depends(deps.require_permission("incidents:read")),
) -> Any:
    """
    List incidents with filtering.
    """
    repo = IncidentRepository(db)
    return repo.get_incidents(
        skip=skip, 
        limit=limit, 
        status=status, 
        severity=severity, 
        primary_resource_id=primary_resource_id
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    current_user: User = Depends(deps.require_permission("incidents:read")),
) -> Any:
    """
    Get a specific incident by ID.
    """
    repo = IncidentRepository(db)
    incident = repo.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    current_user: User = Depends(deps.require_permission("incidents:update")),
) -> Any:
    """
    Acknowledge an incident.
    """
    incident_service = IncidentService(db)
    return incident_service.acknowledge_incident(incident_id, current_user.id, request_id="api")

@router.post("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    status_update: IncidentStatusUpdate,
    current_user: User = Depends(deps.require_permission("incidents:update")),
) -> Any:
    """
    Update incident status.
    """
    incident_service = IncidentService(db)
    return incident_service.update_incident_status(
        incident_id, 
        status_update.status, 
        current_user.id, 
        "api", 
        status_update.message
    )

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    current_user: User = Depends(deps.require_permission("incidents:update")),
) -> Any:
    """
    Shortcut to resolve an incident.
    """
    incident_service = IncidentService(db)
    return incident_service.update_incident_status(
        incident_id, 
        IncidentStatus.RESOLVED.value, 
        current_user.id, 
        "api"
    )
    
@router.post("/{incident_id}/close", response_model=IncidentResponse)
def close_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    current_user: User = Depends(deps.require_permission("incidents:manage")),
) -> Any:
    """
    Shortcut to close an incident. Requires manage permission.
    """
    incident_service = IncidentService(db)
    return incident_service.update_incident_status(
        incident_id, 
        IncidentStatus.CLOSED.value, 
        current_user.id, 
        "api"
    )

@router.get("/{incident_id}/timeline", response_model=List[IncidentEventResponse])
def get_incident_timeline(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.require_permission("incidents:read")),
) -> Any:
    """
    Get the timeline of events for an incident.
    """
    repo = IncidentRepository(db)
    return repo.get_incident_events(incident_id, skip=skip, limit=limit)

@router.get("/{incident_id}/alerts", response_model=List[AlertResponse])
def get_incident_alerts(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.require_permission("incidents:read")),
) -> Any:
    """
    Get alerts correlated to an incident.
    For V1 correlation, this gets alerts associated with the incident's primary resource
    within the incident time window. We will query Alerts by resource_id and time bounds.
    """
    incident_repo = IncidentRepository(db)
    incident = incident_repo.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    event_repo = EventRepository(db)
    # Simple strategy: grab alerts matching the resource_id if it exists.
    # In a more advanced implementation, the correlation_key would be used, 
    # or an IncidentAlert bridging table would exist.
    
    if not incident.primary_resource_id:
        return []
        
    return event_repo.get_alerts(
        skip=skip,
        limit=limit,
        resource_id=incident.primary_resource_id
    )
