from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.enums import ResourceType, RiskLevel

class RemediationStrategy(BaseModel):
    name: str
    required_capability: str
    compatible_resource_types: List[ResourceType]
    allowed_actions: List[str]
    risk_level: RiskLevel
    requires_approval: bool
    verification_requirement: str
    timeout: int
    retry_policy: Dict[str, Any]

class RemediationRegistry:
    _strategies: Dict[str, RemediationStrategy] = {}

    @classmethod
    def register(cls, strategy: RemediationStrategy):
        cls._strategies[strategy.name] = strategy

    @classmethod
    def get_strategy(cls, name: str) -> Optional[RemediationStrategy]:
        return cls._strategies.get(name)

    @classmethod
    def get_all_strategies(cls) -> List[RemediationStrategy]:
        return list(cls._strategies.values())

    @classmethod
    def get_strategies_for_resource(cls, resource_type: ResourceType) -> List[RemediationStrategy]:
        return [s for s in cls._strategies.values() if resource_type in s.compatible_resource_types]

# Register default strategies
RemediationRegistry.register(RemediationStrategy(
    name="restore_service",
    required_capability="service_management",
    compatible_resource_types=[ResourceType.SERVICE, ResourceType.HOST, ResourceType.VM],
    allowed_actions=["restart_service", "ansible_restart_service"],
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    verification_requirement="verify_service_running",
    timeout=300,
    retry_policy={"max_attempts": 3, "delay_seconds": 10}
))

RemediationRegistry.register(RemediationStrategy(
    name="restart_container",
    required_capability="container_management",
    compatible_resource_types=[ResourceType.CONTAINER],
    allowed_actions=["docker_restart_container"],
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    verification_requirement="verify_container_running",
    timeout=120,
    retry_policy={"max_attempts": 3, "delay_seconds": 5}
))

RemediationRegistry.register(RemediationStrategy(
    name="restart_pod",
    required_capability="workload_management",
    compatible_resource_types=[ResourceType.KUBERNETES_POD],
    allowed_actions=["kubernetes_delete_pod"],
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    verification_requirement="verify_pod_running",
    timeout=120,
    retry_policy={"max_attempts": 2, "delay_seconds": 10}
))

RemediationRegistry.register(RemediationStrategy(
    name="restart_deployment",
    required_capability="workload_management",
    compatible_resource_types=[ResourceType.KUBERNETES_DEPLOYMENT],
    allowed_actions=["kubernetes_restart_deployment"],
    risk_level=RiskLevel.HIGH,
    requires_approval=True,
    verification_requirement="verify_deployment_ready",
    timeout=300,
    retry_policy={"max_attempts": 1, "delay_seconds": 0}
))

RemediationRegistry.register(RemediationStrategy(
    name="restart_instance",
    required_capability="cloud_compute_management",
    compatible_resource_types=[ResourceType.CLOUD_INSTANCE],
    allowed_actions=["aws_reboot_instance", "aws_start_instance"],
    risk_level=RiskLevel.HIGH,
    requires_approval=True,
    verification_requirement="aws_verify_instance_running",
    timeout=300,
    retry_policy={"max_attempts": 1, "delay_seconds": 0}
))

RemediationRegistry.register(RemediationStrategy(
    name="collect_diagnostics",
    required_capability="resource_read",
    compatible_resource_types=[
        ResourceType.CLOUD_INSTANCE, 
        ResourceType.KUBERNETES_POD, 
        ResourceType.CONTAINER, 
        ResourceType.HOST
    ],
    allowed_actions=["aws_collect_instance_information", "docker_collect_logs"],
    risk_level=RiskLevel.LOW,
    requires_approval=False,
    verification_requirement="none",
    timeout=60,
    retry_policy={"max_attempts": 1, "delay_seconds": 0}
))
