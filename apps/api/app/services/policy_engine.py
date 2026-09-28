from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict, Any, List
from app.models.automation import AutomationExecution, PlaybookStep
from app.models.policy import Policy, PolicyDecision
from app.models.enums import PolicyDecisionType, RiskLevel, AutomationExecutionStatus
import logging

logger = logging.getLogger(__name__)

class PolicyEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_execution(self, execution: AutomationExecution) -> Tuple[PolicyDecisionType, Optional[str], Optional[Policy]]:
        """Evaluates policies against an active execution."""
        if execution.status != AutomationExecutionStatus.POLICY_EVALUATION.value:
            logger.error(f"Cannot evaluate policy for execution {execution.id} in state {execution.status}")
            return PolicyDecisionType.DENY, "Invalid execution state for policy evaluation", None

        # Build context
        context = {
            "risk_level": execution.risk_level,
            "action_type": [step.action_type for step in execution.playbook.steps],
            "provider": execution.resource.provider if execution.resource else None,
            "resource_type": execution.resource.resource_type if execution.resource else None,
            "incident_severity": execution.incident.severity if execution.incident else None,
            "environment": execution.resource.environment if execution.resource else None
        }
        
        decision, reason, matched_policy = self.simulate(context)
        return decision, reason, matched_policy

    def simulate(self, context: Dict[str, Any]) -> Tuple[PolicyDecisionType, str, Optional[Policy]]:
        """Simulates policy evaluation based on a dictionary context."""
        active_policies = self.db.query(Policy).filter(Policy.enabled == True).order_by(Policy.priority).all()
        
        if not active_policies:
            return PolicyDecisionType.DENY, "No active policies found. Defaulting to DENY.", None

        for policy in active_policies:
            match = True
            for rule in policy.rules:
                field_val = context.get(rule.field)
                
                if rule.operator == "EQUALS":
                    if field_val != rule.expected_value:
                        match = False
                        break
                elif rule.operator == "IN":
                    if isinstance(field_val, list):
                        if not any(a in rule.expected_value for a in field_val):
                            match = False
                            break
                    else:
                        if field_val not in rule.expected_value:
                            match = False
                            break
                elif rule.operator == "CONTAINS":
                    if isinstance(field_val, list) and rule.expected_value not in field_val:
                        match = False
                        break
                    
            if match:
                decision_str = policy.rules[0].decision if policy.rules else PolicyDecisionType.DENY.value
                return PolicyDecisionType(decision_str), f"Matched policy '{policy.name}'", policy
                
        return PolicyDecisionType.DENY, "No matching policy found. Defaulting to DENY.", None

    def record_decision(self, execution: AutomationExecution, decision: PolicyDecisionType, reason: str, policy: Optional[Policy] = None) -> PolicyDecision:
        policy_decision = PolicyDecision(
            execution_id=execution.id,
            policy_id=policy.id if policy else None,
            decision=decision.value,
            risk_level=execution.risk_level,
            reason=reason
        )
        self.db.add(policy_decision)
        self.db.flush()
        return policy_decision

# Compatibility wrappers for existing code
def evaluate_automation_policy(db: Session, execution: AutomationExecution) -> Tuple[PolicyDecisionType, Optional[str]]:
    engine = PolicyEngine(db)
    decision, reason, matched_policy = engine.evaluate_execution(execution)
    return decision, reason

def record_policy_decision(db: Session, execution: AutomationExecution, decision: PolicyDecisionType, reason: str) -> PolicyDecision:
    engine = PolicyEngine(db)
    # The original implementation doesn't pass the policy, so we leave it None or we query it. We'll leave it None for backward compat.
    return engine.record_decision(execution, decision, reason, None)
