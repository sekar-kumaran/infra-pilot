from typing import Optional, Dict, Any, List
from pydantic import BaseModel, HttpUrl

class PrometheusIntegrationConfig(BaseModel):
    base_url: str
    timeout_seconds: Optional[int] = 5
    tls_verify: Optional[bool] = True

class PrometheusAlert(BaseModel):
    labels: Dict[str, str]
    annotations: Dict[str, str]
    state: str
    activeAt: Optional[str] = None
    value: Optional[str] = None
