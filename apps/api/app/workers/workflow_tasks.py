import logging
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session
from app.workers.celery_app import celery_app
from app.database.session import get_session_factory
from app.models.workflow import WorkflowExecution
from app.models.enums import WorkflowExecutionStatus
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

@shared_task(name="app.workers.workflow_tasks.process_retries_task", ignore_result=True)
def process_retries_task():
    """
    Finds workflow executions in RETRYING state where next_retry_at has passed,
    and resumes their execution.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        retrying_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == WorkflowExecutionStatus.RETRYING.value,
            WorkflowExecution.next_retry_at <= now
        ).all()
        
        if retrying_executions:
            logger.info(f"Found {len(retrying_executions)} workflow executions to retry.")
            engine = WorkflowEngine(db)
            
            for execution in retrying_executions:
                try:
                    logger.info(f"Retrying workflow execution {execution.id} (Attempt {execution.retry_count + 1})")
                    # Transition to RUNNING before starting
                    engine._transition_state(execution, WorkflowExecutionStatus.RUNNING.value)
                    execution.last_attempt_at = now
                    db.commit()
                    
                    # Instead of blocking the whole loop, we can just call start_execution
                    # In a fully distributed system, this would queue a specific Celery task
                    # per workflow execution, but for now we run it synchronously here.
                    engine.start_execution(execution.id)
                except Exception as ex:
                    logger.error(f"Error during retry of execution {execution.id}: {ex}")
                    db.rollback()
    except Exception as e:
        logger.error(f"Failed to process workflow retries: {e}")
        db.rollback()
    finally:
        db.close()
