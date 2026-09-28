import logging
from typing import Dict, Any, List

from app.models.enums import ProviderType, ResourceType
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.exceptions import ProviderError

from .client import TerraformClient
from .schemas import TerraformIntegrationConfig, TerraformIntegrationSecrets
from .resource_mapper import map_workspace

logger = logging.getLogger(__name__)


class TerraformIntegrationAdapter(ProviderAdapter):
    """
    Adapter for Terraform Cloud / Terraform Enterprise.
    Discovers workspaces and their current run states.
    """

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.TERRAFORM

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
            provider=ProviderType.TERRAFORM,
            display_name="Terraform Cloud",
            version="TFC API v2",
            capabilities=[
                "health_check",
                "resource_discovery",
                "resource_read",
                "workspace_management",
                "run_trigger",
                "state_read",
            ],
            resources=[ResourceType.SERVICE],
            read_operations=["terraform_get_workspace", "terraform_list_runs", "terraform_get_outputs"],
            mutation_operations=["terraform_trigger_run"],
            authentication_requirements=["api_token"]
        )

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> TerraformClient:
        cfg = TerraformIntegrationConfig(**config)
        sec = TerraformIntegrationSecrets(api_token=secrets.get("api_token"))
        if not sec.api_token:
            raise ProviderError("Terraform API token is required")
        return TerraformClient(
            base_url=cfg.base_url,
            api_token=sec.api_token,
            organization=cfg.organization
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            client = self._get_client(config, secrets)
            healthy = client.check_health()
            if not healthy:
                raise ProviderError("Terraform API did not respond to account details check")
            logger.info("Terraform API health check passed")
            return True
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"Terraform connection error: {str(e)}")

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        resources = []

        cfg = TerraformIntegrationConfig(**config)
        organizations = []

        if cfg.organization:
            organizations = [cfg.organization]
        else:
            orgs_data = client.list_organizations()
            organizations = [o.get("attributes", {}).get("name") for o in orgs_data if o.get("attributes", {}).get("name")]

        for org in organizations:
            workspaces = client.list_workspaces(org)
            for ws in workspaces:
                try:
                    resources.append(map_workspace(ws, org))
                except Exception as e:
                    logger.warning(f"Failed to map workspace: {e}")

        logger.info(f"Discovered {len(resources)} Terraform workspaces across {len(organizations)} organizations")
        return resources
