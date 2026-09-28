from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.events import RawEventCreate, RawEventResponse
from app.services.event_ingestion import EventIngestionService
from app.repositories.events import EventRepository
from app.models.user import User

router = APIRouter()

@router.post("", response_model=RawEventResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(
    *,
    db: Session = Depends(deps.get_db),
    event_in: RawEventCreate,
    current_user: User = Depends(deps.require_permission("events:ingest")),
) -> Any:
    """
    Ingest a raw event. Returns 202 Accepted.
    Idempotent: Duplicate payloads return the existing record.
    """
    event_service = EventIngestionService(db)
    event, is_new = event_service.ingest_event(
        event_in=event_in,
        current_user_id=current_user.id
    )
    return event

@router.get("", response_model=List[RawEventResponse])
def list_events(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.require_permission("events:read")),
) -> Any:
    """
    List raw events.
    """
    repo = EventRepository(db)
    return repo.get_raw_events(skip=skip, limit=limit)

@router.get("/jobs/{job_id}")
def get_job_status(
    *,
    job_id: str,
    current_user: User = Depends(deps.require_permission("events:read")),
) -> Any:
    """
    Get Celery job status safely.
    """
    from app.workers.celery_app import celery_app
    from celery.result import AsyncResult
    
    result = AsyncResult(job_id, app=celery_app)
    # Map celery states to simple statuses
    state_map = {
        "PENDING": "PENDING",
        "STARTED": "RUNNING",
        "SUCCESS": "SUCCESS",
        "FAILURE": "FAILED",
        "RETRY": "RETRYING",
        "REVOKED": "FAILED"
    }
    
    status = state_map.get(result.state, result.state)
    return {"job_id": job_id, "status": status}

@router.get("/{event_id}", response_model=RawEventResponse)
def get_event(
    *,
    db: Session = Depends(deps.get_db),
    event_id: UUID,
    current_user: User = Depends(deps.require_permission("events:read")),
) -> Any:
    """
    Get a specific raw event by ID.
    """
    repo = EventRepository(db)
    event = repo.get_raw_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/{event_id}/reprocess")
def reprocess_event(
    *,
    db: Session = Depends(deps.get_db),
    event_id: UUID,
    current_user: User = Depends(deps.require_permission("events:ingest")),
) -> Any:
    """
    Reprocess a failed event.
    """
    from app.models.enums import RawEventProcessingStatus
    from app.workers.tasks import process_raw_event_task
    from app.services.audit import log_event
    
    repo = EventRepository(db)
    event = repo.get_raw_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if event.processing_status not in [RawEventProcessingStatus.FAILED.value, RawEventProcessingStatus.RECEIVED.value]:
        raise HTTPException(status_code=400, detail="Event is not eligible for reprocessing")
        
    event.processing_status = RawEventProcessingStatus.RECEIVED.value
    db.commit()
    
    log_event(
        db=db,
        actor_user_id=current_user.id,
        action="event.reprocessed",
        resource_type="event",
        resource_id=str(event.id),
        result="success",
        metadata={"previous_status": RawEventProcessingStatus.FAILED.value}
    )
    
    task = process_raw_event_task.delay(str(event.id))
    
    return {"job_id": task.id, "status": "PENDING"}


