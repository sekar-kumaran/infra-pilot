from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

from app.models.incidents import Incident
from app.models.remediation import RemediationPlan
from app.models.enums import IncidentStatus, ApprovalStatus, AutomationExecutionStatus, VerificationStatus
from app.services.remediation_registry import RemediationRegistry
from app.services.provider_resolver import ProviderResolver
from app.repositories.resources import ResourceRepository
from app.services.incidents import IncidentService

logger = logging.getLogger(__name__)

class IncidentPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.incident_service = IncidentService(db)
        self.resource_repo = ResourceRepository(db)

    def evaluate_remediation_options(self, incident: Incident) -> List[Dict[str, Any]]:
        """
        Evaluate and return all valid remediation options for this incident.
        """
        if not incident.primary_resource_id:
            return []
            
        resource = self.resource_repo.get_by_id(incident.primary_resource_id)
        if not resource:
            return []

        options = []
        # Get all strategies that support this resource type
        strategies = RemediationRegistry.get_strategies_for_resource(resource.resource_type)
        
        for strategy in strategies:
            resolved = ProviderResolver.resolve_provider_for_strategy(strategy, resource.resource_type)
            if resolved:
                options.append({
                    "strategy": strategy.name,
                    "provider": resolved.provider,
                    "action": resolved.action,
                    "executor": resolved.executor,
                    "risk_level": resolved.risk.value,
                    "requires_approval": resolved.requires_approval,
                    "verification": resolved.verification
                })
        return options

    def create_remediation_plan(
        self, 
        incident_id: uuid.UUID, 
        strategy_name: str, 
        parameters: Dict[str, Any] = None
    ) -> RemediationPlan:
        """
        Creates a RemediationPlan mapping an incident to a provider execution.
        """
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        if not incident.primary_resource_id:
            raise ValueError("Incident has no primary resource")
            
        resource = self.resource_repo.get_by_id(incident.primary_resource_id)
        
        strategy = RemediationRegistry.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy {strategy_name}")
            
        resolved = ProviderResolver.resolve_provider_for_strategy(strategy, resource.resource_type)
        if not resolved:
            raise ValueError(f"No provider can execute {strategy_name} for {resource.resource_type}")

        # Idempotency check:
        existing = self.db.query(RemediationPlan).filter(
            RemediationPlan.incident_id == incident_id,
            RemediationPlan.strategy == strategy_name,
            RemediationPlan.target_resource_id == resource.id,
            RemediationPlan.execution_status.notin_([AutomationExecutionStatus.FAILED.value, AutomationExecutionStatus.SUCCEEDED.value])
        ).first()
        if existing:
            return existing
            
        plan = RemediationPlan(
            incident_id=incident.id,
            strategy=strategy_name,
            target_resource_id=resource.id,
            required_capability=strategy.required_capability,
            selected_action=resolved.action,
            provider=resolved.provider,
            requires_approval=resolved.requires_approval,
            risk_level=resolved.risk.value,
            parameters=parameters or {}
        )
        self.db.add(plan)
        
        # Move Incident to REMEDIATION_PENDING
        self.incident_service.update_incident_status(
            incident.id, 
            IncidentStatus.REMEDIATION_PENDING.value,
            actor_id=None,
            request_id=str(uuid.uuid4()),
            message=f"Remediation plan created: {strategy_name}"
        )
        
        # Depending on approval requirement, transition
        if resolved.requires_approval:
            plan.approval_status = ApprovalStatus.PENDING.value
            self.db.flush()
            self.incident_service.update_incident_status(
                incident.id, 
                IncidentStatus.APPROVAL_REQUIRED.value,
                actor_id=None,
                request_id=str(uuid.uuid4()),
                message="Waiting for remediation approval"
            )
        else:
            plan.approval_status = ApprovalStatus.APPROVED.value
            
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def approve_remediation_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> RemediationPlan:
        plan = self.db.query(RemediationPlan).filter(RemediationPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
            
        if plan.approval_status != ApprovalStatus.PENDING.value:
            raise ValueError("Plan is not pending approval")
            
        plan.approval_status = ApprovalStatus.APPROVED.value
        self.db.commit()
        return plan
