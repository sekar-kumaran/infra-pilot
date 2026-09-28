from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.exceptions import (
    ProviderError,
    ProviderConfigurationError,
    ProviderAuthenticationError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
    ProviderDiscoveryError,
    ProviderUnsupportedOperationError,
    ProviderNotFoundError
)
from app.integrations.adapter import ProviderAdapter
from app.integrations.registry import AdapterRegistry

from app.integrations.providers.test_provider import TestProviderAdapter
from app.integrations.providers.prometheus.adapter import PrometheusAdapter
from app.integrations.providers.nagios.adapter import NagiosAdapter
from app.integrations.providers.kubernetes.adapter import KubernetesProviderAdapter
from app.integrations.providers.ansible.adapter import AnsibleAdapter
from app.integrations.providers.docker.adapter import DockerIntegrationAdapter
from app.integrations.providers.aws.adapter import AWSAdapter
from app.integrations.providers.grafana.adapter import GrafanaAdapter

AdapterRegistry.register(TestProviderAdapter)
AdapterRegistry.register(PrometheusAdapter)
AdapterRegistry.register(NagiosAdapter)
AdapterRegistry.register(KubernetesProviderAdapter)
AdapterRegistry.register(AnsibleAdapter)
AdapterRegistry.register(DockerIntegrationAdapter)
AdapterRegistry.register(AWSAdapter)
AdapterRegistry.register(GrafanaAdapter)

__all__ = [
    "IntegrationCapability",
    "DiscoveredResource",
    "ProviderError",
    "ProviderConfigurationError",
    "ProviderAuthenticationError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "ProviderValidationError",
    "ProviderDiscoveryError",
    "ProviderUnsupportedOperationError",
    "ProviderNotFoundError",
    "ProviderAdapter",
    "AdapterRegistry"
]
