import uuid
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, Dict, Any
from app.models.automation import AutomationExecution, AutomationStepExecution, Playbook, AutomationApproval
from app.models.enums import AutomationExecutionStatus, ApprovalStatus, RiskLevel
from app.services.policy_engine import evaluate_automation_policy, record_policy_decision, PolicyDecisionType
from app.models.incidents import Incident
from app.repositories.incidents import IncidentRepository
from app.models.enums import IncidentEventType

def create_execution(
    db: Session,
    playbook_id: uuid.UUID,
    trigger_type: str,
    trigger_source: str,
    actor_user_id: Optional[uuid.UUID] = None,
    incident_id: Optional[uuid.UUID] = None,
    alert_id: Optional[uuid.UUID] = None,
    resource_id: Optional[uuid.UUID] = None
) -> AutomationExecution:
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
        
    if playbook.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Cannot execute non-active playbook")

    # Idempotency check:
    # If there's already a PENDING/RUNNING execution for the same playbook and context, return it
    # Simplified check for Phase 1.10
    existing = db.query(AutomationExecution).filter(
        AutomationExecution.playbook_id == playbook_id,
        AutomationExecution.incident_id == incident_id,
        AutomationExecution.alert_id == alert_id,
        AutomationExecution.resource_id == resource_id,
        AutomationExecution.status.in_([
            AutomationExecutionStatus.PENDING.value,
            AutomationExecutionStatus.POLICY_EVALUATION.value,
            AutomationExecutionStatus.AWAITING_APPROVAL.value,
            AutomationExecutionStatus.RUNNING.value,
            AutomationExecutionStatus.VERIFYING.value
        ])
    ).first()
    
    if existing:
        return existing

    from app.services.risk_engine import evaluate_execution_risk
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first() if incident_id else None
    
    execution = AutomationExecution(
        playbook_id=playbook_id,
        playbook_version=playbook.version,
        trigger_type=trigger_type,
        trigger_source=trigger_source,
        incident_id=incident_id,
        alert_id=alert_id,
        resource_id=resource_id,
        actor_user_id=actor_user_id,
        status=AutomationExecutionStatus.PENDING.value,
    )
    
    # Calculate Risk
    # In a real app we might load resource as well, simplified here
    risk = evaluate_execution_risk(db, playbook.steps, None, incident)
    execution.risk_level = risk.value
    
    db.add(execution)
    db.flush()

    # Create step executions
    for step in playbook.steps:
        step_exec = AutomationStepExecution(
            execution_id=execution.id,
            playbook_step_id=step.id,
            step_order=step.step_order,
        )
        db.add(step_exec)
        
    db.commit()
    db.refresh(execution)
    
    if incident_id:
        repo = IncidentRepository(db)
        repo.create_incident_event({
            "incident_id": incident_id,
            "event_type": IncidentEventType.REMEDIATION_STARTED.value,
            "source": "automation",
            "message": f"Automation execution {execution.id} created",
            "event_metadata": {}
        })

    return execution


def start_policy_evaluation(db: Session, execution: AutomationExecution):
    execution.status = AutomationExecutionStatus.POLICY_EVALUATION.value
    db.commit()


def process_policy_decision(db: Session, execution: AutomationExecution, decision: PolicyDecisionType, reason: str):
    record_policy_decision(db, execution, decision, reason)
    
    if decision == PolicyDecisionType.DENY:
        execution.status = AutomationExecutionStatus.REJECTED.value
        execution.error_message = f"Policy denied: {reason}"
        if execution.incident_id:
            repo = IncidentRepository(db)
            repo.create_incident_event({
                "incident_id": execution.incident_id,
                "event_type": IncidentEventType.REMEDIATION_COMPLETED.value,
                "source": "automation",
                "message": f"Automation execution {execution.id} rejected by policy",
                "event_metadata": {}
            })
            
    elif decision == PolicyDecisionType.ALLOW:
        execution.status = AutomationExecutionStatus.APPROVED.value
        # Actually approving immediately since policy allowed it
        
    elif decision == PolicyDecisionType.REQUIRE_APPROVAL:
        execution.status = AutomationExecutionStatus.AWAITING_APPROVAL.value
        # Create approval record
        approval = AutomationApproval(
            execution_id=execution.id,
            status=ApprovalStatus.PENDING.value,
        )
        db.add(approval)
        if execution.incident_id:
            repo = IncidentRepository(db)
            repo.create_incident_event({
                "incident_id": execution.incident_id,
                "event_type": IncidentEventType.STATUS_CHANGED.value,
                "source": "automation",
                "message": f"Automation execution {execution.id} requires approval",
                "event_metadata": {}
            })

    db.commit()


def approve_execution(db: Session, approval_id: uuid.UUID, user_id: uuid.UUID) -> AutomationApproval:
    approval = db.query(AutomationApproval).filter(AutomationApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot approve in state {approval.status}")
        
    execution = approval.execution
    
    # Self-approval protection for HIGH/CRITICAL risk
    if execution.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value] and execution.actor_user_id == user_id:
        raise HTTPException(status_code=403, detail="Self-approval for high/critical risk is forbidden")
        
    approval.status = ApprovalStatus.APPROVED.value
    approval.approved_at = datetime.datetime.utcnow()
    approval.approved_by = user_id
    
    execution.status = AutomationExecutionStatus.APPROVED.value
    db.commit()
    db.refresh(approval)
    
    if execution.incident_id:
        repo = IncidentRepository(db)
        repo.create_incident_event({
            "incident_id": execution.incident_id,
            "event_type": IncidentEventType.STATUS_CHANGED.value,
            "source": "automation",
            "message": f"Automation execution {execution.id} approved",
            "event_metadata": {}
        })
        
    return approval


def reject_execution(db: Session, approval_id: uuid.UUID, user_id: uuid.UUID, reason: str) -> AutomationApproval:
    approval = db.query(AutomationApproval).filter(AutomationApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot reject in state {approval.status}")
        
    approval.status = ApprovalStatus.REJECTED.value
    approval.rejected_at = datetime.datetime.utcnow()
    approval.rejected_by = user_id
    approval.reason = reason
    
    execution = approval.execution
    execution.status = AutomationExecutionStatus.REJECTED.value
    db.commit()
    db.refresh(approval)
    return approval
