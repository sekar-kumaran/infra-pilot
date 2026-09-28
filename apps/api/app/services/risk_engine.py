from typing import Optional
from sqlalchemy.orm import Session
from app.models.enums import RiskLevel, AutomationActionType, EnvironmentType, Severity
from app.models.automation import PlaybookStep
from app.models.resource import InfrastructureResource
from app.models.incidents import Incident
from app.services.action_registry import ActionRegistry

def calculate_step_risk(step: PlaybookStep) -> RiskLevel:
    """Calculate the base risk of a playbook step based on its action."""
    action_def = ActionRegistry.get_action(step.action_name)
    if action_def:
        return action_def.risk_level
    
    # Fallback mappings for safety
    if step.action_type in [AutomationActionType.COLLECT_INFORMATION, AutomationActionType.VALIDATE_RESOURCE, AutomationActionType.NOOP]:
        return RiskLevel.LOW
    elif step.action_type == AutomationActionType.EXECUTE_PROVIDER_ACTION:
        return RiskLevel.HIGH
    
    return RiskLevel.HIGH  # Default unknown actions to high risk

def evaluate_execution_risk(
    db: Session,
    steps: list[PlaybookStep],
    resource: Optional[InfrastructureResource] = None,
    incident: Optional[Incident] = None
) -> RiskLevel:
    """
    Deterministically evaluates the overall risk of an automation execution.
    Risk is the maximum of the calculated step risks, elevated by context.
    """
    highest_step_risk = RiskLevel.LOW
    
    for step in steps:
        step_risk = calculate_step_risk(step)
        if step_risk == RiskLevel.CRITICAL:
            highest_step_risk = RiskLevel.CRITICAL
        elif step_risk == RiskLevel.HIGH and highest_step_risk not in [RiskLevel.CRITICAL]:
            highest_step_risk = RiskLevel.HIGH
        elif step_risk == RiskLevel.MEDIUM and highest_step_risk in [RiskLevel.LOW]:
            highest_step_risk = RiskLevel.MEDIUM

    # Elevate based on environment context
    if resource and resource.environment_id:
        # Load environment to check if it's production
        # Assuming we can check resource.environment.environment_type
        # We will use a safe access pattern if environment is loaded
        # For phase 1.10, we'll elevate HIGH -> CRITICAL for production
        env = resource.environment
        if env and env.environment_type == EnvironmentType.PRODUCTION.value and highest_step_risk in [RiskLevel.HIGH]:
            return RiskLevel.CRITICAL

    # Elevate based on incident context
    if incident and incident.severity == Severity.CRITICAL.value and highest_step_risk in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
        # Critical incidents with mutating actions are critical risk
        if highest_step_risk != RiskLevel.LOW:
            return RiskLevel.CRITICAL

    return highest_step_risk
