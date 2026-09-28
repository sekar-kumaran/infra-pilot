from typing import Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.deps import get_db, require_permission, get_current_user
from app.models.user import User
from app.schemas.inventory import (
    InfrastructureResourceCreate,
    InfrastructureResourceUpdate,
    InfrastructureResourceResponse,
    ResourceListResponse,
    ResourceRelationshipCreate,
    ResourceRelationshipResponse,
    RelationshipListResponse
)
from app.services.resources import ResourceService
from app.models.enums import ResourceType, ProviderType, ResourceStatus


router = APIRouter()

# --- Resource Endpoints ---

@router.post(
    "/",
    response_model=InfrastructureResourceResponse,
    status_code=201,
    dependencies=[Depends(require_permission("resources:create"))]
)
def create_resource(
    *,
    db = Depends(get_db),
    resource_in: InfrastructureResourceCreate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    resource = service.create_resource(resource_in, current_user=current_user, request_id=request_id)
    db.commit()
    return resource

@router.get(
    "/",
    response_model=ResourceListResponse,
    dependencies=[Depends(require_permission("resources:read"))]
)
def list_resources(
    *,
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    resource_type: Optional[ResourceType] = None,
    provider: Optional[ProviderType] = None,
    environment_id: Optional[UUID] = None,
    status: Optional[ResourceStatus] = None,
    name: Optional[str] = None,
    external_id: Optional[str] = None
) -> Any:
    service = ResourceService(db)
    items, total = service.list_resources(
        page=page, page_size=page_size,
        resource_type=resource_type, provider=provider,
        environment_id=environment_id, status=status,
        name=name, external_id=external_id
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get(
    "/{resource_id}",
    response_model=InfrastructureResourceResponse,
    dependencies=[Depends(require_permission("resources:read"))]
)
def get_resource(
    *,
    db = Depends(get_db),
    resource_id: UUID
) -> Any:
    service = ResourceService(db)
    return service.get_resource(resource_id)

@router.patch(
    "/{resource_id}",
    response_model=InfrastructureResourceResponse,
    dependencies=[Depends(require_permission("resources:update"))]
)
def update_resource(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    resource_in: InfrastructureResourceUpdate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    resource = service.update_resource(resource_id, resource_in, current_user=current_user, request_id=request_id)
    db.commit()
    return resource

# --- Relationship Endpoints ---

@router.post(
    "/{resource_id}/relationships",
    response_model=ResourceRelationshipResponse,
    status_code=201,
    dependencies=[Depends(require_permission("relationships:create"))]
)
def create_relationship(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    relationship_in: ResourceRelationshipCreate,
    current_user: User = Depends(get_current_user),
    request_id: str = "req-123"
) -> Any:
    service = ResourceService(db)
    rel = service.create_relationship(resource_id, relationship_in, current_user=current_user, request_id=request_id)
    db.commit()
    return rel

@router.get(
    "/{resource_id}/relationships",
    response_model=RelationshipListResponse,
    dependencies=[Depends(require_permission("relationships:read"))]
)
def list_relationships(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
) -> Any:
    service = ResourceService(db)
    items, total = service.list_relationships(resource_id, page=page, page_size=page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

from app.models.audit import AuditEvent

@router.get(
    "/{resource_id}/history",
    dependencies=[Depends(require_permission("resources:read"))]
)
def list_resource_history(
    *,
    db = Depends(get_db),
    resource_id: UUID,
) -> Any:
    events = db.query(AuditEvent).filter(
        AuditEvent.resource_id == str(resource_id)
    ).order_by(AuditEvent.timestamp.desc()).all()
    
    return [
        {
            "id": e.id,
            "action": e.action,
            "actor_user_id": e.actor_user_id,
            "result": e.result,
            "timestamp": e.timestamp,
            "metadata_": e.metadata_
        }
        for e in events
    ]


# --- Resource Live Data Endpoints (Docker-aware) ---

def _get_docker_client_for_resource(resource, db):
    """Find the Docker integration for a resource and return a ready client."""
    from app.models.integration import Integration
    from app.integrations.providers.docker.adapter import DockerIntegrationAdapter
    from app.services.integration_crypto import decrypt_secrets

    integration = db.query(Integration).filter(
        Integration.provider == "docker",
        Integration.status == "HEALTHY"
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="No healthy Docker integration found")

    adapter = DockerIntegrationAdapter()
    secrets = decrypt_secrets(integration.encrypted_secrets or {})
    return adapter._get_client(integration.configuration, secrets)


@router.get(
    "/{resource_id}/logs",
    dependencies=[Depends(require_permission("resources:read"))]
)
def get_resource_logs(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    tail: int = Query(200, ge=10, le=1000),
) -> Any:
    """
    Fetch the last N log lines for a Docker container resource.
    """
    service = ResourceService(db)
    resource = service.get_resource(resource_id)

    if resource.provider != "docker":
        raise HTTPException(status_code=400, detail="Logs are only supported for Docker provider resources")
    if resource.resource_type not in ("CONTAINER",):
        raise HTTPException(status_code=400, detail="Logs are only available for container resources")

    # Extract docker container ID from external_id: "docker/container/<id>"
    parts = (resource.external_id or "").split("/")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Cannot determine container ID from resource")
    container_id = parts[-1]

    try:
        client = _get_docker_client_for_resource(resource, db)
        logs = client.get_container_logs(container_id, max_lines=tail)
        lines = [l for l in logs.splitlines() if l.strip()]
        return {"resource_id": str(resource_id), "container_id": container_id, "lines": lines, "total": len(lines)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch logs: {str(e)}")


@router.get(
    "/{resource_id}/metrics",
    dependencies=[Depends(require_permission("resources:read"))]
)
def get_resource_metrics(
    *,
    db = Depends(get_db),
    resource_id: UUID,
) -> Any:
    """
    Fetch real-time CPU and memory stats for a Docker container resource.
    """
    service = ResourceService(db)
    resource = service.get_resource(resource_id)

    if resource.provider != "docker" or resource.resource_type != "CONTAINER":
        raise HTTPException(status_code=400, detail="Metrics currently only supported for Docker container resources")

    parts = (resource.external_id or "").split("/")
    container_id = parts[-1] if len(parts) >= 3 else None
    if not container_id:
        raise HTTPException(status_code=400, detail="Cannot determine container ID")

    try:
        client = _get_docker_client_for_resource(resource, db)
        raw = client.get_container_stats(container_id)
        if not raw:
            return {"cpu_percent": 0, "memory_mb": 0, "memory_limit_mb": 0, "memory_percent": 0}

        # Calculate CPU %
        cpu_delta = raw.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) - \
                    raw.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
        system_delta = raw.get("cpu_stats", {}).get("system_cpu_usage", 0) - \
                       raw.get("precpu_stats", {}).get("system_cpu_usage", 0)
        num_cpus = len(raw.get("cpu_stats", {}).get("cpu_usage", {}).get("percpu_usage") or [1])
        cpu_percent = round((cpu_delta / system_delta) * num_cpus * 100.0, 2) if system_delta > 0 else 0

        # Memory
        mem_stats = raw.get("memory_stats", {})
        mem_usage = mem_stats.get("usage", 0) - mem_stats.get("stats", {}).get("cache", 0)
        mem_limit = mem_stats.get("limit", 1)
        mem_mb = round(mem_usage / 1024 / 1024, 2)
        mem_limit_mb = round(mem_limit / 1024 / 1024, 2)
        mem_percent = round((mem_usage / mem_limit) * 100, 2) if mem_limit > 0 else 0

        # Network I/O
        networks = raw.get("networks", {})
        net_rx = sum(n.get("rx_bytes", 0) for n in networks.values())
        net_tx = sum(n.get("tx_bytes", 0) for n in networks.values())

        # Block I/O
        blkio = raw.get("blkio_stats", {}).get("io_service_bytes_recursive") or []
        blk_read = sum(b.get("value", 0) for b in blkio if b.get("op") == "read")
        blk_write = sum(b.get("value", 0) for b in blkio if b.get("op") == "write")

        return {
            "resource_id": str(resource_id),
            "container_id": container_id,
            "cpu_percent": cpu_percent,
            "memory_mb": mem_mb,
            "memory_limit_mb": mem_limit_mb,
            "memory_percent": mem_percent,
            "net_rx_mb": round(net_rx / 1024 / 1024, 3),
            "net_tx_mb": round(net_tx / 1024 / 1024, 3),
            "blk_read_mb": round(blk_read / 1024 / 1024, 3),
            "blk_write_mb": round(blk_write / 1024 / 1024, 3),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch metrics: {str(e)}")


@router.post(
    "/{resource_id}/actions/{action}",
    dependencies=[Depends(require_permission("resources:update"))]
)
def perform_resource_action(
    *,
    db = Depends(get_db),
    resource_id: UUID,
    action: str,
) -> Any:
    """
    Perform a lifecycle action on a Docker container: start | stop | restart.
    """
    ALLOWED_ACTIONS = {"start", "stop", "restart"}
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Action must be one of: {', '.join(ALLOWED_ACTIONS)}")

    service = ResourceService(db)
    resource = service.get_resource(resource_id)

    if resource.provider != "docker" or resource.resource_type != "CONTAINER":
        raise HTTPException(status_code=400, detail="Actions only supported for Docker container resources")

    parts = (resource.external_id or "").split("/")
    container_id = parts[-1] if len(parts) >= 3 else None
    if not container_id:
        raise HTTPException(status_code=400, detail="Cannot determine container ID")

    try:
        client = _get_docker_client_for_resource(resource, db)
        if action == "start":
            client.start_container(container_id)
        elif action == "stop":
            client.stop_container(container_id)
        elif action == "restart":
            client.restart_container(container_id)
        return {"success": True, "action": action, "container_id": container_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to {action} container: {str(e)}")
