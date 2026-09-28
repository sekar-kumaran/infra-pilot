from pydantic import BaseModel
from typing import Optional


class TerraformIntegrationConfig(BaseModel):
    """Configuration for a Terraform Cloud / Terraform Enterprise integration."""
    base_url: str = "https://app.terraform.io"  # Override for TFE
    organization: Optional[str] = None


class TerraformIntegrationSecrets(BaseModel):
    api_token: Optional[str] = None
