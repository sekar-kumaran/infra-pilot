import logging
from typing import Dict, Any, List, Optional

from app.models.enums import ResourceType, ResourceStatus, ProviderType
from app.integrations.models import DiscoveredResource

logger = logging.getLogger(__name__)

_SENSITIVE_LABEL_TERMS = ("secret", "token", "password", "passwd", "key", "credential", "auth")


def _redact_labels(labels: Dict[str, str]) -> Dict[str, str]:
    """Remove labels whose keys hint at containing secrets."""
    return {
        k: v for k, v in labels.items()
        if not any(term in k.lower() for term in _SENSITIVE_LABEL_TERMS)
    }


def map_container(container: Dict[str, Any], parent_id: Optional[str] = None) -> DiscoveredResource:
    container_id = container.get("Id", "")
    names = container.get("Names", [])
    name = names[0].lstrip('/') if names else container_id[:12]

    state_raw = container.get("State", "")
    state_str = state_raw if isinstance(state_raw, str) else ""

    res_status = ResourceStatus.UNKNOWN
    if state_str == "running":
        res_status = ResourceStatus.ACTIVE
    elif state_str in ("exited", "stopped"):
        res_status = ResourceStatus.INACTIVE
    elif state_str in ("dead", "created"):
        res_status = ResourceStatus.DEGRADED

    labels = container.get("Labels") or {}
    safe_labels = _redact_labels(labels)

    metadata: Dict[str, Any] = {
        "image": container.get("Image"),
        "image_id": container.get("ImageID"),
        "state": state_str,
        "status": container.get("Status"),
        "created_at": container.get("Created"),
        "ports": container.get("Ports", []),
        "labels": safe_labels,
        "restart_count": container.get("RestartCount", 0),
    }

    # Handle inspect-style response (State is a dict)
    if isinstance(container.get("State"), dict):
        state_dict = container["State"]
        metadata["state"] = state_dict.get("Status")
        if state_dict.get("Running"):
            res_status = ResourceStatus.ACTIVE
        else:
            res_status = ResourceStatus.INACTIVE

        health = state_dict.get("Health")
        if health:
            metadata["health_status"] = health.get("Status")
            if health.get("Status") == "unhealthy":
                res_status = ResourceStatus.DEGRADED
        # Config.Env deliberately NOT included

    return DiscoveredResource(
        provider=ProviderType.DOCKER,
        external_id=f"docker/container/{container_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CONTAINER,
        status=res_status,
        metadata=metadata,
        parent_external_id=parent_id
    )


def map_image(image: Dict[str, Any], parent_id: Optional[str] = None) -> DiscoveredResource:
    image_id = image.get("Id", "")
    repo_tags = image.get("RepoTags") or []
    name = repo_tags[0] if repo_tags else image_id[:20]

    repository = None
    tag = None
    if repo_tags and ':' in name:
        parts = name.rsplit(':', 1)
        repository = parts[0]
        tag = parts[1]

    metadata = {
        "repository": repository,
        "tag": tag,
        "image_id": image_id,
        "created_at": image.get("Created"),
        "size": image.get("Size"),
        "labels": _redact_labels(image.get("Labels") or {}),
    }

    return DiscoveredResource(
        provider=ProviderType.DOCKER,
        external_id=f"docker/image/{image_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CONTAINER_IMAGE,
        status=ResourceStatus.ACTIVE,
        metadata=metadata,
        parent_external_id=parent_id
    )


def map_network(network: Dict[str, Any], parent_id: Optional[str] = None) -> DiscoveredResource:
    network_id = network.get("Id", "")
    name = network.get("Name", network_id[:12])

    metadata = {
        "driver": network.get("Driver"),
        "scope": network.get("Scope"),
        "container_count": len(network.get("Containers") or {}),
        "labels": _redact_labels(network.get("Labels") or {}),
    }

    return DiscoveredResource(
        provider=ProviderType.DOCKER,
        external_id=f"docker/network/{network_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CONTAINER_NETWORK,
        status=ResourceStatus.ACTIVE,
        metadata=metadata,
        parent_external_id=parent_id
    )


def map_volume(volume: Dict[str, Any], parent_id: Optional[str] = None) -> DiscoveredResource:
    name = volume.get("Name", "")

    metadata = {
        "driver": volume.get("Driver"),
        "mountpoint": volume.get("Mountpoint"),
        "scope": volume.get("Scope"),
        "labels": _redact_labels(volume.get("Labels") or {}),
    }

    return DiscoveredResource(
        provider=ProviderType.DOCKER,
        external_id=f"docker/volume/{name}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CONTAINER_VOLUME,
        status=ResourceStatus.ACTIVE,
        metadata=metadata,
        parent_external_id=parent_id
    )
