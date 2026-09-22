from typing import Dict, Any, List
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import Base
from app.models.enums import ProviderType, Severity, AlertStatus, RawEventProcessingStatus

class RawEvent(Base):
    """
    Immutable representation of the original payload received from an external integration.
    Append-only for forensic analysis, audit, and correlation replay.
    """
    __tablename__ = "raw_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    external_event_id = Column(String(255), nullable=True)
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSONB, nullable=False, default=dict)
    payload_hash = Column(String(64), nullable=False, unique=True, index=True)
    source = Column(String(255), nullable=True)
    resource_external_id = Column(String(255), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True)
    processing_status = Column(String(50), default=RawEventProcessingStatus.RECEIVED.value, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Alert(Base):
    """
    Normalized operational signal derived from a RawEvent.
    The schema is provider-neutral and forms the basis for correlation.
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_event_id = Column(UUID(as_uuid=True), ForeignKey("raw_events.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(50), nullable=False)
    
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), default=Severity.UNKNOWN.value, nullable=False, index=True)
    status = Column(String(50), default=AlertStatus.ACTIVE.value, nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    description = Column(String, nullable=True)
    labels = Column(JSONB, nullable=False, default=dict)
    
    starts_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Used for deterministic deduplication of equivalent alerts
    fingerprint = Column(String(64), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
