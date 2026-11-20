"""
Centralized SQLAlchemy 2.0 ORM Model Registry for InfraPilot.
Ensures all foreign key target tables (e.g., tenants.id, applications.id) are
registered in Base.metadata before any mapper or seed script executes.
"""
# Export all 30 domain entities in dependency order
__all__ = [
    "Tenant",
    "Application",
    "Environment",
    "InfrastructureResource",
    "ResourceRelationship",
    "Integration",
    "RawEvent",
    "Alert",
    "Incident",
    "IncidentEvent",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "ResourceScope",
    "AuditEvent",
    "Playbook",
    "PlaybookStep",
    "AutomationExecution",
    "AutomationStepExecution",
    "AutomationApproval",
    "Policy",
    "PolicyRule",
    "PolicyDecision",
    "FailedEvent",
    "WorkerNode",
    "OperationWorkflow",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowStepExecution",
]
