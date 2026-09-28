from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import logging
import re

from app.models.incidents import Incident
from app.models.events import Alert
from app.models.workflow import OperationWorkflow, WorkflowExecution
from app.models.resource import InfrastructureResource
from app.services.workflow_engine import WorkflowEngine
from app.workers.tasks import execute_workflow_task
from app.models.enums import WorkflowExecutionStatus

logger = logging.getLogger(__name__)

class EventTriggerService:
    def __init__(self, db: Session):
        self.db = db
        self.workflow_engine = WorkflowEngine(db)

    def evaluate_and_trigger(self, incident: Incident) -> List[WorkflowExecution]:
        """
        Evaluates active, enabled workflows with trigger_type="event" against the incident.
        Returns a list of created executions.
        """
        # Find active workflows with event triggers
        workflows = self.db.query(OperationWorkflow).filter(
            OperationWorkflow.enabled == True,
            OperationWorkflow.trigger_type == "event"
        ).all()
        
        triggered_executions = []
        
        # Load resource if available
        resource = None
        if incident.primary_resource_id:
            resource = self.db.query(InfrastructureResource).filter(InfrastructureResource.id == incident.primary_resource_id).first()
            
        # Get alerts to match against (from related_alerts JSONB or just assume mock passes them)
        alerts = []
        if incident.related_alerts:
            alerts = self.db.query(Alert).filter(Alert.id.in_(incident.related_alerts)).all()
        
        for workflow in workflows:
            conditions = workflow.trigger_conditions or []
            if not conditions:
                continue
                
            # If ANY condition block matches, trigger the workflow
            if any(self._evaluate_condition(cond, incident, resource, alerts) for cond in conditions):
                
                # Enforce idempotency: prevent multiple running/pending executions for the same incident + workflow
                existing = self.db.query(WorkflowExecution).filter(
                    WorkflowExecution.workflow_id == workflow.id,
                    WorkflowExecution.incident_id == incident.id,
                    WorkflowExecution.status.in_([
                        WorkflowExecutionStatus.PENDING.value,
                        WorkflowExecutionStatus.RUNNING.value,
                        WorkflowExecutionStatus.WAITING_APPROVAL.value,
                        WorkflowExecutionStatus.VERIFYING.value,
                        WorkflowExecutionStatus.SUCCEEDED.value
                    ])
                ).first()
                
                if existing:
                    logger.info(f"Workflow {workflow.name} already triggered for Incident {incident.id}, skipping.")
                    continue
                
                logger.info(f"Triggering workflow {workflow.name} for Incident {incident.id}")
                
                # We enforce approval requirement inside the engine when it hits a step
                # The workflow itself starts and pauses if approval is needed.
                execution = WorkflowExecution(
                    workflow_id=workflow.id,
                    incident_id=incident.id,
                    resource_id=incident.primary_resource_id,
                    execution_context={"source": "event_trigger", "incident_id": str(incident.id)}
                )
                self.db.add(execution)
                self.db.flush()
                
                # Kick off execution
                execute_workflow_task.delay(str(execution.id))
                triggered_executions.append(execution)
                
        self.db.commit()
        return triggered_executions

    def _evaluate_condition(self, condition: Dict[str, Any], incident: Incident, resource: Optional[InfrastructureResource], alerts: List[Alert]) -> bool:
        """
        Evaluates a single condition dictionary against the incident context.
        All specified keys must match (AND logic).
        """
        if "provider" in condition:
            if not any(a.provider == condition["provider"] for a in alerts):
                return False
                
        if "resource_type" in condition:
            if not resource or resource.resource_type != condition["resource_type"]:
                return False
                
        if "severity" in condition:
            if incident.severity != condition["severity"]:
                return False
                
        if "alert_name" in condition:
            pattern = condition["alert_name"]
            try:
                # Simple exact match or regex
                matched = False
                for a in alerts:
                    if a.alert_name == pattern or re.match(pattern, a.alert_name):
                        matched = True
                        break
                if not matched:
                    return False
            except Exception:
                return False

        if "environment" in condition:
            # Check resource tags or metadata if we track env
            # For simplicity, if not tracked, fail if required
            return False

        return True
