from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.workflow import (
    OperationWorkflowCreate,
    OperationWorkflowUpdate,
    OperationWorkflowResponse,
    WorkflowExecutionResponse
)
from app.models.workflow import OperationWorkflow, WorkflowStep, WorkflowExecution
from app.models.user import User
from app.services.workflow_engine import WorkflowEngine
from app.workers.tasks import execute_workflow_task

router = APIRouter()

@router.post("/", response_model=OperationWorkflowResponse)
def create_workflow(
    *,
    db: Session = Depends(deps.get_db),
    workflow_in: OperationWorkflowCreate,
    current_user: User = Depends(deps.require_permission("workflows:write")),
) -> Any:
    workflow = OperationWorkflow(
        name=workflow_in.name,
        description=workflow_in.description,
        enabled=workflow_in.enabled,
        trigger_type=workflow_in.trigger_type,
        policy_configuration=workflow_in.policy_configuration
    )
    db.add(workflow)
    db.flush()
    
    for step_in in workflow_in.steps:
        step = WorkflowStep(
            workflow_id=workflow.id,
            sequence=step_in.sequence,
            action=step_in.action,
            capability=step_in.capability,
            provider_constraint=step_in.provider_constraint,
            target_resolution_strategy=step_in.target_resolution_strategy,
            parameters=step_in.parameters,
            approval_requirement=step_in.approval_requirement,
            timeout=step_in.timeout,
            retry_policy=step_in.retry_policy,
            verification_strategy=step_in.verification_strategy,
            failure_behavior=step_in.failure_behavior,
            conditions=step_in.conditions
        )
        db.add(step)
        
    db.commit()
    db.refresh(workflow)
    return workflow

@router.get("/", response_model=List[OperationWorkflowResponse])
def get_workflows(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    return db.query(OperationWorkflow).all()

@router.get("/{id}", response_model=OperationWorkflowResponse)
def get_workflow(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    workflow = db.query(OperationWorkflow).filter(OperationWorkflow.id == id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.post("/{id}/validate")
def validate_workflow(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    workflow = db.query(OperationWorkflow).filter(OperationWorkflow.id == id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    engine = WorkflowEngine(db)
    return engine.validate_workflow(workflow)

@router.post("/{id}/execute", response_model=WorkflowExecutionResponse)
def execute_workflow(
    id: UUID,
    incident_id: UUID = None,
    resource_id: UUID = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:execute")),
) -> Any:
    workflow = db.query(OperationWorkflow).filter(OperationWorkflow.id == id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        incident_id=incident_id,
        resource_id=resource_id,
        execution_context={"actor_id": str(current_user.id)}
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Queue celery task
    execute_workflow_task.delay(str(execution.id))
    
    return execution

@router.get("/executions", response_model=List[WorkflowExecutionResponse])
def get_all_executions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    return db.query(WorkflowExecution).order_by(WorkflowExecution.created_at.desc()).all()

@router.get("/{id}/executions", response_model=List[WorkflowExecutionResponse])
def get_workflow_executions(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    return db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == id).all()

from app.schemas.workflow import WorkflowTimelineEventResponse

@router.get("/executions/{execution_id}/timeline", response_model=List[WorkflowTimelineEventResponse])
def get_execution_timeline(
    execution_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:read")),
) -> Any:
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow execution not found")
        
    events = []
    
    # 1. Execution Started
    events.append({
        "timestamp": execution.created_at,
        "event_type": "EXECUTION_CREATED",
        "message": f"Workflow execution {execution.id} created",
        "metadata": {"status": "PENDING"}
    })
    
    if execution.started_at:
        events.append({
            "timestamp": execution.started_at,
            "event_type": "EXECUTION_STARTED",
            "message": "Workflow execution started running",
            "metadata": {}
        })
        
    # 2. Steps
    for step_exec in execution.step_executions:
        events.append({
            "timestamp": step_exec.created_at,
            "event_type": "STEP_STARTED",
            "message": f"Step {step_exec.step.sequence if step_exec.step else 'Unknown'} ({step_exec.action}) started",
            "metadata": {"action": step_exec.action, "provider": step_exec.provider}
        })
        
        if step_exec.completed_at:
            events.append({
                "timestamp": step_exec.completed_at,
                "event_type": "STEP_COMPLETED",
                "message": f"Step ({step_exec.action}) completed with status {step_exec.status}",
                "metadata": {"status": step_exec.status, "error": step_exec.error, "verification_status": step_exec.verification_status}
            })
            
    # 3. Execution Completed
    if execution.completed_at:
        events.append({
            "timestamp": execution.completed_at,
            "event_type": "EXECUTION_COMPLETED",
            "message": f"Workflow execution completed with status {execution.status}",
            "metadata": {"status": execution.status, "failure_reason": execution.failure_reason}
        })
        
    events.sort(key=lambda x: x["timestamp"])
    return events

@router.post("/executions/{execution_id}/resume")
def resume_workflow_execution(
    execution_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("workflows:execute")),
) -> Any:
    # We will use WorkflowEngine to attempt resume
    engine = WorkflowEngine(db)
    return engine.resume_workflow_execution(execution_id, current_user.id)
