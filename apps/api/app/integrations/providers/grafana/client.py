import httpx
import logging
from typing import Dict, Any, List, Optional
from app.integrations.providers.exceptions import (
    ProviderAuthenticationError, 
    ProviderUnavailableError,
    ProviderTimeoutError,
    ProviderExecutionException
)

logger = logging.getLogger(__name__)

class GrafanaClient:
    def __init__(self, url: str, token: str, verify_tls: bool = True, timeout: int = 10):
        self.url = url.rstrip('/')
        self.token = token
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        full_url = f"{self.url}/api/{path.lstrip('/')}"
        
        try:
            with httpx.Client(verify=self.verify_tls, timeout=self.timeout) as client:
                response = client.request(method, full_url, headers=self.headers, params=params)
                
                if response.status_code in [401, 403]:
                    raise ProviderAuthenticationError("Grafana authentication failed (401/403)")
                    
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Grafana request timed out: {str(e)}")
        except httpx.RequestError as e:
            raise ProviderUnavailableError(f"Grafana connection failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ProviderExecutionException(f"Grafana HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            if isinstance(e, ProviderExecutionException):
                raise
            raise ProviderExecutionException(f"Grafana client error: {str(e)}")

    def health_check(self) -> bool:
        try:
            res = self._request("GET", "/health")
            return res.get("database") == "ok"
        except Exception as e:
            logger.error(f"Grafana health check failed: {str(e)}")
            return False

    def list_dashboards(self) -> List[Dict[str, Any]]:
        # Grafana Search API
        res = self._request("GET", "/search", params={"type": "dash-db"})
        return res if isinstance(res, list) else []

    def list_folders(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "/search", params={"type": "dash-folder"})
        return res if isinstance(res, list) else []
        
    def list_alert_rules(self) -> List[Dict[str, Any]]:
        # Grafana 8+ alerting provisioning API
        try:
            return self._request("GET", "/v1/provisioning/alert-rules")
        except Exception as e:
            logger.warning(f"Failed to list alert rules (possibly not Grafana 8+): {str(e)}")
            return []

    def list_datasources(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "/datasources")
        if not isinstance(res, list):
            return []
            
        safe_datasources = []
        for ds in res:
            safe_ds = {
                "id": ds.get("id"),
                "uid": ds.get("uid"),
                "name": ds.get("name"),
                "type": ds.get("type"),
                "url": ds.get("url"),
                "access": ds.get("access"),
                "isDefault": ds.get("isDefault"),
            }
            safe_datasources.append(safe_ds)
            
        return safe_datasources
