from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories import audit as audit_repo

def log_event(
    db: Session,
    action: str,
    resource_type: str,
    result: str,
    actor_user_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event.
    """
    safe_metadata = {}
    if metadata:
        safe_metadata = {k: v for k, v in metadata.items()}
        # Strip out sensitive info from metadata just in case
        sensitive_keys = {"password", "password_hash", "jwt", "authorization", "database_url", "auth_secret_key"}
        for k in list(safe_metadata.keys()):
            if str(k).lower() in sensitive_keys:
                safe_metadata[k] = "[REDACTED]"
                
    return audit_repo.create_audit_event(
        db=db,
        action=action,
        resource_type=resource_type,
        result=result,
        actor_user_id=actor_user_id,
        resource_id=resource_id,
        request_id=request_id,
        metadata=safe_metadata if safe_metadata else None
    )

def get_audit_events(
    db: Session,
    actor_user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    result: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[Any] = None, # using Any or datetime from python datetime module
    end_time: Optional[Any] = None,
    skip: int = 0,
    limit: int = 50
):
    return audit_repo.get_audit_events(
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
        limit=limit
    )
