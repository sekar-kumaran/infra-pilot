from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.api.deps import get_current_user, get_db

router = APIRouter()


@router.get("/logs")
def get_logs(
    query: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Log querying endpoint. Reads from the RawEvent table as a best-effort log source.
    A real implementation would connect to Loki, Elasticsearch, or Datadog.
    """
    from app.models.events import RawEvent
    from sqlalchemy import desc

    q = db.query(RawEvent).order_by(desc(RawEvent.received_at))

    events = q.limit(limit).all()

    items = []
    for e in events:
        payload = e.payload or {}
        msg = payload.get("message") or payload.get("msg") or payload.get("description") or e.event_type
        lvl = payload.get("level") or payload.get("severity") or "INFO"
        if level and lvl.upper() != level.upper():
            continue
        # Trim query results if a text query is provided
        if query and query.lower() not in str(payload).lower() and query.lower() not in (msg or "").lower():
            continue
        items.append({
            "id": str(e.id),
            "timestamp": e.received_at.isoformat(),
            "level": lvl.upper(),
            "service": e.provider or e.source or "unknown",
            "message": str(msg)[:500] if msg else e.event_type,
            "metadata": {
                "trace_id": payload.get("trace_id"),
                "event_type": e.event_type,
                "processing_status": e.processing_status,
                "external_id": e.external_event_id,
            }
        })

    return {"items": items, "total": len(items)}


@router.get("/live-events")
def get_live_events(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Live event feed — returns the most recent raw events as a live activity stream.
    """
    from app.models.events import RawEvent
    from sqlalchemy import desc

    events = db.query(RawEvent).order_by(desc(RawEvent.received_at)).limit(limit).all()

    items = []
    for e in events:
        payload = e.payload or {}
        description = (
            payload.get("message") or payload.get("description") or
            f"{e.event_type} from {e.provider}"
        )
        items.append({
            "id": str(e.id),
            "timestamp": e.received_at.isoformat(),
            "type": _map_event_type(e.event_type),
            "description": str(description)[:200],
            "source": e.provider or "system",
        })

    return {"items": items, "total": len(items)}



def _map_event_type(event_type: Optional[str]) -> str:
    if not event_type:
        return "system"
    et = event_type.lower()
    if "deploy" in et:
        return "deployment"
    if "alert" in et:
        return "alert"
    if "health" in et or "ping" in et:
        return "healthcheck"
    if "scale" in et:
        return "scaling"
    return "system"
