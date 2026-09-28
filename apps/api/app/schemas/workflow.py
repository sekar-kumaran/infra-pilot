from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import WorkflowExecutionStatus, WorkflowStepStatus, VerificationStatus

class WorkflowStepBase(BaseModel):
    sequence: int
    action: str
    capability: str
    provider_constraint: Optional[str] = None
    target_resolution_strategy: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    approval_requirement: bool = False
    timeout: Optional[int] = None
    retry_policy: Optional[Dict[str, Any]] = None
    verification_strategy: Optional[Dict[str, Any]] = None
    failure_behavior: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None

class WorkflowStepCreate(WorkflowStepBase):
    pass

class WorkflowStepResponse(WorkflowStepBase):
    id: UUID
    workflow_id: UUID

    model_config = ConfigDict(from_attributes=True)

class OperationWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger_type: str
    policy_configuration: Optional[Dict[str, Any]] = None

class OperationWorkflowCreate(OperationWorkflowBase):
    steps: List[WorkflowStepCreate]

class OperationWorkflowUpdate(OperationWorkflowBase):
    steps: Optional[List[WorkflowStepCreate]] = None

class OperationWorkflowResponse(OperationWorkflowBase):
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepResponse]

    model_config = ConfigDict(from_attributes=True)


class WorkflowStepExecutionResponse(BaseModel):
    id: UUID
    execution_id: UUID
    step_id: Optional[UUID] = None
    provider: Optional[str] = None
    action: Optional[str] = None
    target_resource_id: Optional[UUID] = None
    status: WorkflowStepStatus
    verification_status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    incident_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    status: WorkflowExecutionStatus
    current_step_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    error_classification: Optional[str] = None
    retry_count: int = 0
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    execution_context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    step_executions: List[WorkflowStepExecutionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class WorkflowTimelineEventResponse(BaseModel):
    timestamp: datetime
    event_type: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
