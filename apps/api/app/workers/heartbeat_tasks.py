import logging
import socket
from datetime import datetime, timezone, timedelta
from celery import shared_task
from sqlalchemy.orm import Session
from app.workers.celery_app import celery_app
from app.database.session import get_session_factory
from app.models.worker import WorkerNode

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="app.workers.heartbeat_tasks.send_heartbeat_task", ignore_result=True)
def send_heartbeat_task(self):
    """
    Periodic task executed by each worker to register its heartbeat.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    # Identify this worker
    worker_id = self.request.hostname or socket.gethostname()
    
    try:
        worker_node = db.query(WorkerNode).filter(WorkerNode.worker_id == worker_id).first()
        now = datetime.now(timezone.utc)
        
        if not worker_node:
            worker_node = WorkerNode(
                worker_id=worker_id,
                hostname=socket.gethostname(),
                status="ONLINE",
                active_tasks=0, # To be filled by inspector if needed
                concurrency=1,
                version="1.0.0",
                started_at=now,
                last_heartbeat=now
            )
            db.add(worker_node)
        else:
            worker_node.status = "ONLINE"
            worker_node.last_heartbeat = now
            
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to send heartbeat for worker {worker_id}: {e}")
    finally:
        db.close()

@shared_task(name="app.workers.heartbeat_tasks.monitor_worker_health_task", ignore_result=True)
def monitor_worker_health_task():
    """
    Periodic task run globally to check if any workers missed their heartbeats.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=2)
        
        # Any worker whose last heartbeat is older than 2 minutes is considered OFFLINE
        stale_workers = db.query(WorkerNode).filter(
            WorkerNode.status.in_(["ONLINE", "DEGRADED"]),
            WorkerNode.last_heartbeat < threshold
        ).all()
        
        for worker in stale_workers:
            logger.warning(f"Worker {worker.worker_id} missed heartbeats. Marking OFFLINE.")
            worker.status = "OFFLINE"
            
        if stale_workers:
            db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to monitor worker health: {e}")
    finally:
        db.close()
