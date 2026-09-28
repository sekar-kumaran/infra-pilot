import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import WorkflowExecutionStatus, WorkflowStepStatus, ApprovalStatus, VerificationStatus

class OperationWorkflow(Base):
    __tablename__ = "operation_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_conditions = Column(JSON, nullable=True, default=list)
    policy_configuration = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    steps = relationship("WorkflowStep", back_populates="workflow", order_by="WorkflowStep.sequence", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("operation_workflows.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    capability = Column(String(255), nullable=False)
    provider_constraint = Column(String(255), nullable=True)
    
    target_resolution_strategy = Column(JSON, nullable=True, default=dict)
    parameters = Column(JSON, nullable=True, default=dict)
    approval_requirement = Column(Boolean, default=False, nullable=False)
    timeout = Column(Integer, nullable=True)
    
    retry_policy = Column(JSON, nullable=True, default=dict)
    verification_strategy = Column(JSON, nullable=True, default=dict)
    failure_behavior = Column(JSON, nullable=True, default=dict)
    conditions = Column(JSON, nullable=True, default=dict)

    workflow = relationship("OperationWorkflow", back_populates="steps")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("operation_workflows.id", ondelete="CASCADE"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), nullable=False, default=WorkflowExecutionStatus.PENDING.value)
    current_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    error_classification = Column(String(100), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    execution_context = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workflow = relationship("OperationWorkflow", back_populates="executions")
    step_executions = relationship("WorkflowStepExecution", back_populates="execution", cascade="all, delete-orphan", order_by="WorkflowStepExecution.created_at")


class WorkflowStepExecution(Base):
    __tablename__ = "workflow_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    
    provider = Column(String(255), nullable=True)
    action = Column(String(255), nullable=True)
    target_resource_id = Column(UUID(as_uuid=True), ForeignKey("infrastructure_resources.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), nullable=False, default=WorkflowStepStatus.PENDING.value)
    verification_status = Column(String(50), nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    output = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    execution = relationship("WorkflowExecution", back_populates="step_executions")
