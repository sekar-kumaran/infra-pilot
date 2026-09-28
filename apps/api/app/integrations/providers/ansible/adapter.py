from typing import Dict, Any, List
import logging
import httpx

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.providers.exceptions import ProviderUnavailableError, ProviderExecutionException

logger = logging.getLogger(__name__)

class AnsibleAdapter(ProviderAdapter):
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANSIBLE
        
    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=False,
            logs_read=False,
            alerts_read=False,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.ANSIBLE,
            display_name="Ansible",
            version="1.0",
            capabilities=[
                "configuration_management", "service_management",
                "container_management", "system_information", "automation"
            ],
            resources=[
                ResourceType.HOST, ResourceType.VM, ResourceType.CONTAINER, ResourceType.SERVICE
            ],
            read_operations=[
                "collect_system_information", "check_disk_usage", "check_memory_usage", "check_cpu_usage", "check_service", "inspect_docker_container"
            ],
            mutation_operations=[
                "restart_service", "start_service", "stop_service",
                "restart_docker_container", "start_docker_container", "stop_docker_container",
                "validate_configuration", "deploy_configuration", "rollback_configuration"
            ],
            authentication_requirements=["inventory_url"]
        )

    def _get_runner_url(self, config: Dict[str, Any]) -> str:
        """Get the base URL for the Ansible runner API."""
        url = config.get("inventory_url") or config.get("base_url") or config.get("url")
        if not url:
            raise ProviderExecutionException("Ansible runner URL is required in configuration (inventory_url or base_url)")
        return url.rstrip("/")

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        """Validate by hitting the Ansible runner /health endpoint."""
        try:
            url = self._get_runner_url(config)
            with httpx.Client(timeout=10, verify=False) as client:
                response = client.get(f"{url}/health")
                response.raise_for_status()
                data = response.json()
                return data.get("status") == "ok"
        except Exception as e:
            logger.error(f"Ansible runner health check failed: {str(e)}")
            return False

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        """Discover hosts from the Ansible runner inventory."""
        try:
            url = self._get_runner_url(config)
            with httpx.Client(timeout=10, verify=False) as client:
                response = client.get(f"{url}/api/v1/inventory")
                response.raise_for_status()
                data = response.json()
                
            resources = []
            for host in data.get("hosts", []):
                resources.append(DiscoveredResource(
                    name=host.get("name"),
                    resource_type=ResourceType.HOST,
                    external_id=f"ansible/host/{host.get('name')}",
                    provider=ProviderType.ANSIBLE,
                    metadata={
                        "address": host.get("address"),
                        "groups": host.get("groups", [])
                    },
                    status=ResourceStatus.ACTIVE
                ))
            return resources
        except Exception as e:
            logger.error(f"Ansible inventory discovery failed: {str(e)}")
            return []
