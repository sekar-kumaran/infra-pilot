import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.models.enums import ResourceType, ProviderType
from app.services.provider_resolver import ProviderResolver
from app.services.remediation_registry import RemediationRegistry
from app.integrations.registry import AdapterRegistry
from app.integrations.providers.aws.adapter import AWSAdapter
from app.integrations.providers.kubernetes.adapter import KubernetesProviderAdapter

AdapterRegistry.register(AWSAdapter)
AdapterRegistry.register(KubernetesProviderAdapter)

strategy = RemediationRegistry.get_strategy("restart_instance")
print(f"Strategy: {strategy}")
resolved = ProviderResolver.resolve_provider_for_strategy(strategy, ResourceType.CLOUD_INSTANCE)
print(f"Resolved AWS: {resolved}")

strategy2 = RemediationRegistry.get_strategy("restart_deployment")
print(f"Strategy2: {strategy2}")
resolved2 = ProviderResolver.resolve_provider_for_strategy(strategy2, ResourceType.KUBERNETES_DEPLOYMENT)
print(f"Resolved K8S: {resolved2}")
