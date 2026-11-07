from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional

class KubernetesConfigSchema(BaseModel):
    base_url: str = Field(..., description="The Kubernetes API server base URL")
    bearer_token: Optional[str] = Field(None, description="The bearer token for authentication")
    verify_tls: bool = Field(True, description="Whether to verify TLS certificates")
    ca_certificate: Optional[str] = Field(None, description="Optional custom CA certificate content")

    @field_validator("base_url")
    def validate_url(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v
