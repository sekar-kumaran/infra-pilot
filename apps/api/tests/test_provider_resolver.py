import pytest
from app.services.provider_resolver import ProviderResolver
from app.services.remediation_registry import RemediationRegistry
from app.models.enums import ResourceType, ProviderType
from app.integrations.registry import AdapterRegistry
from app.integrations.providers.aws.adapter import AWSAdapter
from app.integrations.providers.kubernetes.adapter import KubernetesProviderAdapter

AdapterRegistry.register(AWSAdapter)
AdapterRegistry.register(KubernetesProviderAdapter)

def test_resolve_provider_for_kubernetes():
    strategy = RemediationRegistry.get_strategy("restart_deployment")
    resolved = ProviderResolver.resolve_provider_for_strategy(strategy, ResourceType.KUBERNETES_DEPLOYMENT)
    
    assert resolved is not None
    assert resolved.provider == ProviderType.KUBERNETES
    assert resolved.action == "kubernetes_restart_deployment"

def test_resolve_provider_for_aws():
    strategy = RemediationRegistry.get_strategy("restart_instance")
    resolved = ProviderResolver.resolve_provider_for_strategy(strategy, ResourceType.CLOUD_INSTANCE)
    
    assert resolved is not None
    assert resolved.provider == ProviderType.AWS
    # It should pick one of the allowed actions based on availability (usually the first one in the list that exists)
    assert resolved.action in ["aws_reboot_instance", "aws_start_instance"]

def test_resolve_provider_unsupported_resource():
    strategy = RemediationRegistry.get_strategy("restart_instance")
    # Even though restart_instance is valid for AWS, providing a KUBERNETES_POD target type should fail
    resolved = ProviderResolver.resolve_provider_for_strategy(strategy, ResourceType.KUBERNETES_POD)
    
    assert resolved is None
