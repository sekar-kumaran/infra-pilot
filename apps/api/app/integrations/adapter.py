from abc import ABC, abstractmethod
from typing import Dict, Any, List

from app.models.enums import ProviderType
from app.integrations.models import IntegrationCapability, DiscoveredResource

class ProviderAdapter(ABC):
    """
    Base contract for all external provider integrations.
    """
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type this adapter implements."""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> IntegrationCapability:
        """Return the capabilities supported by this provider."""
        pass

    @abstractmethod
    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        """
        Validates the connection using the provided configuration and secrets.
        Raises appropriate ProviderError exceptions on failure.
        """
        pass

    @abstractmethod
    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        """
        Discovers resources from the provider and returns them in the canonical format.
        """
        pass
