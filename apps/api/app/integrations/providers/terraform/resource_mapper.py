from typing import Dict, Any
from app.integrations.models import DiscoveredResource
from app.models.enums import ResourceType, ResourceStatus


def map_workspace(ws: Dict[str, Any], organization: str) -> DiscoveredResource:
    """Map a Terraform Cloud workspace to a DiscoveredResource."""
    attrs = ws.get("attributes", {})
    ws_id = ws.get("id", "")
    ws_name = attrs.get("name", ws_id)
    run_status = attrs.get("latest-run-status") or "unknown"
    locked = attrs.get("locked", False)

    status = ResourceStatus.ACTIVE
    if run_status in ("errored", "canceled", "discarded"):
        status = ResourceStatus.FAILED
    elif locked:
        status = ResourceStatus.DEGRADED

    return DiscoveredResource(
        name=ws_name,
        display_name=f"{organization}/{ws_name}",
        resource_type=ResourceType.SERVICE,
        provider="terraform",
        external_id=f"terraform/workspace/{ws_id}",
        status=status,
        metadata={
            "organization": organization,
            "workspace_id": ws_id,
            "workspace_name": ws_name,
            "terraform_version": attrs.get("terraform-version"),
            "auto_apply": attrs.get("auto-apply", False),
            "latest_run_status": run_status,
            "resource_count": attrs.get("resource-count", 0),
            "updated_at": attrs.get("latest-change-at"),
            "vcs_repo": (attrs.get("vcs-repo") or {}).get("identifier"),
            "description": attrs.get("description"),
            "environment": attrs.get("environment"),
        }
    )
