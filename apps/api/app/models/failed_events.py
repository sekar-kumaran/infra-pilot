from typing import Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import Base
from app.models.enums import FailedEventStatus

class FailedEvent(Base):
    """
    Durable representation of an event that failed to process.
    Tracks celery task failures, retries, and manual operator actions.
    """
    __tablename__ = "failed_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_event_id = Column(UUID(as_uuid=True), ForeignKey("raw_events.id", ondelete="CASCADE"), nullable=False, index=True)
    
    task_name = Column(String(255), nullable=False)
    failure_type = Column(String(100), nullable=False)
    failure_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Optional payload/metadata snapshot to assist operators (sanitized)
    payload_reference = Column(JSONB, nullable=True)
    
    status = Column(String(50), default=FailedEventStatus.FAILED.value, nullable=False, index=True)
    
    first_failed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_failed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
