from typing import Dict, Any, List
import logging

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.exceptions import ProviderValidationError

logger = logging.getLogger(__name__)

class TestProviderAdapter(ProviderAdapter):
    """
    DETERMINISTIC TEST ADAPTER.
    This adapter is used strictly for internal framework and E2E testing.
    It does not connect to any external infrastructure.
    """
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.TEST_PROVIDER

    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            health_check=True
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        # Deterministic validation logic
        # For testing, we require config to have 'test_mode' = True
        # and secrets to have 'test_token' = 'valid'
        
        test_mode = config.get("test_mode")
        if not test_mode:
            raise ProviderValidationError("Configuration must include 'test_mode': true")
            
        test_token = secrets.get("test_token")
        if test_token == "invalid":
            raise ProviderValidationError("Invalid test token provided")
            
        return True

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        """
        Returns a deterministic list of fake resources.
        """
        self.validate_connection(config, secrets)
        
        resources = [
            DiscoveredResource(
                provider=self.provider_type,
                external_id="test-host-01",
                name="test-web-server",
                display_name="Test Web Server",
                resource_type=ResourceType.HOST,
                status=ResourceStatus.ACTIVE,
                description="Deterministic test host",
                metadata={"os": "linux", "cores": 4}
            ),
            DiscoveredResource(
                provider=self.provider_type,
                external_id="test-db-01",
                name="test-database",
                display_name="Test Database",
                resource_type=ResourceType.DATABASE,
                status=ResourceStatus.ACTIVE,
                description="Deterministic test database",
                metadata={"engine": "postgres"}
            )
        ]
        return resources
