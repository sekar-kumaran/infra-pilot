import httpx
import logging
from typing import Dict, Any, Tuple
from urllib.parse import urljoin

from .errors import NagiosConnectionError, NagiosAuthenticationError, NagiosParserError
from .parser import NagiosStatusParser
from .schemas import NagiosHostStatus, NagiosServiceStatus

logger = logging.getLogger(__name__)

class NagiosClient:
    def __init__(self, base_url: str, status_endpoint: str, timeout: int = 10, tls_verify: bool = True, secrets: Dict[str, Any] = None):
        self.base_url = base_url.rstrip('/')
        self.status_endpoint = status_endpoint
        self.timeout = timeout
        self.tls_verify = tls_verify
        self.secrets = secrets or {}

    def _get_auth(self):
        username = self.secrets.get("username")
        password = self.secrets.get("password")
        if username and password:
            return (username, password)
        return None

    def get_status(self) -> Tuple[list[NagiosHostStatus], list[NagiosServiceStatus]]:
        url = urljoin(f"{self.base_url}/", self.status_endpoint.lstrip('/'))
        auth = self._get_auth()
        
        try:
            with httpx.Client(verify=self.tls_verify, timeout=self.timeout) as client:
                response = client.get(url, auth=auth)
                
                if response.status_code == 401 or response.status_code == 403:
                    raise NagiosAuthenticationError("Authentication failed for Nagios endpoint")
                
                response.raise_for_status()
                
                content = response.text
                if not content or "{" not in content:
                    raise NagiosParserError("Endpoint returned an invalid format for Nagios status data")
                
                return NagiosStatusParser.parse(content)
                
        except httpx.TimeoutException as e:
            raise NagiosConnectionError(f"Connection to Nagios timed out: {e}")
        except httpx.RequestError as e:
            raise NagiosConnectionError(f"Failed to connect to Nagios: {e}")
        except httpx.HTTPStatusError as e:
            raise NagiosConnectionError(f"Nagios returned HTTP error: {e.response.status_code}")
