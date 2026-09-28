from pydantic import BaseModel, Field
from typing import Dict, Any, Type, Optional, Callable
from app.models.enums import AutomationActionType, RiskLevel, ResourceType

class ActionParameterSchema(BaseModel):
    name: str
    type: str
    required: bool
    description: str

class ActionDefinition(BaseModel):
    action_name: str
    action_type: AutomationActionType
    risk_level: RiskLevel
    parameter_schema: list[ActionParameterSchema]
    executor_name: str
    target_resource_types: list[ResourceType] = Field(default_factory=list)
    requires_approval: bool = False
    timeout: int = 300
    retry_policy: Optional[str] = None
    verification_strategy: Optional[str] = None
    compensating_action: Optional[str] = None
    reversible: bool = False

class ActionRegistry:
    _actions: Dict[str, ActionDefinition] = {}

    @classmethod
    def register(cls, definition: ActionDefinition):
        cls._actions[definition.action_name] = definition

    @classmethod
    def get_action(cls, action_name: str) -> Optional[ActionDefinition]:
        return cls._actions.get(action_name)

    @classmethod
    def get_all_actions(cls) -> list[ActionDefinition]:
        return list(cls._actions.values())

    @classmethod
    def validate_parameters(cls, action_name: str, parameters: dict) -> bool:
        action = cls.get_action(action_name)
        if not action:
            return False
        
        for param in action.parameter_schema:
            if param.required and param.name not in parameters:
                return False
        return True


# Pre-register Phase 1.10 Test Actions
ActionRegistry.register(ActionDefinition(
    action_name="test_action_success",
    action_type=AutomationActionType.NOOP,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="test_executor",
    verification_strategy="test_verify_success"
))

ActionRegistry.register(ActionDefinition(
    action_name="test_action_failure",
    action_type=AutomationActionType.NOOP,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="test_executor",
    verification_strategy="test_verify_failure"
))

ActionRegistry.register(ActionDefinition(
    action_name="test_action_timeout",
    action_type=AutomationActionType.NOOP,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="test_executor"
))

ActionRegistry.register(ActionDefinition(
    action_name="test_collect_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[ActionParameterSchema(name="query", type="string", required=True, description="The query to collect information")],
    executor_name="test_executor"
))

ActionRegistry.register(ActionDefinition(
    action_name="test_validate_resource",
    action_type=AutomationActionType.VALIDATE_RESOURCE,
    risk_level=RiskLevel.LOW,
    parameter_schema=[ActionParameterSchema(name="resource_id", type="string", required=True, description="The resource ID")],
    executor_name="test_executor"
))

# Simulate a high-risk test action
ActionRegistry.register(ActionDefinition(
    action_name="test_provider_mutation",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[ActionParameterSchema(name="action_param", type="string", required=True, description="Action param")],
    executor_name="test_executor"
))

# --- Phase 1.14: Real Ansible Provider Actions ---

# Low Risk Actions
ActionRegistry.register(ActionDefinition(
    action_name="collect_system_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM]
))

ActionRegistry.register(ActionDefinition(
    action_name="check_service",
    action_type=AutomationActionType.VALIDATE_RESOURCE,
    risk_level=RiskLevel.LOW,
    parameter_schema=[
        ActionParameterSchema(name="service_name", type="string", required=True, description="The name of the service to check")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM]
))

ActionRegistry.register(ActionDefinition(
    action_name="check_disk_usage",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM]
))

ActionRegistry.register(ActionDefinition(
    action_name="check_memory_usage",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM]
))

# High Risk / Mutating Actions
ActionRegistry.register(ActionDefinition(
    action_name="restart_service",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="service_name", type="string", required=True, description="The name of the service to restart")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.SERVICE],
    requires_approval=True,
    verification_strategy="verify_service"
))

ActionRegistry.register(ActionDefinition(
    action_name="start_service",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="service_name", type="string", required=True, description="The name of the service to start")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.SERVICE],
    requires_approval=True,
    verification_strategy="verify_service"
))

ActionRegistry.register(ActionDefinition(
    action_name="stop_service",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="service_name", type="string", required=True, description="The name of the service to stop")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.SERVICE],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="restart_docker_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="container_name", type="string", required=True, description="The name of the docker container to restart")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.CONTAINER],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="inspect_docker_container",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[
        ActionParameterSchema(name="container_name", type="string", required=True, description="The name of the docker container")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.CONTAINER]
))

ActionRegistry.register(ActionDefinition(
    action_name="start_docker_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="container_name", type="string", required=True, description="The name of the docker container")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.CONTAINER],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="stop_docker_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="container_name", type="string", required=True, description="The name of the docker container")
    ],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM, ResourceType.CONTAINER],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="validate_configuration",
    action_type=AutomationActionType.VALIDATE_RESOURCE,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM]
))

ActionRegistry.register(ActionDefinition(
    action_name="deploy_configuration",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="rollback_configuration",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="ansible",
    target_resource_types=[ResourceType.HOST, ResourceType.VM],
    requires_approval=True
))

# --- Phase 1.15: Real Kubernetes Provider Actions ---

# Low Risk Actions
ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_collect_pod_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_POD]
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_collect_deployment_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT]
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_collect_service_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_SERVICE]
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_verify_deployment",
    action_type=AutomationActionType.VALIDATE_RESOURCE,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT]
))

# High Risk / Mutating Actions
ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_scale_deployment",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[
        ActionParameterSchema(name="desired_replicas", type="integer", required=True, description="The desired number of replicas")
    ],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    requires_approval=True,
    verification_strategy="kubernetes_verify_scale"
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_restart_pod",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_POD],
    requires_approval=True,
    verification_strategy="kubernetes_verify_restart"
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_restart_deployment",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    requires_approval=True,
    verification_strategy="kubernetes_verify_deployment_rollout"
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_pause_deployment",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    requires_approval=True
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_resume_deployment",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    requires_approval=True
))

# --- Phase 1.17: Real Docker Provider Actions ---

# Read / Low-risk Actions
ActionRegistry.register(ActionDefinition(
    action_name="docker_collect_container_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER],
    requires_approval=False,
    timeout=60
))

ActionRegistry.register(ActionDefinition(
    action_name="docker_inspect_image",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER_IMAGE],
    requires_approval=False,
    timeout=60
))

ActionRegistry.register(ActionDefinition(
    action_name="docker_collect_container_logs",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[
        ActionParameterSchema(name="max_lines", type="integer", required=False, description="Maximum number of log lines to retrieve (default 100)"),
    ],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER],
    requires_approval=False,
    timeout=30
))

# Medium-risk / Mutating Actions
ActionRegistry.register(ActionDefinition(
    action_name="docker_start_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.MEDIUM,
    parameter_schema=[],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER],
    requires_approval=True,
    timeout=60,
    verification_strategy="docker_verify_container_running"
))

# High-risk / Mutating Actions
ActionRegistry.register(ActionDefinition(
    action_name="docker_restart_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER],
    requires_approval=True,
    timeout=120,
    verification_strategy="docker_verify_container_running"
))

ActionRegistry.register(ActionDefinition(
    action_name="docker_stop_container",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="docker",
    target_resource_types=[ResourceType.CONTAINER],
    requires_approval=True,
    timeout=60,
    verification_strategy="docker_verify_container_stopped"
))

# AWS Actions
ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_instance_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_volume_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_VOLUME],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_network_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_VPC, ResourceType.CLOUD_SUBNET, ResourceType.CLOUD_SECURITY_GROUP, ResourceType.CLOUD_NETWORK],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_start_instance",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.MEDIUM,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=True,
    timeout=60,
    verification_strategy="aws_verify_instance_running"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_stop_instance",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=True,
    timeout=120,
    verification_strategy="aws_verify_instance_stopped"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_reboot_instance",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=True,
    timeout=180,
    verification_strategy="aws_verify_instance_running"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_terminate_instance",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=True,
    timeout=120,
    verification_strategy="aws_verify_instance_terminated"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_asg_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_AUTO_SCALING_GROUP],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_set_asg_desired_capacity",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[ActionParameterSchema(name="desired_capacity", type="integer", required=True, description="Desired capacity for ASG")],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_AUTO_SCALING_GROUP],
    requires_approval=True,
    timeout=300,
    verification_strategy="aws_verify_asg_capacity"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_suspend_asg_process",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_AUTO_SCALING_GROUP],
    requires_approval=True,
    timeout=60
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_resume_asg_process",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_AUTO_SCALING_GROUP],
    requires_approval=True,
    timeout=60
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_database_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.DATABASE_INSTANCE],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_collect_bucket_information",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_BUCKET],
    requires_approval=False,
    timeout=30
))

ActionRegistry.register(ActionDefinition(
    action_name="kubernetes_restart_deployment",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="kubernetes",
    target_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    requires_approval=True,
    timeout=120,
    verification_strategy="kubernetes_verify_deployment"
))

ActionRegistry.register(ActionDefinition(
    action_name="aws_reboot_instance",
    action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
    risk_level=RiskLevel.HIGH,
    parameter_schema=[],
    executor_name="aws",
    target_resource_types=[ResourceType.CLOUD_INSTANCE],
    requires_approval=True,
    timeout=300,
    verification_strategy="aws_verify_instance_running"
))

ActionRegistry.register(ActionDefinition(
    action_name="prometheus_query",
    action_type=AutomationActionType.COLLECT_INFORMATION,
    risk_level=RiskLevel.LOW,
    parameter_schema=[],
    executor_name="prometheus",
    target_resource_types=[],
    requires_approval=False
))
