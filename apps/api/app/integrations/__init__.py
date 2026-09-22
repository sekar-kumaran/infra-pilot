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

AdapterRegistry.register(TestProviderAdapter)

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
