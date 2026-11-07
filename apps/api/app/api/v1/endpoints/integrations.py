import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Any, Optional, Dict
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
from app.integrations.registry import AdapterRegistry
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

@router.get("/{integration_id}/metrics", dependencies=[Depends(require_permission("metrics:read"))])
def get_integration_metrics(
    *,
    db: Session = Depends(get_db),
    integration_id: uuid.UUID,
    metric_type: Optional[str] = None,
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Read named metrics from the integration provider.
    """
    service = IntegrationService(db)
    integration = service.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    if integration.status != IntegrationStatus.HEALTHY:
        raise HTTPException(status_code=400, detail="Integration must be HEALTHY to read metrics")

    effective_metric = metric_type or query
    if not effective_metric:
        raise HTTPException(status_code=400, detail="metric_type or query is required")

    import re
    if query:
        if not re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*(\{[^}]*\})?$', query.strip()):
            raise HTTPException(status_code=400, detail="Query contains unsafe or unsupported PromQL operations")

    from app.core.encryption import decrypt_secret_payload
    try:
        adapter = AdapterRegistry.get_adapter(integration.provider)
        # Check capability
        caps = adapter.get_capabilities()
        if not caps.metrics_read:
            raise HTTPException(status_code=400, detail="Provider does not support metrics read")
            
        secrets = {}
        if integration.secret_payload:
            secrets = decrypt_secret_payload(integration.secret_payload)
            
        # The adapter needs a way to read metrics.
        if hasattr(adapter, "read_metrics"):
            return adapter.read_metrics(integration.configuration, secrets, metric_type=effective_metric)
        else:
            raise HTTPException(status_code=400, detail="Adapter implementation does not support metrics_read")
            
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook/prometheus", status_code=status.HTTP_200_OK)
def receive_prometheus_webhook(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Webhook receiver for Prometheus Alertmanager alerts.
    Supports demo app and production Alertmanager webhook integration.
    Normalizes alerts into RawEvents and routes them to the correlation & incident engine.
    """
    from app.models.integration import Integration
    from app.models.enums import ProviderType
    from app.services.event_ingestion import EventIngestionService
    from app.schemas.events import RawEventCreate
    from datetime import datetime, timezone

    # 1. Resolve or create a default Prometheus integration
    integration = db.query(Integration).filter(Integration.provider == ProviderType.PROMETHEUS.value).first()
    if not integration:
        integration = Integration(
            id=uuid.uuid4(),
            name="Prometheus Alertmanager",
            provider=ProviderType.PROMETHEUS.value,
            configuration={"base_url": "http://demo_app_prometheus:9090", "timeout_seconds": 10},
            status=IntegrationStatus.HEALTHY.value
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)

    event_service = EventIngestionService(db)
    alerts = payload.get("alerts", [])
    if not alerts and payload.get("status"):
        alerts = [payload]

    processed = 0
    for alert in alerts:
        labels = alert.get("labels", {})
        alertname = labels.get("alertname", "PrometheusAlert")
        state = alert.get("status", payload.get("status", "firing"))

        instance = labels.get("instance", "")
        job = labels.get("job", "weather-api")
        starts_at = alert.get("startsAt", datetime.now(timezone.utc).isoformat())
        external_event_id = f"{integration.id}-{alertname}-{job}-{instance}-{starts_at}"

        resource_external_id = f"{job}/{instance}" if instance else job

        event_in = RawEventCreate(
            provider=ProviderType.PROMETHEUS.value,
            integration_id=integration.id,
            external_event_id=external_event_id,
            event_type=f"prometheus_{state}",
            occurred_at=datetime.now(timezone.utc),
            resource_external_id=resource_external_id,
            payload=alert
        )
        event, is_new = event_service.ingest_event(event_in=event_in, current_user_id=None)
        if is_new:
            processed += 1

    return {"status": "ok", "alerts_received": len(alerts), "new_events_ingested": processed}

