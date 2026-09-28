from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.remediation import RemediationPlanResponse
from app.models.remediation import RemediationPlan
from app.models.user import User
from app.services.incident_pipeline import IncidentPipeline

router = APIRouter()

@router.get("/{id}", response_model=RemediationPlanResponse)
def get_remediation_plan(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("incidents:read")),
) -> Any:
    """
    Get remediation plan details.
    """
    plan = db.query(RemediationPlan).filter(RemediationPlan.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    return plan

@router.post("/{id}/approve", response_model=RemediationPlanResponse)
def approve_remediation_plan(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("incidents:write")),
) -> Any:
    """
    Approve a pending remediation plan.
    """
    pipeline = IncidentPipeline(db)
    try:
        plan = pipeline.approve_remediation_plan(id, current_user.id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/execute")
def execute_remediation_plan(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("incidents:write")),
) -> Any:
    """
    Execute an approved remediation plan.
    """
    # Just validate it exists and state is ready, then dispatch celery task
    from app.models.remediation import RemediationPlan
    from app.models.enums import ApprovalStatus, AutomationExecutionStatus
    
    plan = db.query(RemediationPlan).filter(RemediationPlan.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
        
    if plan.requires_approval and plan.approval_status != ApprovalStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail=f"Cannot execute. Approval status is {plan.approval_status}")
        
    if plan.execution_status not in [AutomationExecutionStatus.PENDING.value, AutomationExecutionStatus.APPROVED.value]:
        raise HTTPException(status_code=400, detail=f"Cannot execute plan in status {plan.execution_status}")
        
    # Dispatch task
    from app.workers.tasks import execute_remediation_task
    execute_remediation_task.delay(str(plan.id))
    
    return {"status": "dispatched", "message": "Remediation execution dispatched"}
