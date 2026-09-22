from typing import Dict, Type, List
import logging

from app.models.enums import ProviderType
from app.integrations.adapter import ProviderAdapter
from app.integrations.exceptions import ProviderNotFoundError, ProviderConfigurationError

logger = logging.getLogger(__name__)

class AdapterRegistry:
    _adapters: Dict[ProviderType, Type[ProviderAdapter]] = {}

    @classmethod
    def register(cls, adapter_class: Type[ProviderAdapter]) -> None:
        """Register a new provider adapter."""
        # Instantiate temporarily just to get the provider type cleanly
        # assuming adapters have a no-arg constructor or we use class property
        # For simplicity, we assume `provider_type` can be accessed or we instantiate it
        try:
            instance = adapter_class()
            provider_type = instance.provider_type
            if provider_type in cls._adapters:
                logger.warning(f"Provider {provider_type} is already registered. Overwriting.")
            cls._adapters[provider_type] = adapter_class
            logger.info(f"Registered integration adapter for {provider_type}")
        except Exception as e:
            raise ProviderConfigurationError(f"Failed to register adapter {adapter_class.__name__}: {str(e)}")

    @classmethod
    def get_adapter(cls, provider: ProviderType) -> ProviderAdapter:
        """Get an instance of the provider adapter."""
        adapter_class = cls._adapters.get(provider)
        if not adapter_class:
            raise ProviderNotFoundError(f"Provider adapter not found for {provider}")
        return adapter_class()

    @classmethod
    def get_registered_providers(cls) -> List[ProviderType]:
        return list(cls._adapters.keys())
