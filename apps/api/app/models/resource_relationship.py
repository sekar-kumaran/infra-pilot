import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database.base import Base

class ResourceRelationship(Base):
    __tablename__ = "resource_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_resource_id = Column(UUID(as_uuid=True), ForeignKey('infrastructure_resources.id', ondelete='CASCADE'), index=True, nullable=False)
    target_resource_id = Column(UUID(as_uuid=True), ForeignKey('infrastructure_resources.id', ondelete='CASCADE'), index=True, nullable=False)
    relationship_type = Column(String, index=True, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('source_resource_id', 'target_resource_id', 'relationship_type', name='uix_resource_relationship'),
    )
