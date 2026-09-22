import hashlib
import json
from uuid import UUID
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.events import RawEvent
from app.models.enums import RawEventProcessingStatus
from app.repositories.events import EventRepository
from app.schemas.events import RawEventCreate
from app.services.audit import log_event
from app.workers.tasks import process_raw_event_task

class EventIngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def _canonicalize_payload(self, payload: Dict[str, Any]) -> str:
        """
        Deterministically canonicalize a JSON payload for hashing.
        """
        return json.dumps(payload, sort_keys=True, separators=(',', ':'))

    def _calculate_payload_hash(self, integration_id: str, provider: str, external_event_id: str, payload: Dict[str, Any]) -> str:
        """
        Calculate deterministic SHA-256 hash for idempotency.
        Hash inputs: integration_id + provider + external_event_id + payload
        """
        canonical_payload = self._canonicalize_payload(payload)
        external_id = external_event_id or ""
        raw_string = f"{integration_id}|{provider}|{external_id}|{canonical_payload}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def ingest_event(self, event_in: RawEventCreate, current_user_id: Optional[UUID] = None, request_id: str = None) -> Tuple[RawEvent, bool]:
        """
        Ingest a raw event from an integration.
        Returns Tuple[RawEvent, bool] where bool is True if it's a new event, False if duplicate.
        """
        # Calculate Idempotency Hash
        payload_hash = self._calculate_payload_hash(
            str(event_in.integration_id),
            event_in.provider,
            event_in.external_event_id,
            event_in.payload
        )
        
        # Check for duplication
        existing_event = self.event_repo.get_raw_event_by_hash(payload_hash)
        if existing_event:
            # Audit the duplicate submission
            log_event(
                db=self.db,
                actor_user_id=current_user_id,
                action="event.ingestion.duplicate",
                resource_type="raw_event",
                resource_id=str(existing_event.id),
                result="success",
                request_id=request_id,
                metadata={
                    "integration_id": str(event_in.integration_id),
                    "provider": event_in.provider,
                    "payload_hash": payload_hash
                }
            )
            self.db.commit()
            return existing_event, False

        # Create new RawEvent
        try:
            event_data = event_in.model_dump()
            # Explicitly set processing status to RECEIVED
            event = self.event_repo.create_raw_event(event_data, payload_hash)
            
            # Flush changes to assign ID before logging audit
            self.db.flush()
            
            log_event(
                db=self.db,
                actor_user_id=current_user_id,
                action="event.ingestion.success",
                resource_type="raw_event",
                resource_id=str(event.id),
                result="success",
                request_id=request_id,
                metadata={
                    "integration_id": str(event.integration_id),
                    "provider": event.provider,
                    "event_type": event.event_type
                }
            )
            # Transaction boundary: Commit the raw event to DB BEFORE enqueueing Celery task
            self.db.commit()
            self.db.refresh(event)
            
            # Enqueue to Celery
            process_raw_event_task.delay(str(event.id))
            
            return event, True
            
        except IntegrityError:
            self.db.rollback()
            # Race condition: someone else inserted the exact same hash
            existing_event = self.event_repo.get_raw_event_by_hash(payload_hash)
            if existing_event:
                return existing_event, False
            raise HTTPException(status_code=500, detail="Failed to ingest event due to integrity error")
