import requests
import logging
from typing import Dict, Any, List

from .errors import (
    PrometheusConnectionError,
    PrometheusTimeoutError,
    PrometheusAuthenticationError,
    PrometheusQueryError,
    PrometheusInvalidResponseError
)

logger = logging.getLogger(__name__)

class PrometheusClient:
    def __init__(self, base_url: str, secrets: Dict[str, Any], timeout: int = 5, tls_verify: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.tls_verify = tls_verify
        
        self.session = requests.Session()
        self.session.verify = self.tls_verify
        
        # Setup authentication
        token = secrets.get("bearer_token")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
        username = secrets.get("username")
        password = secrets.get("password")
        if username and password:
            self.session.auth = (username, password)

    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code in (401, 403):
                raise PrometheusAuthenticationError(f"Authentication failed to Prometheus ({response.status_code})")
                
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError:
                raise PrometheusInvalidResponseError("Prometheus returned malformed JSON")
                
            if data.get("status") != "success":
                error_type = data.get("errorType", "Unknown")
                error_msg = data.get("error", "Unknown error returned by Prometheus API")
                raise PrometheusQueryError(f"Prometheus API Error [{error_type}]: {error_msg}")
                
            return data.get("data", {})
            
        except requests.exceptions.Timeout:
            raise PrometheusTimeoutError(f"Timeout connecting to Prometheus ({self.timeout}s)")
        except requests.exceptions.ConnectionError:
            raise PrometheusConnectionError("Failed to connect to Prometheus")
        except requests.exceptions.HTTPError as e:
            raise PrometheusConnectionError(f"HTTP Error: {e.response.status_code}")
        except Exception as e:
            if isinstance(e, (PrometheusAuthenticationError, PrometheusTimeoutError, PrometheusConnectionError, PrometheusQueryError, PrometheusInvalidResponseError)):
                raise
            raise PrometheusConnectionError(f"Unexpected error communicating with Prometheus")

    def get_buildinfo(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/status/buildinfo")

    def get_targets(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/targets")

    def query(self, query: str) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/query", params={"query": query})

    def get_alerts(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/alerts")
