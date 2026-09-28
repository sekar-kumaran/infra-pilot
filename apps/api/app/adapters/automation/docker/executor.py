import logging
import time
from typing import Dict, Any, Tuple

from sqlalchemy.orm import Session
from app.adapters.automation.base import AutomationExecutor
from app.services.action_registry import ActionRegistry
from app.models.resource import InfrastructureResource
from app.models.integration import Integration
from app.models.enums import ProviderType, ResourceType

from app.integrations.providers.docker.client import DockerClient
from app.integrations.providers.docker.schemas import DockerIntegrationConfig, DockerIntegrationSecrets
from app.integrations.providers.docker.errors import DockerProviderError, DockerNotFoundError
from app.core.encryption import decrypt_secret_payload
from .errors import DockerExecutorError, DockerResourceNotFoundError, DockerInvalidActionError

logger = logging.getLogger(__name__)

DOCKER_READ_ACTIONS = {
    "docker_collect_container_information",
    "docker_collect_container_logs",
    "docker_inspect_image",
}

DOCKER_MUTATING_ACTIONS = {
    "docker_start_container",
    "docker_stop_container",
    "docker_restart_container",
}

ALL_DOCKER_ACTIONS = DOCKER_READ_ACTIONS | DOCKER_MUTATING_ACTIONS


class DockerAutomationExecutor(AutomationExecutor):
    """
    Real execution provider for Docker Engine operations.
    Adheres strictly to the AutomationExecutor interface.
    No mock behavior or arbitrary Docker API access is permitted.
    """

    def __init__(self, session: Session):
        self.session = session

    def _get_client_for_resource(self, resource: InfrastructureResource) -> DockerClient:
        if resource.provider != ProviderType.DOCKER.value:
            raise DockerInvalidActionError(
                f"Resource must belong to Docker provider, got: {resource.provider}"
            )

        # Find the Docker integration for this resource's environment
        integration = (
            self.session.query(Integration)
            .filter(
                Integration.provider == ProviderType.DOCKER.value,
                Integration.environment_id == resource.environment_id,
            )
            .first()
        )

        if not integration:
            raise DockerInvalidActionError(
                "No active Docker integration found for the resource environment"
            )

        cfg = DockerIntegrationConfig(**(integration.config or {}))

        secrets_dict = {}
        if integration.secrets:
            try:
                secrets_dict = decrypt_secret_payload(integration.secrets)
            except Exception as e:
                logger.warning(f"Failed to decrypt Docker secrets: {e}")

        secrets_model = DockerIntegrationSecrets(
            tls_cert=secrets_dict.get("tls_cert"),
            tls_key=secrets_dict.get("tls_key"),
            client_token=secrets_dict.get("client_token"),
        )

        return DockerClient(config=cfg, secrets=secrets_model)

    def _resolve_container_id(self, resource: InfrastructureResource) -> str:
        """Extract raw container ID from external_id: docker/container/{id}"""
        parts = resource.external_id.split("/")
        if len(parts) < 3 or parts[0] != "docker" or parts[1] != "container":
            raise DockerInvalidActionError(
                f"Invalid Docker container external_id format: {resource.external_id}"
            )
        return parts[2]

    def _resolve_image_id(self, resource: InfrastructureResource) -> str:
        parts = resource.external_id.split("/")
        if len(parts) < 3 or parts[0] != "docker" or parts[1] != "image":
            raise DockerInvalidActionError(
                f"Invalid Docker image external_id format: {resource.external_id}"
            )
        return parts[2]

    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        action_def = ActionRegistry.get_action(action_name)
        if not action_def:
            logger.error(f"Action '{action_name}' is not registered.")
            return False

        if action_def.executor_name != "docker":
            logger.error(f"Action '{action_name}' is not a Docker action.")
            return False

        if not ActionRegistry.validate_parameters(action_name, parameters):
            logger.error(f"Action '{action_name}' failed parameter schema validation.")
            return False

        resource = parameters.get("resource")
        if not resource or not isinstance(resource, InfrastructureResource):
            logger.error("Target resource is missing or is not an InfrastructureResource.")
            return False

        # Ensure resource type matches action target types
        if action_def.target_resource_types:
            resource_type_val = resource.resource_type
            target_vals = [rt.value for rt in action_def.target_resource_types]
            if resource_type_val not in target_vals:
                logger.error(
                    f"Action '{action_name}' requires resource types {target_vals}, "
                    f"but got {resource_type_val}."
                )
                return False

        return True

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        if not self.validate(action_name, parameters):
            return False, {}, f"Validation failed for Docker action '{action_name}'"

        resource: InfrastructureResource = parameters["resource"]

        try:
            client = self._get_client_for_resource(resource)

            if action_name == "docker_collect_container_information":
                container_id = self._resolve_container_id(resource)
                data = client.inspect_container(container_id)
                # Strip Config.Env before returning (may contain secrets)
                config_data = data.get("Config", {})
                config_data.pop("Env", None)
                sanitized = {k: v for k, v in data.items() if k not in ("Config",)}
                sanitized["Config"] = config_data
                return True, sanitized, ""

            elif action_name == "docker_inspect_image":
                image_id = self._resolve_image_id(resource)
                images = client.list_images()
                target = next((i for i in images if i.get("Id", "") == image_id), None)
                if not target:
                    return False, {}, f"Image {image_id} not found"
                return True, target, ""

            elif action_name == "docker_collect_container_logs":
                container_id = self._resolve_container_id(resource)
                max_lines = int(parameters.get("max_lines", 100))
                # Safety cap: max 500 lines to prevent data flooding
                max_lines = min(max_lines, 500)
                logs = client.get_container_logs(container_id, max_lines=max_lines)
                return True, {"logs": logs, "container_id": container_id}, ""

            elif action_name == "docker_start_container":
                container_id = self._resolve_container_id(resource)
                client.start_container(container_id)
                return True, {"container_id": container_id, "action": "start", "status": "start_issued"}, ""

            elif action_name == "docker_stop_container":
                container_id = self._resolve_container_id(resource)
                client.stop_container(container_id)
                return True, {"container_id": container_id, "action": "stop", "status": "stop_issued"}, ""

            elif action_name == "docker_restart_container":
                container_id = self._resolve_container_id(resource)
                client.restart_container(container_id)
                return True, {"container_id": container_id, "action": "restart", "status": "restart_issued"}, ""

            else:
                return False, {}, f"Unsupported Docker action: '{action_name}'"

        except DockerNotFoundError as e:
            logger.error(f"Docker resource not found: {e}")
            return False, {}, f"Docker resource not found: {str(e)}"
        except DockerInvalidActionError as e:
            logger.error(f"Docker action invalid: {e}")
            return False, {}, str(e)
        except DockerProviderError as e:
            logger.error(f"Docker provider error: {e}")
            return False, {}, f"Docker error: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error during Docker execution of '{action_name}'")
            return False, {}, f"Unexpected error: {str(e)}"

    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        # Docker operations are not cancellable once issued
        return False

    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        resource: InfrastructureResource = parameters.get("resource")
        if not resource:
            return False, {}, "No resource provided for Docker verification"

        try:
            container_id = self._resolve_container_id(resource)
        except DockerInvalidActionError as e:
            return False, {}, str(e)

        try:
            client = self._get_client_for_resource(resource)

            if action_name in ("docker_start_container", "docker_restart_container"):
                # Verify the container transitions to running with bounded polling
                max_attempts = 12
                delay = 3
                for attempt in range(max_attempts):
                    try:
                        data = client.inspect_container(container_id)
                        state = data.get("State", {})
                        if state.get("Running") is True:
                            return True, {"state": state.get("Status")}, "Container is running"
                    except DockerNotFoundError:
                        return False, {}, "Container not found during verification"
                    time.sleep(delay)

                return False, {"state": "unknown"}, f"Container not running after {max_attempts * delay}s"

            elif action_name == "docker_stop_container":
                max_attempts = 8
                delay = 3
                for attempt in range(max_attempts):
                    try:
                        data = client.inspect_container(container_id)
                        state = data.get("State", {})
                        if state.get("Running") is False:
                            return True, {"state": state.get("Status")}, "Container is stopped"
                    except DockerNotFoundError:
                        # Container removed after stop — also counts as stopped
                        return True, {"state": "removed"}, "Container stopped and removed"
                    time.sleep(delay)

                return False, {"state": "unknown"}, "Container did not stop within timeout"

            # For read actions, verification is not strictly required
            return True, {}, "No verification required for read actions"

        except DockerProviderError as e:
            return False, {}, f"Docker verification error: {str(e)}"
        except Exception as e:
            return False, {}, f"Unexpected verification error: {str(e)}"
