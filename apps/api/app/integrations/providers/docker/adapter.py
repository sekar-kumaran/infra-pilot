import logging
from typing import Dict, Any, List, Optional

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.exceptions import ProviderError

from .client import DockerClient
from .schemas import DockerIntegrationConfig, DockerIntegrationSecrets
from .errors import DockerConnectionError, DockerAuthenticationError, DockerAPIError, DockerProviderError
from .resource_mapper import map_container, map_image, map_network, map_volume

logger = logging.getLogger(__name__)


class DockerIntegrationAdapter(ProviderAdapter):

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.DOCKER

    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=False,
            logs_read=True,
            alerts_read=False,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.DOCKER,
            display_name="Docker Engine",
            version="API v1.43+",
            capabilities=[
                "health_check",
                "resource_discovery",
                "resource_read",
                "container_management",
                "container_start",
                "container_stop",
                "container_restart",
                "container_logs",
                "image_read",
                "network_read",
                "volume_read"
            ],
            resources=[
                ResourceType.CONTAINER,
                ResourceType.CONTAINER_IMAGE,
                ResourceType.CONTAINER_NETWORK,
                ResourceType.CONTAINER_VOLUME,
            ],
            read_operations=[
                "docker_collect_container_information",
                "docker_inspect_image",
                "docker_collect_container_logs",
            ],
            mutation_operations=[
                "docker_start_container",
                "docker_stop_container",
                "docker_restart_container",
            ],
            authentication_requirements=["tls_cert", "tls_key", "client_token"]
        )

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> DockerClient:
        cfg = DockerIntegrationConfig(**config)
        secrets_model = DockerIntegrationSecrets(
            tls_cert=secrets.get("tls_cert"),
            tls_key=secrets.get("tls_key"),
            client_token=secrets.get("client_token")
        )
        return DockerClient(config=cfg, secrets=secrets_model)

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            client = self._get_client(config, secrets)
            healthy = client.check_health()
            if not healthy:
                raise ProviderError("Docker API did not return OK on health check")
            logger.info("Docker API health check passed")
            return True
        except DockerAuthenticationError as e:
            raise ProviderError(f"Docker authentication failed: {str(e)}")
        except DockerConnectionError as e:
            raise ProviderError(f"Cannot connect to Docker API: {str(e)}")
        except DockerProviderError as e:
            raise ProviderError(f"Docker validation error: {str(e)}")

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        resources = []

        # Use the integration name as a placeholder for engine_external_id
        # In practice, integration_id is provided during sync via IntegrationService
        engine_external_id = None  # parent will be resolved by integration service

        # Containers
        try:
            containers = client.list_containers(all_containers=True)
            for c in containers:
                resources.append(map_container(c, parent_id=engine_external_id))
        except DockerProviderError as e:
            logger.warning(f"Docker container discovery failed: {e}")

        # Images
        try:
            images = client.list_images()
            for i in images:
                resources.append(map_image(i, parent_id=engine_external_id))
        except DockerProviderError as e:
            logger.warning(f"Docker image discovery failed: {e}")

        # Networks
        try:
            networks = client.list_networks()
            for n in networks:
                resources.append(map_network(n, parent_id=engine_external_id))
        except DockerProviderError as e:
            logger.warning(f"Docker network discovery failed: {e}")

        # Volumes
        try:
            volumes_res = client.list_volumes()
            volumes = volumes_res.get("Volumes", []) if isinstance(volumes_res, dict) else []
            for v in volumes:
                resources.append(map_volume(v, parent_id=engine_external_id))
        except DockerProviderError as e:
            logger.warning(f"Docker volume discovery failed: {e}")

        return resources
