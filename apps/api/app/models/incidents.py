from typing import Dict, Any, List
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import Base
from app.models.enums import IncidentStatus, IncidentPriority, Severity, IncidentEventType

class Incident(Base):
    """
    Represents an operational problem derived from one or more correlated Alerts.
    """
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(String, nullable=True)
    
    severity = Column(String(50), default=Severity.UNKNOWN.value, nullable=False, index=True)
    status = Column(String(50), default=IncidentStatus.OPEN.value, nullable=False, index=True)
    priority = Column(String(50), nullable=True, index=True)
    
    primary_resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True, index=True)
    source = Column(String(255), nullable=True)
    
    # Used for grouping deterministic alerts into the same active incident
    correlation_key = Column(String(255), nullable=True, index=True)
    
    opened_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Phase 1.9 Operational Intelligence Fields
    incident_fingerprint = Column(String(255), nullable=True, index=True)
    correlation_confidence = Column(String(50), nullable=True) # E.g., HIGH, MEDIUM, LOW or exact value
    root_cause_candidate = Column(String, nullable=True)
    contributing_resources = Column(JSONB, nullable=False, default=list)
    related_alerts = Column(JSONB, nullable=False, default=list)
    related_incidents = Column(JSONB, nullable=False, default=list)
    duration_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IncidentEvent(Base):
    """
    Append-only timeline of everything that happens to an Incident.
    """
    __tablename__ = "incident_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(255), nullable=True)
    message = Column(String, nullable=True)
    event_metadata = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
