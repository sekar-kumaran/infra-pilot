from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.worker import WorkerNode
from app.api.deps import get_current_user
from app.api.dependencies.tenant import get_current_tenant
from app.services.authorization import AuthorizationService
from app.models.tenant import Tenant
from app.workers.celery_app import celery_app

router = APIRouter()

@router.get("/workers")
def list_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> List[Dict[str, Any]]:
    """List all workers in the fleet."""
    authz = AuthorizationService(db)
    if not authz.check_permission(current_user, "operations:read", current_tenant_id=current_tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view workers.")
        
    workers = db.query(WorkerNode).all()
    return [{
        "id": w.id,
        "worker_id": w.worker_id,
        "hostname": w.hostname,
        "status": w.status,
        "active_tasks": w.active_tasks,
        "queue": w.queue,
        "concurrency": w.concurrency,
        "version": w.version,
        "last_heartbeat": w.last_heartbeat,
        "started_at": w.started_at
    } for w in workers]

@router.get("/workers/{worker_id}")
def get_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Get details for a specific worker."""
    authz = AuthorizationService(db)
    if not authz.check_permission(current_user, "operations:read", current_tenant_id=current_tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view workers.")
        
    worker = db.query(WorkerNode).filter(WorkerNode.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
        
    return {
        "id": worker.id,
        "worker_id": worker.worker_id,
        "hostname": worker.hostname,
        "status": worker.status,
        "active_tasks": worker.active_tasks,
        "queue": worker.queue,
        "concurrency": worker.concurrency,
        "version": worker.version,
        "last_heartbeat": worker.last_heartbeat,
        "started_at": worker.started_at
    }

@router.get("/queues")
def list_queues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> List[Dict[str, Any]]:
    """Get queue health and stats."""
    authz = AuthorizationService(db)
    if not authz.check_permission(current_user, "operations:read", current_tenant_id=current_tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view queues.")
        
    # Attempt to query celery inspect to get real queue stats if RabbitMQ/Redis allows
    # For now, we will return a structured response with empty/simulated data 
    # if inspect is not available or blocked.
    
    inspect = celery_app.control.inspect()
    active_tasks = inspect.active() or {}
    reserved_tasks = inspect.reserved() or {}
    
    queues_map = {}
    
    # Calculate queue depths (basic implementation)
    # Note: real queue depth normally requires polling RabbitMQ API or Redis directly.
    # Celery inspect only gives us tasks currently held by workers.
    
    for worker_name, tasks in active_tasks.items():
        for task in tasks:
            q = task.get('delivery_info', {}).get('routing_key', 'celery')
            if q not in queues_map:
                queues_map[q] = {'pending': 0, 'active': 0, 'reserved': 0, 'workers': set()}
            queues_map[q]['active'] += 1
            queues_map[q]['workers'].add(worker_name)
            
    for worker_name, tasks in reserved_tasks.items():
        for task in tasks:
            q = task.get('delivery_info', {}).get('routing_key', 'celery')
            if q not in queues_map:
                queues_map[q] = {'pending': 0, 'active': 0, 'reserved': 0, 'workers': set()}
            queues_map[q]['reserved'] += 1
            queues_map[q]['workers'].add(worker_name)

    results = []
    for q_name, stats in queues_map.items():
        results.append({
            "queue_name": q_name,
            "pending_tasks": stats['pending'],
            "active_tasks": stats['active'],
            "reserved_tasks": stats['reserved'],
            "worker_count": len(stats['workers']),
            "healthy_worker_count": len(stats['workers']), # would map from db
            "unhealthy_worker_count": 0
        })
        
    if not results:
        # Default empty fallback for 'celery' queue
        results.append({
            "queue_name": "celery",
            "pending_tasks": 0,
            "active_tasks": 0,
            "reserved_tasks": 0,
            "worker_count": 0,
            "healthy_worker_count": 0,
            "unhealthy_worker_count": 0
        })
        
    return results

@router.get("/health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Get overall system control-plane health."""
    authz = AuthorizationService(db)
    if not authz.check_permission(current_user, "operations:read", current_tenant_id=current_tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
        
    workers = db.query(WorkerNode).all()
    online = sum(1 for w in workers if w.status == "ONLINE")
    degraded = sum(1 for w in workers if w.status == "DEGRADED")
    offline = sum(1 for w in workers if w.status == "OFFLINE")
    
    return {
        "status": "HEALTHY" if online > 0 else "DEGRADED",
        "workers": {
            "total": len(workers),
            "online": online,
            "degraded": degraded,
            "offline": offline
        }
    }
