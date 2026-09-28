import requests
import json
import logging
from typing import Dict, Any, List, Optional
from requests.exceptions import Timeout, ConnectionError, RequestException

from app.integrations.providers.docker.errors import (
    DockerConnectionError,
    DockerAuthenticationError,
    DockerNotFoundError,
    DockerAPIError,
    DockerTimeoutError
)
from app.integrations.providers.docker.schemas import DockerIntegrationConfig, DockerIntegrationSecrets

logger = logging.getLogger(__name__)

class DockerClient:
    """REST Client for Docker Engine API."""
    def __init__(self, config: DockerIntegrationConfig, secrets: Optional[DockerIntegrationSecrets] = None):
        self.base_url = config.base_url.rstrip('/')
        self.timeout = config.timeout_seconds
        
        self.session = requests.Session()
        self.session.verify = config.verify_tls
        
        if secrets:
            if secrets.tls_cert and secrets.tls_key:
                # We would typically write these to a tempfile if using requests, 
                # or pass if already paths. For now, assume we just use the token if any.
                pass
            if secrets.client_token:
                self.session.headers.update({"Authorization": f"Bearer {secrets.client_token}"})
                
    def _handle_response(self, response: requests.Response, is_text: bool = False) -> Any:
        if response.status_code == 401 or response.status_code == 403:
            raise DockerAuthenticationError(f"Authentication/Authorization failed: {response.text}")
        elif response.status_code == 404:
            raise DockerNotFoundError(f"Resource not found: {response.text}")
        elif not (200 <= response.status_code < 300):
            raise DockerAPIError(f"Docker API error {response.status_code}: {response.text}")

        if is_text:
            return response.text

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or response.text.strip().startswith(("{", "[")):
            try:
                return response.json()
            except Exception:
                pass
        return response.text

    def _get(self, path: str, params: Optional[Dict] = None, is_text: bool = False) -> Any:
        url = f"{self.base_url}{path}"
        try:
            res = self.session.get(url, params=params, timeout=self.timeout)
            return self._handle_response(res, is_text=is_text)
        except Timeout:
            raise DockerTimeoutError(f"Request to {url} timed out")
        except ConnectionError as e:
            raise DockerConnectionError(f"Failed to connect to Docker API: {str(e)}")
        except (DockerAuthenticationError, DockerNotFoundError, DockerAPIError, DockerTimeoutError, DockerConnectionError):
            raise
        except RequestException as e:
            raise DockerAPIError(f"Request failed: {str(e)}")

    def _post(self, path: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            res = self.session.post(url, json=json_data, params=params, timeout=self.timeout)
            return self._handle_response(res)
        except Timeout:
            raise DockerTimeoutError(f"Request to {url} timed out")
        except ConnectionError as e:
            raise DockerConnectionError(f"Failed to connect to Docker API: {str(e)}")
        except (DockerAuthenticationError, DockerNotFoundError, DockerAPIError, DockerTimeoutError, DockerConnectionError):
            raise
        except RequestException as e:
            raise DockerAPIError(f"Request failed: {str(e)}")

    def check_health(self) -> bool:
        try:
            res = self._get("/_ping", is_text=True)
            return "OK" in str(res)
        except Exception as e:
            logger.warning(f"Docker health check failed: {e}")
            return False
            
    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        return self._get("/containers/json", params={"all": all_containers})
        
    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        return self._get(f"/containers/{container_id}/json")
        
    def list_images(self) -> List[Dict[str, Any]]:
        return self._get("/images/json")
        
    def list_networks(self) -> List[Dict[str, Any]]:
        return self._get("/networks")
        
    def list_volumes(self) -> Dict[str, Any]:
        # returns {"Volumes": [], "Warnings": []}
        return self._get("/volumes")

    # Mutations
    
    def start_container(self, container_id: str) -> None:
        self._post(f"/containers/{container_id}/start")
        
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        self._post(f"/containers/{container_id}/stop", params={"t": timeout})
        
    def restart_container(self, container_id: str, timeout: int = 10) -> None:
        self._post(f"/containers/{container_id}/restart", params={"t": timeout})
        
    def get_container_logs(self, container_id: str, max_lines: int = 200) -> str:
        url = f"{self.base_url}/containers/{container_id}/logs"
        try:
            res = self.session.get(url, params={"stdout": True, "stderr": True, "tail": max_lines, "timestamps": True}, timeout=self.timeout)
            if 200 <= res.status_code < 300:
                import re
                clean_text = re.sub(r'[^\x20-\x7E\n\t]', '', res.text)
                return clean_text
            self._handle_response(res)
        except Timeout:
            raise DockerTimeoutError(f"Request to {url} timed out")
        except ConnectionError as e:
            raise DockerConnectionError(f"Failed to connect to Docker API: {str(e)}")
        except RequestException as e:
            raise DockerAPIError(f"Request failed: {str(e)}")
        return ""

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get a single snapshot of container stats (CPU, memory, network I/O)."""
        url = f"{self.base_url}/containers/{container_id}/stats"
        try:
            # stream=False gives one snapshot and closes
            res = self.session.get(url, params={"stream": False}, timeout=10)
            if 200 <= res.status_code < 300:
                return res.json()
            self._handle_response(res)
        except Timeout:
            raise DockerTimeoutError(f"Stats request timed out")
        except ConnectionError as e:
            raise DockerConnectionError(f"Failed to connect to Docker API: {str(e)}")
        except RequestException as e:
            raise DockerAPIError(f"Request failed: {str(e)}")
        return {}

