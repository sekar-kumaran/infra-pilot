from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database.session import get_db
from app.api.deps import get_current_user, require_permission
from app.models.user import User
from app.models.automation import Playbook, AutomationExecution, AutomationApproval
from app.models.policy import Policy
from app.services.automation import create_execution, start_policy_evaluation, approve_execution, reject_execution
from app.workers.tasks import evaluate_automation_policy_task
from pydantic import BaseModel
import subprocess

router = APIRouter()

@router.get("/schedules")
def list_schedules(current_user: User = Depends(require_permission("automation:read"))):
    return []

class PlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    version: int = 1

class ExecutionCreate(BaseModel):
    playbook_id: uuid.UUID
    trigger_type: str
    trigger_source: str
    incident_id: Optional[uuid.UUID] = None
    alert_id: Optional[uuid.UUID] = None
    resource_id: Optional[uuid.UUID] = None

class ApprovalAction(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    reason: Optional[str] = None


@router.post("/playbooks", status_code=201)
def create_playbook(
    playbook_in: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("playbooks:create"))
):
    playbook = Playbook(
        name=playbook_in.name,
        description=playbook_in.description,
        trigger_type=playbook_in.trigger_type,
        version=playbook_in.version,
        created_by=current_user.id
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    return {"id": playbook.id, "name": playbook.name, "status": playbook.status}


@router.get("/playbooks")
def list_playbooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("playbooks:read"))
):
    playbooks = db.query(Playbook).all()
    return [{"id": p.id, "name": p.name, "status": p.status, "version": p.version} for p in playbooks]


@router.get("/templates")
def list_playbook_templates(current_user: User = Depends(require_permission("playbooks:read"))):
    """
    Phase 3: Pre-built templates for automated runbook execution.
    These are the out-of-the-box templates developers can use.
    """
    return [
        {
            "id": "tpl-1",
            "name": "Restart Service / Container",
            "description": "Standard restart procedure. Health checks pre- and post-restart.",
            "trigger_type": "MANUAL",
            "tags": ["core", "recovery"]
        },
        {
            "id": "tpl-2",
            "name": "Collect Memory Heap Dump",
            "description": "Triggered on High Memory. Collects a heap dump and uploads to S3.",
            "trigger_type": "ALERT",
            "tags": ["diagnostics", "memory"]
        },
        {
            "id": "tpl-3",
            "name": "Rollback to Previous Version",
            "description": "Rolls back a deployment. Requires approval if in production environment.",
            "trigger_type": "MANUAL",
            "tags": ["deployment", "rollback"]
        },
        {
            "id": "tpl-4",
            "name": "Clear Cache",
            "description": "Flushes Redis cache and warms up critical paths.",
            "trigger_type": "MANUAL",
            "tags": ["maintenance", "cache"]
        }
    ]


@router.post("/executions", status_code=201)
def trigger_automation(
    execution_in: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:execute"))
):
    try:
        execution = create_execution(
            db=db,
            playbook_id=execution_in.playbook_id,
            trigger_type=execution_in.trigger_type,
            trigger_source=execution_in.trigger_source,
            actor_user_id=current_user.id,
            incident_id=execution_in.incident_id,
            alert_id=execution_in.alert_id,
            resource_id=execution_in.resource_id
        )
        
        # Start evaluation
        start_policy_evaluation(db, execution)
        
        # Trigger async task for policy evaluation
        evaluate_automation_policy_task.delay(str(execution.id))
        
        return {"execution_id": execution.id, "status": execution.status, "risk_level": execution.risk_level}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions")
def list_executions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:read"))
):
    from sqlalchemy.orm import joinedload
    executions = db.query(AutomationExecution).options(
        joinedload(AutomationExecution.playbook),
        joinedload(AutomationExecution.resource)
    ).order_by(AutomationExecution.created_at.desc()).all()
    
    result = []
    for ex in executions:
        item = {
            "id": ex.id,
            "playbook_id": ex.playbook_id,
            "status": ex.status,
            "risk_level": ex.risk_level,
            "started_at": ex.started_at,
            "completed_at": ex.completed_at,
            "playbook": {"name": ex.playbook.name} if ex.playbook else None,
            "resource": ex.resource.name if ex.resource else None,
            "resource_type": ex.resource.resource_type if ex.resource else None,
            "metadata_": ex.resource.metadata_ if ex.resource else None,
        }
        result.append(item)
    return result


@router.get("/executions/{execution_id}")
def get_execution(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:read"))
):
    execution = db.query(AutomationExecution).filter(AutomationExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    return {
        "id": execution.id,
        "playbook_id": execution.playbook_id,
        "status": execution.status,
        "risk_level": execution.risk_level,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "error_message": execution.error_message
    }


@router.get("/approvals")
def list_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:read"))
):
    approvals = db.query(AutomationApproval).all()
    result = []
    for a in approvals:
        result.append({
            "id": a.id,
            "execution_id": a.execution_id,
            "status": a.status,
            "created_at": a.created_at,
            "action_by": a.action_by,
            "action_at": a.action_at
        })
    return result

@router.post("/approvals/{approval_id}/action")
def action_approval(
    approval_id: uuid.UUID,
    action_in: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:approve"))
):
    try:
        if action_in.action == "APPROVE":
            approval = approve_execution(db, approval_id, current_user.id)
            
            # Since it was approved, queue the execution task
            from app.workers.tasks import execute_automation_task
            execute_automation_task.delay(str(approval.execution_id))
            
            return {"status": approval.status, "execution_status": approval.execution.status}
        elif action_in.action == "REJECT":
            approval = reject_execution(db, approval_id, current_user.id, action_in.reason or "Rejected by user")
            return {"status": approval.status, "execution_status": approval.execution.status}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers")
def list_providers(current_user: User = Depends(require_permission("automation:read"))):
    return [
        {"provider": "ansible", "status": "AVAILABLE"},
        {"provider": "kubernetes", "status": "AVAILABLE"}
    ]


@router.get("/providers/ansible/status")
def get_ansible_status(current_user: User = Depends(require_permission("automation:read"))):
    try:
        result = subprocess.run(["ansible-playbook", "--version"], capture_output=True, text=True, check=False)
        available = result.returncode == 0
        version = result.stdout.split('\n')[0] if available else None
        return {
            "provider": "ansible",
            "available": available,
            "version": version,
            "executable": "ansible-playbook"
        }
    except Exception:
        return {
            "provider": "ansible",
            "available": False,
            "version": None,
            "executable": "ansible-playbook"
        }

@router.get("/providers/kubernetes/status")
def get_kubernetes_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("automation:read"))
):
    try:
        from app.models.integration import Integration
        from app.models.enums import ProviderType
        from app.integrations.registry import AdapterRegistry
        
        has_integration = db.query(Integration).filter(Integration.provider == ProviderType.KUBERNETES).first() is not None
        
        return {
            "provider": "kubernetes",
            "available": has_integration,
            "version": "v1 (REST API)",
            "capabilities": ["RESOURCE_DISCOVERY", "RESOURCE_READ", "AUTOMATION"],
            "available_actions": [
                "kubernetes_scale_deployment", 
                "kubernetes_restart_pod", 
                "kubernetes_collect_pod_information", 
                "kubernetes_collect_deployment_information", 
                "kubernetes_verify_deployment"
            ]
        }
    except Exception:
        return {
            "provider": "kubernetes",
            "available": False,
            "version": None,
            "capabilities": [],
            "available_actions": []
        }
