from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List

class DockerIntegrationConfig(BaseModel):
    base_url: str = "http://localhost:2375"
    verify_tls: bool = False
    timeout_seconds: int = 10

class DockerIntegrationSecrets(BaseModel):
    # Depending on auth, might be certs or token. We will just support basic/empty for now
    tls_cert: Optional[str] = None
    tls_key: Optional[str] = None
    client_token: Optional[str] = None
