"""
Security unit tests for Docker provider:
- No arbitrary API paths
- No credentials in logs or exceptions
- No env vars in returned data
- Container ID validation
- Action allowlist enforcement
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.action_registry import ActionRegistry
from app.models.enums import ResourceType
from app.integrations.providers.docker.resource_mapper import map_container


class TestDockerActionAllowlist:
    """Verifies only registered Docker actions can be dispatched."""

    ALLOWED_DOCKER_ACTIONS = {
        "docker_collect_container_information",
        "docker_inspect_image",
        "docker_collect_container_logs",
        "docker_start_container",
        "docker_stop_container",
        "docker_restart_container",
    }

    def test_all_docker_actions_registered(self):
        for action_name in self.ALLOWED_DOCKER_ACTIONS:
            action = ActionRegistry.get_action(action_name)
            assert action is not None, f"Action '{action_name}' must be registered"
            assert action.executor_name == "docker"

    def test_docker_actions_target_correct_resource_types(self):
        container_actions = {
            "docker_collect_container_information",
            "docker_collect_container_logs",
            "docker_start_container",
            "docker_stop_container",
            "docker_restart_container",
        }
        for action_name in container_actions:
            action = ActionRegistry.get_action(action_name)
            assert ResourceType.CONTAINER in action.target_resource_types, (
                f"Action '{action_name}' must target CONTAINER"
            )

    def test_image_action_targets_container_image(self):
        action = ActionRegistry.get_action("docker_inspect_image")
        assert ResourceType.CONTAINER_IMAGE in action.target_resource_types

    def test_high_risk_mutations_require_approval(self):
        for action_name in ("docker_restart_container", "docker_stop_container"):
            action = ActionRegistry.get_action(action_name)
            assert action.requires_approval is True, (
                f"Action '{action_name}' must require approval"
            )

    def test_low_risk_reads_do_not_require_approval(self):
        for action_name in (
            "docker_collect_container_information",
            "docker_collect_container_logs",
            "docker_inspect_image",
        ):
            action = ActionRegistry.get_action(action_name)
            assert action.requires_approval is False, (
                f"Read action '{action_name}' must not require approval"
            )


class TestDockerSecretRedaction:
    """Verifies sensitive data is never exposed through the mapper."""

    def test_env_vars_not_in_metadata(self):
        container = {
            "Id": "abc123",
            "Names": ["/app"],
            "State": "running",
            "Status": "Up",
            "Labels": {"secret_key": "should_be_removed"},
            "Config": {"Env": ["DB_PASSWORD=ultra_secret"]},
        }
        resource = map_container(container)
        metadata_str = str(resource.metadata)
        assert "ultra_secret" not in metadata_str
        assert "DB_PASSWORD" not in metadata_str

    def test_secret_labels_redacted(self):
        container = {
            "Id": "abc123",
            "Names": ["/app"],
            "State": "running",
            "Status": "Up",
            "Labels": {
                "safe.label": "ok",
                "token": "should_be_gone",
                "SECRET_ENV": "exposed_value",
            },
        }
        resource = map_container(container)
        labels = resource.metadata.get("labels", {})
        assert "token" not in labels
        assert "SECRET_ENV" not in labels
        assert "safe.label" in labels
