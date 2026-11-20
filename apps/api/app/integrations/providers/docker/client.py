"""
InfraPilot Dual-Transport Docker Engine Client.
Supports BOTH:
1. TCP Docker Proxy (`http://infrapilot_docker_proxy:2375` via alpine/socat)
2. Native Unix Domain Socket (`unix:///var/run/docker.sock` or `/var/run/docker.sock`)
   using Python's built-in `socket.AF_UNIX` + `http.client.HTTPConnection` so
   `requests` never fails with `InvalidSchema: No connection adapters were found for unix://...`!
"""
import json
import socket
import http.client
import urllib.request
from typing import Any, Dict, List, Optional


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection over a local Unix domain socket (/var/run/docker.sock)."""

    def __init__(self, unix_socket_path: str, timeout: int = 5):
        super().__init__("localhost", timeout=timeout)
        self.unix_socket_path = unix_socket_path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.unix_socket_path)
        self.sock = sock


class DockerEngineClient:
    def __init__(self, base_url: str = "http://infrapilot_docker_proxy:2375", timeout: int = 5):
        self.base_url = (base_url or "http://infrapilot_docker_proxy:2375").strip()
        self.timeout = timeout

    def _is_unix_socket(self) -> bool:
        return self.base_url.startswith("unix://") or self.base_url.startswith("/")

    def _socket_path(self) -> str:
        if self.base_url.startswith("unix:///"):
            return "/" + self.base_url[len("unix:///"):]
        if self.base_url.startswith("unix://"):
            return self.base_url[len("unix://"):]
        return self.base_url

    def _request(self, method: str, path: str) -> Any:
        if self._is_unix_socket():
            sock_path = self._socket_path()
            if os.path.exists(sock_path):
                conn = UnixSocketHTTPConnection(sock_path, timeout=self.timeout)
                conn.request(method, path, headers={"Host": "localhost"})
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8", errors="replace")
                conn.close()
                try:
                    return json.loads(raw)
                except Exception:
                    return raw
            # Automatic fallback to socat TCP proxy if socket isn't mounted directly
            tcp_url = f"http://infrapilot_docker_proxy:2375{path}"
        else:
            tcp_url = f"{self.base_url.rstrip('/')}{path}"

        req = urllib.request.Request(tcp_url, method=method)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            try:
                return json.loads(body)
            except Exception:
                return body

    def ping(self) -> bool:
        try:
            res = self._request("GET", "/_ping")
            return str(res).strip() == "OK"
        except Exception:
            return False

    def discover_containers(self) -> List[Dict[str, Any]]:
        try:
            data = self._request("GET", "/containers/json?all=1")
            return data if isinstance(data, list) else []
        except Exception:
            return []
