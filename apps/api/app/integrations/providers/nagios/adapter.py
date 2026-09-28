import logging
from typing import Dict, Any, List

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.exceptions import ProviderError

from .client import NagiosClient
from .schemas import NagiosIntegrationConfig

logger = logging.getLogger(__name__)

class NagiosAdapter(ProviderAdapter):
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.NAGIOS
        
    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=False,
            logs_read=False,
            alerts_read=True,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.NAGIOS,
            display_name="Nagios",
            version="1.0",
            capabilities=["health_check", "alerts_read", "resource_discovery"],
            resources=[ResourceType.HOST, ResourceType.SERVICE],
            read_operations=[],
            mutation_operations=[],
            authentication_requirements=["base_url", "username", "password"]
        )

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> NagiosClient:
        cfg = NagiosIntegrationConfig(**config)
        return NagiosClient(
            base_url=cfg.base_url,
            status_endpoint=cfg.status_endpoint,
            timeout=cfg.timeout_seconds,
            tls_verify=cfg.tls_verify,
            secrets=secrets
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            client = self._get_client(config, secrets)
            # The client fetches status and parses it. 
            # If it succeeds and returns the tuple of lists, validation is successful.
            # We don't demand any hosts or services exist.
            client.get_status()
            return True
        except ProviderError as e:
            logger.error(f"Nagios validation failed: {str(e)}")
            raise

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        hosts, services = client.get_status()
        
        resources = []
        
        for host in hosts:
            if not host.host_name:
                continue
                
            external_id = f"nagios/host/{host.host_name}"
            status = ResourceStatus.ACTIVE if host.current_state == 0 else ResourceStatus.FAILED
            if host.current_state not in (0, 1, 2):
                status = ResourceStatus.UNKNOWN
                
            metadata = {
                "provider": "nagios",
                "entity_type": "host",
                "host_name": host.host_name,
                "state": host.current_state,
                "plugin_output": host.plugin_output,
                "acknowledged": bool(host.problem_has_been_acknowledged),
                "notifications_enabled": bool(host.notifications_enabled)
            }
            
            resources.append(
                DiscoveredResource(
                    provider=ProviderType.NAGIOS,
                    external_id=external_id,
                    name=host.host_name,
                    display_name=host.host_name,
                    resource_type=ResourceType.HOST,
                    status=status,
                    description=f"Nagios host {host.host_name}",
                    metadata=metadata
                )
            )
            
        for service in services:
            if not service.host_name or not service.service_description:
                continue
                
            external_id = f"nagios/service/{service.host_name}/{service.service_description}"
            status = ResourceStatus.ACTIVE if service.current_state == 0 else ResourceStatus.FAILED
            if service.current_state == 3:
                status = ResourceStatus.UNKNOWN
                
            metadata = {
                "provider": "nagios",
                "entity_type": "service",
                "host_name": service.host_name,
                "service_description": service.service_description,
                "state": service.current_state,
                "plugin_output": service.plugin_output,
                "acknowledged": bool(service.problem_has_been_acknowledged),
                "notifications_enabled": bool(service.notifications_enabled)
            }
            
            resources.append(
                DiscoveredResource(
                    provider=ProviderType.NAGIOS,
                    external_id=external_id,
                    name=f"{service.host_name}-{service.service_description}",
                    display_name=service.service_description,
                    resource_type=ResourceType.SERVICE,
                    status=status,
                    description=f"Nagios service {service.service_description} on {service.host_name}",
                    metadata=metadata
                )
            )

        return resources
