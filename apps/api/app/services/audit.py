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
    import copy
    
    def redact_dict(d: dict) -> dict:
        redacted = copy.deepcopy(d)
        sensitive_substrings = ["password", "secret", "token", "key", "authorization", "kubeconfig"]
        for k, v in redacted.items():
            if any(sub in str(k).lower() for sub in sensitive_substrings):
                redacted[k] = "***REDACTED***"
            elif isinstance(v, dict):
                redacted[k] = redact_dict(v)
            elif isinstance(v, list):
                redacted[k] = [redact_dict(i) if isinstance(i, dict) else i for i in v]
        return redacted

    safe_metadata = {}
    if metadata:
        safe_metadata = redact_dict(metadata)
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
