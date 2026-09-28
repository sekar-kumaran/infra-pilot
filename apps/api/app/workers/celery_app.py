from celery import Celery
from app.core.config import settings

# Import all models so SQLAlchemy can resolve foreign keys during flush
import app.models.tenant
import app.models.user
import app.models.rbac
import app.models.audit
import app.models.environment
import app.models.resource
import app.models.resource_relationship
import app.models.integration
import app.models.events
import app.models.failed_events
import app.models.incidents
import app.models.automation
import app.models.policy
import app.models.remediation
import app.models.workflow
import app.models.worker

celery_app = Celery(
    "infrapilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.integration_tasks", "app.workers.tasks", "app.workers.heartbeat_tasks", "app.workers.workflow_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    beat_schedule={
        'poll-prometheus-alerts': {
            'task': 'app.workers.integration_tasks.poll_prometheus_alerts_task',
            'schedule': 30.0, # Poll every 30 seconds
        },
        'poll-nagios-status': {
            'task': 'app.workers.integration_tasks.poll_nagios_status_task',
            'schedule': 60.0, # Poll every 60 seconds
        },
        'worker-heartbeat': {
            'task': 'app.workers.heartbeat_tasks.send_heartbeat_task',
            'schedule': 30.0,
        },
        'monitor-worker-health': {
            'task': 'app.workers.heartbeat_tasks.monitor_worker_health_task',
            'schedule': 60.0,
        },
        'process-workflow-retries': {
            'task': 'app.workers.workflow_tasks.process_retries_task',
            'schedule': 10.0, # Check for retries every 10 seconds
        },
    }
)
