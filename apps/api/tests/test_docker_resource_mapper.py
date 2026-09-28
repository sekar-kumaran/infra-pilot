"""
Unit tests for Docker resource mapper: deterministic IDs, secret redaction, metadata safety.
"""
import pytest
from app.integrations.providers.docker.resource_mapper import (
    map_container, map_image, map_network, map_volume
)
from app.models.enums import ResourceType, ResourceStatus


INTEGRATION_ID = "test-integration-id"


class TestContainerMapper:
    def test_external_id_deterministic(self):
        container = {"Id": "abc123def456", "Names": ["/web"], "State": "running", "Status": "Up", "Labels": {}}
        resource = map_container(container)
        assert resource.external_id == "docker/container/abc123def456"
        assert resource.resource_type == ResourceType.CONTAINER
        assert resource.name == "web"

    def test_state_to_status_running(self):
        container = {"Id": "abc123", "Names": ["/web"], "State": "running", "Status": "Up", "Labels": {}}
        resource = map_container(container)
        assert resource.status == ResourceStatus.ACTIVE

    def test_state_to_status_exited(self):
        container = {"Id": "abc123", "Names": ["/web"], "State": "exited", "Status": "Exited", "Labels": {}}
        resource = map_container(container)
        assert resource.status == ResourceStatus.INACTIVE

    def test_sensitive_labels_redacted(self):
        container = {
            "Id": "abc123",
            "Names": ["/web"],
            "State": "running",
            "Status": "Up",
            "Labels": {
                "com.example.version": "1.0",
                "com.example.secret": "mysecret",
                "auth_token": "should_be_redacted"
            }
        }
        resource = map_container(container)
        labels = resource.metadata.get("labels", {})
        assert "com.example.secret" not in labels
        assert "auth_token" not in labels
        assert "com.example.version" in labels

    def test_no_env_vars_in_metadata(self):
        # Even if the raw container JSON somehow includes Config.Env,
        # the mapper never exposes it
        container = {
            "Id": "abc123",
            "Names": ["/api"],
            "State": "running",
            "Status": "Up",
            "Labels": {},
            "Config": {"Env": ["DB_PASS=supersecret", "API_KEY=12345"]}
        }
        resource = map_container(container)
        metadata_str = str(resource.metadata)
        assert "supersecret" not in metadata_str
        assert "API_KEY" not in metadata_str


class TestImageMapper:
    def test_external_id_deterministic(self):
        image = {"Id": "sha256:abc123", "RepoTags": ["nginx:latest"], "Created": 0, "Size": 1024, "Labels": {}}
        resource = map_image(image)
        assert resource.external_id == "docker/image/sha256:abc123"
        assert resource.resource_type == ResourceType.CONTAINER_IMAGE
        assert resource.name == "nginx:latest"

    def test_repository_and_tag_split(self):
        image = {"Id": "sha256:abc123", "RepoTags": ["myregistry.io/app:v2.0"], "Created": 0, "Size": 500, "Labels": {}}
        resource = map_image(image)
        assert resource.metadata["repository"] == "myregistry.io/app"
        assert resource.metadata["tag"] == "v2.0"


class TestNetworkMapper:
    def test_external_id_deterministic(self):
        network = {"Id": "net001", "Name": "bridge", "Driver": "bridge", "Scope": "local", "Containers": {}, "Labels": {}}
        resource = map_network(network)
        assert resource.external_id == "docker/network/net001"
        assert resource.resource_type == ResourceType.CONTAINER_NETWORK
        assert resource.metadata["driver"] == "bridge"


class TestVolumeMapper:
    def test_external_id_deterministic(self):
        volume = {"Name": "myvolume", "Driver": "local", "Mountpoint": "/var/lib/docker/volumes/myvolume/_data", "Scope": "local", "Labels": {}}
        resource = map_volume(volume)
        assert resource.external_id == "docker/volume/myvolume"
        assert resource.resource_type == ResourceType.CONTAINER_VOLUME
        assert resource.metadata["driver"] == "local"
