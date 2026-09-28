import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TerraformClient:
    """
    HTTP client for Terraform Cloud / Terraform Enterprise API.
    Docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
    """

    def __init__(self, base_url: str, api_token: str, organization: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.organization = organization
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/vnd.api+json",
        })

    def _get(self, path: str, params: Dict = None) -> Dict:
        url = f"{self.base_url}/api/v2{path}"
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def check_health(self) -> bool:
        """Verify the API token works by fetching the account info."""
        try:
            self._get("/account/details")
            return True
        except Exception as e:
            logger.warning(f"Terraform health check failed: {e}")
            return False

    def list_organizations(self) -> List[Dict]:
        """List all accessible organizations."""
        try:
            data = self._get("/organizations")
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to list organizations: {e}")
            return []

    def list_workspaces(self, organization: str) -> List[Dict]:
        """List all workspaces in an organization."""
        try:
            data = self._get(f"/organizations/{organization}/workspaces", params={"page[size]": 100})
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to list workspaces for {organization}: {e}")
            return []

    def get_workspace(self, organization: str, workspace_name: str) -> Optional[Dict]:
        """Get a single workspace."""
        try:
            data = self._get(f"/organizations/{organization}/workspaces/{workspace_name}")
            return data.get("data")
        except Exception:
            return None

    def list_runs(self, workspace_id: str) -> List[Dict]:
        """List recent runs for a workspace."""
        try:
            data = self._get(f"/workspaces/{workspace_id}/runs", params={"page[size]": 10})
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to list runs for {workspace_id}: {e}")
            return []

    def get_state_outputs(self, workspace_id: str) -> List[Dict]:
        """Get current Terraform state outputs for a workspace."""
        try:
            data = self._get(f"/workspaces/{workspace_id}/current-state-version-outputs")
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to get state outputs for {workspace_id}: {e}")
            return []

    def trigger_run(self, workspace_id: str, message: str = "Triggered via InfraPilot") -> Optional[str]:
        """Trigger a new Terraform plan+apply run."""
        try:
            payload = {
                "data": {
                    "type": "runs",
                    "attributes": {"message": message, "auto-apply": True},
                    "relationships": {
                        "workspace": {"data": {"type": "workspaces", "id": workspace_id}}
                    }
                }
            }
            resp = self.session.post(f"{self.base_url}/api/v2/runs", json=payload, timeout=15)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("id")
        except Exception as e:
            logger.error(f"Failed to trigger run: {e}")
            return None
