import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database.base import Base
from app.models.environment import Environment

class InfrastructureResource(Base):
    __tablename__ = "infrastructure_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    resource_type = Column(String, index=True, nullable=False)
    provider = Column(String, index=True, nullable=False)
    environment_id = Column(UUID(as_uuid=True), ForeignKey('environments.id', ondelete='CASCADE'), index=True, nullable=True)
    external_id = Column(String, index=True, nullable=True)
    status = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('provider', 'external_id', name='uix_provider_external_id'),
    )
