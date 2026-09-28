from app.integrations.registry import AdapterRegistry
from app.integrations.capabilities import ProviderCapabilityRegistry, ProviderCapabilityRegistryEntry
from app.integrations.providers.docker.adapter import DockerIntegrationAdapter
from app.models.enums import ProviderType, ResourceType

def register_provider():
    AdapterRegistry.register(DockerIntegrationAdapter)
    
    # Register capabilities explicitly
    ProviderCapabilityRegistry.register(ProviderCapabilityRegistryEntry(
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
            ResourceType.CONTAINER_VOLUME
        ],
        read_operations=[
            "list_containers",
            "inspect_container",
            "list_images",
            "inspect_image",
            "list_networks",
            "inspect_network",
            "list_volumes",
            "inspect_volume",
            "get_container_logs"
        ],
        mutation_operations=[
            "start_container",
            "stop_container",
            "restart_container"
        ],
        authentication_requirements=["tls_cert", "tls_key", "client_token"]
    ))
