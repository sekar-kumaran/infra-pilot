"""
Settings endpoints — notification channels, tenant configuration, etc.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/notifications")
def list_notification_channels(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns the configured notification channels (Slack, PagerDuty, Email, etc.)
    Phase 2+ will persist these to the database and support CRUD.
    Currently returns an empty structured response until channels are configured.
    """
    # Future: read from a NotificationChannel model in the DB
    return {
        "items": [],
        "total": 0
    }


@router.post("/notifications")
def create_notification_channel(
    channel: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new notification channel. Stub for Phase 2+.
    """
    return {
        "status": "accepted",
        "message": "Notification channel creation is scheduled for Phase 2 integration."
    }
