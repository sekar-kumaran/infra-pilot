import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
from app.models.enums import (
    PlaybookStatus,
    PlaybookTriggerType,
    AutomationActionType,
    AutomationExecutionStatus,
    AutomationStepStatus,
    RiskLevel,
    ApprovalStatus,
    VerificationStatus
)

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default=PlaybookStatus.DRAFT.value)
    trigger_type = Column(String(50), nullable=False, default=PlaybookTriggerType.MANUAL.value)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    steps = relationship("PlaybookStep", back_populates="playbook", order_by="PlaybookStep.step_order", cascade="all, delete-orphan")
    executions = relationship("AutomationExecution", back_populates="playbook")


class PlaybookStep(Base):
    __tablename__ = "playbook_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    action_name = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    risk_level = Column(String(50), nullable=False, default=RiskLevel.LOW.value)
    timeout_seconds = Column(Integer, nullable=False, default=300)
    continue_on_failure = Column(Boolean, nullable=False, default=False)
    verification_config = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    playbook = relationship("Playbook", back_populates="steps")


class AutomationExecution(Base):
    __tablename__ = "automation_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id"), nullable=False)
    playbook_version = Column(Integer, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_source = Column(String(255), nullable=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), nullable=False, default=AutomationExecutionStatus.PENDING.value)
    risk_level = Column(String(50), nullable=False, default=RiskLevel.LOW.value)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)  # metadata is a reserved attribute in SQLAlchemy Model
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    playbook = relationship("Playbook", back_populates="executions")
    incident = relationship("Incident")
    alert = relationship("Alert")
    resource = relationship("InfrastructureResource")
    step_executions = relationship("AutomationStepExecution", back_populates="execution", order_by="AutomationStepExecution.step_order", cascade="all, delete-orphan")
    approvals = relationship("AutomationApproval", back_populates="execution", cascade="all, delete-orphan")


class AutomationStepExecution(Base):
    __tablename__ = "automation_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False)
    playbook_step_id = Column(UUID(as_uuid=True), ForeignKey("playbook_steps.id", ondelete="SET NULL"), nullable=True)
    step_order = Column(Integer, nullable=False)
    
    status = Column(String(50), nullable=False, default=AutomationStepStatus.PENDING.value)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    output = Column(JSON, nullable=True)  # Ensure no sensitive information
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    execution = relationship("AutomationExecution", back_populates="step_executions")
    verification_result = relationship("VerificationResult", back_populates="step_execution", uselist=False, cascade="all, delete-orphan")


class AutomationApproval(Base):
    __tablename__ = "automation_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING.value)
    
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    reason = Column(Text, nullable=True)

    execution = relationship("AutomationExecution", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approved_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False)
    step_execution_id = Column(UUID(as_uuid=True), ForeignKey("automation_step_executions.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50), nullable=False, default=VerificationStatus.PENDING.value)
    expected_state = Column(JSON, nullable=True)
    observed_state = Column(JSON, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    execution = relationship("AutomationExecution")
    step_execution = relationship("AutomationStepExecution", back_populates="verification_result")
