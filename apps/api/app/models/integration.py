from typing import Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import Base
from app.models.enums import ProviderType, IntegrationStatus
from app.models.tenant import Tenant

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    status = Column(String(50), default=IntegrationStatus.CONFIGURED.value, nullable=False)
    
    # Safe configuration that does not contain secrets
    configuration = Column(JSONB, nullable=False, default=dict)
    
    # Encrypted payload containing sensitive tokens, passwords, etc.
    secret_payload = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    # Circuit Breaker state
    circuit_state = Column(String(50), nullable=False, default="CLOSED")
    failure_count = Column(Integer, nullable=False, default=0)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
