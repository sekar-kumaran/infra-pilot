from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.api.deps import get_db, require_permission

router = APIRouter()

class SystemInfo(BaseModel):
    application_name: str
    version: str
    environment: str

@router.get("/info", response_model=SystemInfo)
async def system_info():
    return {
        "application_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

@router.get("/metrics")
async def metrics():
    """
    Exposes application-level Prometheus metrics.
    """
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/metrics-summary")
async def metrics_summary(
    db = Depends(get_db),
    current_user = Depends(require_permission("monitoring:read"))
):
    """
    Safe aggregated operational information.
    """
    from app.models.events import RawEvent, Alert
    from app.models.incidents import Incident
    from app.models.enums import IncidentStatus, AlertStatus, RawEventProcessingStatus
    from sqlalchemy import func
    
    from app.models.integration import Integration
    from app.models.automation import AutomationExecution
    
    events_processed = db.query(func.count(RawEvent.id)).filter(RawEvent.processing_status == RawEventProcessingStatus.PROCESSED.value).scalar() or 0
    failed_events = db.query(func.count(RawEvent.id)).filter(RawEvent.processing_status == RawEventProcessingStatus.FAILED.value).scalar() or 0
    active_alerts = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.ACTIVE.value).scalar() or 0
    open_incidents = db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.OPEN.value).scalar() or 0
    critical_incidents = db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.OPEN.value, Incident.severity == "CRITICAL").scalar() or 0
    
    active_integrations = db.query(func.count(Integration.id)).filter(Integration.status == 'HEALTHY').scalar() or 0
    automation_executions = db.query(func.count(AutomationExecution.id)).scalar() or 0
    failed_executions = db.query(func.count(AutomationExecution.id)).filter(AutomationExecution.status == 'FAILED').scalar() or 0
    
    return {
        "events_processed": events_processed,
        "failed_events": failed_events,
        "active_alerts": active_alerts,
        "open_incidents": open_incidents,
        "critical_incidents": critical_incidents,
        "active_integrations": active_integrations,
        "automation_executions": automation_executions,
        "failed_executions": failed_executions
    }
