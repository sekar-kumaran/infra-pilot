import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
from app.models.enums import ApprovalStatus, AutomationExecutionStatus, VerificationStatus

class RemediationPlan(Base):
    __tablename__ = "remediation_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String(255), nullable=False)
    target_resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True)
    required_capability = Column(String(255), nullable=True)
    selected_action = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    risk_level = Column(String(50), nullable=False, default="LOW")
    parameters = Column(JSON, nullable=True, default=dict)
    
    approval_status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING.value)
    execution_status = Column(String(50), nullable=False, default=AutomationExecutionStatus.PENDING.value)
    verification_status = Column(String(50), nullable=False, default=VerificationStatus.PENDING.value)
    
    automation_execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_executions.id", ondelete="SET NULL"), nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    incident = relationship("Incident")
    target_resource = relationship("InfrastructureResource")
    automation_execution = relationship("AutomationExecution")
