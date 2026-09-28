import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.remediation import RemediationPlan
from app.models.incidents import Incident
from app.models.resource import InfrastructureResource
from app.models.automation import AutomationExecution
from app.models.enums import (
    AutomationExecutionStatus,
    ApprovalStatus,
    VerificationStatus,
    IncidentStatus,
    IncidentEventType,
    RiskLevel
)
from app.repositories.incidents import IncidentRepository
from app.services.provider_resolver import ProviderResolver
from app.services.remediation_registry import RemediationRegistry
from app.adapters.automation.factory import ExecutorFactory
from app.services.audit import log_event

class RemediationExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)

    def execute_remediation_plan(self, plan_id: uuid.UUID) -> bool:
        """
        Executes a remediation plan synchronously.
        For production, this would be wrapped in a Celery task.
        """
        plan = self.db.query(RemediationPlan).filter(RemediationPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Remediation plan not found")

        # 1. Validate Approval
        if plan.requires_approval and plan.approval_status != ApprovalStatus.APPROVED.value:
            raise ValueError(f"Remediation requires approval but status is {plan.approval_status}")

        # 2. Validate Execution State
        if plan.execution_status not in [AutomationExecutionStatus.PENDING.value, AutomationExecutionStatus.APPROVED.value]:
            raise ValueError(f"Cannot execute plan in status {plan.execution_status}")

        # 3. Load Incident and Validate State
        incident = self.db.query(Incident).filter(Incident.id == plan.incident_id).first()
        if not incident:
            raise ValueError("Associated incident not found")
            
        if incident.status in [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value]:
            raise ValueError("Cannot remediate a resolved or closed incident")

        # 4. Resolve target resource
        if not plan.target_resource_id:
            raise ValueError("Remediation plan has no target resource")
            
        resource = self.db.query(InfrastructureResource).filter(InfrastructureResource.id == plan.target_resource_id).first()
        if not resource:
            raise ValueError("Target resource not found")

        # 5. Lock (Simple DB lock via state transition)
        # Assuming we just do optimistic updates here
        plan.execution_status = AutomationExecutionStatus.RUNNING.value
        plan.started_at = datetime.utcnow()
        self.db.commit()

        self._record_incident_event(incident.id, IncidentEventType.REMEDIATION_STARTED.value, f"Execution of remediation plan {plan.id} started")
        incident.status = IncidentStatus.REMEDIATION_RUNNING.value
        self.db.commit()

        # 6. Resolve Provider, Action, Executor
        strategy = RemediationRegistry.get_strategy(plan.strategy)
        resolved = ProviderResolver.resolve_provider_for_strategy(strategy, resource.resource_type)
        if not resolved:
            self._fail_execution(plan, incident, "Failed to resolve provider and executor for strategy")
            return False

        executor = ExecutorFactory.get_executor(resolved.executor)
        if not executor:
            self._fail_execution(plan, incident, f"Executor {resolved.executor} not found")
            return False

        # Build parameters
        params = plan.parameters or {}
        # The executors usually expect external_id or similar to identify the resource
        params["external_id"] = resource.external_id
        if resource.metadata_:
            params.update(resource.metadata_)

        # 7. Dispatch Execution
        try:
            success, output, error_msg = executor.execute(resolved.action, params)
        except Exception as e:
            success = False
            output = {}
            error_msg = str(e)

        if not success:
            self._fail_execution(plan, incident, f"Execution failed: {error_msg}")
            return False

        # 8. Verification
        plan.execution_status = AutomationExecutionStatus.VERIFYING.value
        self.db.commit()

        try:
            # Note: For real world this would be asynchronous polling. 
            # In E2E we might want to do bounded polling.
            verified_success, state, verify_msg = executor.verify(resolved.action, expected_state={"status": "running"}, parameters=params)
        except Exception as e:
            verified_success = False
            verify_msg = str(e)

        if not verified_success:
            plan.verification_status = VerificationStatus.FAILED.value
            plan.execution_status = AutomationExecutionStatus.SUCCEEDED.value # Action ran, but verification failed
            plan.completed_at = datetime.utcnow()
            
            incident.status = IncidentStatus.ESCALATED.value
            self.db.commit()
            self._record_incident_event(incident.id, IncidentEventType.STATUS_CHANGED.value, f"Verification failed: {verify_msg}. Incident escalated.")
            return False

        # 9. Success updates
        plan.verification_status = VerificationStatus.PASSED.value
        plan.execution_status = AutomationExecutionStatus.SUCCEEDED.value
        plan.completed_at = datetime.utcnow()
        
        incident.status = IncidentStatus.RECOVERED.value
        self.db.commit()
        
        self._record_incident_event(incident.id, IncidentEventType.REMEDIATION_COMPLETED.value, f"Remediation successful and verified.")
        return True


    def _fail_execution(self, plan: RemediationPlan, incident: Incident, reason: str):
        plan.execution_status = AutomationExecutionStatus.FAILED.value
        plan.failure_reason = reason
        plan.completed_at = datetime.utcnow()
        
        incident.status = IncidentStatus.ESCALATED.value
        self.db.commit()
        
        self._record_incident_event(incident.id, IncidentEventType.STATUS_CHANGED.value, f"Remediation failed: {reason}. Incident escalated.")


    def _record_incident_event(self, incident_id: uuid.UUID, event_type: str, message: str):
        self.incident_repo.create_incident_event({
            "incident_id": incident_id,
            "event_type": event_type,
            "source": "remediation_executor",
            "message": message,
            "event_metadata": {}
        })

