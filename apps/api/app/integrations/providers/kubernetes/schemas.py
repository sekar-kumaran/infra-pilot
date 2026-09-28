from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class KubernetesConfigSchema(BaseModel):
    base_url: str = Field(..., description="The Kubernetes API server base URL")
    bearer_token: Optional[str] = Field(None, description="The bearer token for authentication")
    verify_tls: bool = Field(True, description="Whether to verify TLS certificates")
    ca_certificate: Optional[str] = Field(None, description="Optional custom CA certificate content")
