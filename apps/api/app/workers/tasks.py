from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json

from app.workers.celery_app import celery_app
from app.database.session import get_session_factory
from app.models.events import RawEvent
from app.models.enums import RawEventProcessingStatus
from app.services.correlation import CorrelationService

logger = logging.getLogger(__name__)

@celery_app.task(
    name="process_raw_event_task",
    bind=True,
    max_retries=3,
    autoretry_for=(SQLAlchemyError,),
    retry_backoff=True
)
def process_raw_event_task(self, raw_event_id: str):
    logger.info(f"Starting processing for raw event {raw_event_id}")
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        raw_event = db.query(RawEvent).filter(RawEvent.id == UUID(raw_event_id)).first()
        if not raw_event:
            logger.error(f"RawEvent {raw_event_id} not found.")
            return

        if raw_event.processing_status != RawEventProcessingStatus.RECEIVED.value:
            logger.warning(f"RawEvent {raw_event_id} already processed or in progress. Status: {raw_event.processing_status}")
            return
            
        raw_event.processing_status = RawEventProcessingStatus.PROCESSING.value
        db.commit()

        correlation_service = CorrelationService(db)
        
        # 1. Normalize
        alert = correlation_service.normalize_event(raw_event)
        
        # 2. Correlate
        incident = correlation_service.correlate_alert(alert)

        # 3. Mark Processed
        raw_event.processing_status = RawEventProcessingStatus.PROCESSED.value
        db.commit()
        logger.info(f"Successfully processed raw event {raw_event_id}. Incident: {incident.id}")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error processing raw event {raw_event_id}: {str(e)}")
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Permanent failure processing raw event {raw_event_id}: {str(e)}")
        # Mark as FAILED if we can fetch it again
        try:
            failed_event = db.query(RawEvent).filter(RawEvent.id == UUID(raw_event_id)).first()
            if failed_event:
                failed_event.processing_status = RawEventProcessingStatus.FAILED.value
                # Assuming payload is dict, we should not overwrite it completely, but we can't easily add error msg.
                # Just mark as FAILED. 
                db.commit()
        except Exception:
            db.rollback()
            
        # We do not raise here because it's a permanent failure, we don't want to retry indefinitely.
        return
        
    finally:
        db.close()
