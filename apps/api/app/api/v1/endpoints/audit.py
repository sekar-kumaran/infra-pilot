from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import require_permission, get_current_user
from app.models.user import User
from app.schemas.audit import AuditEventResponse
from app.services import audit as audit_service

router = APIRouter()

@router.get("/", response_model=List[AuditEventResponse])
def get_audit_events(
    actor_user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    result: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("security:read"))
):
    skip = (page - 1) * page_size
    items, total = audit_service.get_audit_events(
        db=db,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        request_id=request_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=page_size
    )
    
    return items
