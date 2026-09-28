import requests
import tempfile
import os
from typing import Dict, Any, List, Optional
from .errors import (
    KubernetesAuthenticationError,
    KubernetesAuthorizationError,
    KubernetesResourceNotFoundError,
    KubernetesTimeoutError,
    KubernetesRateLimitError,
    KubernetesServerError,
    KubernetesConnectionError
)

class KubernetesClient:
    def __init__(self, base_url: str, token: Optional[str] = None, verify_tls: bool = True, ca_cert: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls
        
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
        self.ca_cert_file = None
        if verify_tls and ca_cert:
            fd, self.ca_cert_file = tempfile.mkstemp(text=True)
            with os.fdopen(fd, 'w') as f:
                f.write(ca_cert)
            self.session.verify = self.ca_cert_file
        elif not verify_tls:
            self.session.verify = False

    def __del__(self):
        if self.ca_cert_file and os.path.exists(self.ca_cert_file):
            try:
                os.remove(self.ca_cert_file)
            except OSError:
                pass

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        if response.ok:
            return response.json()
            
        status = response.status_code
        if status == 401:
            raise KubernetesAuthenticationError("Unauthorized")
        elif status == 403:
            raise KubernetesAuthorizationError("Forbidden")
        elif status == 404:
            raise KubernetesResourceNotFoundError("Not Found")
        elif status == 408:
            raise KubernetesTimeoutError("Request Timeout")
        elif status == 429:
            raise KubernetesRateLimitError("Too Many Requests")
        elif 500 <= status < 600:
            raise KubernetesServerError(f"Server Error: {status}")
            
        response.raise_for_status()
        return {}

    def _request(self, method: str, path: str, json: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            req_headers = {}
            if headers:
                req_headers.update(headers)
                
            response = self.session.request(
                method, 
                url, 
                json=json, 
                headers=req_headers,
                timeout=(5, 30) # 5s connect, 30s read
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            raise KubernetesTimeoutError(f"Connection timeout to {self.base_url}")
        except requests.exceptions.ConnectionError:
            raise KubernetesConnectionError(f"Connection failed to {self.base_url}")
        except requests.exceptions.RequestException as e:
            # Mask potential sensitive info in exception string
            raise KubernetesConnectionError("An error occurred connecting to Kubernetes")

    def get_version(self) -> Dict[str, Any]:
        return self._request("GET", "/version")

    def list_namespaces(self) -> List[Dict[str, Any]]:
        resp = self._request("GET", "/api/v1/namespaces")
        return resp.get("items", [])

    def list_nodes(self) -> List[Dict[str, Any]]:
        resp = self._request("GET", "/api/v1/nodes")
        return resp.get("items", [])

    def list_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/api/v1/namespaces/{namespace}/pods" if namespace else "/api/v1/pods"
        resp = self._request("GET", path)
        return resp.get("items", [])

    def list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/apps/v1/namespaces/{namespace}/deployments" if namespace else "/apis/apps/v1/deployments"
        resp = self._request("GET", path)
        return resp.get("items", [])

    def list_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/api/v1/namespaces/{namespace}/services" if namespace else "/api/v1/services"
        resp = self._request("GET", path)
        return resp.get("items", [])

    def get_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        return self._request("GET", f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}")

    def get_pod(self, namespace: str, name: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/namespaces/{namespace}/pods/{name}")

    def scale_deployment(self, namespace: str, name: str, replicas: int) -> Dict[str, Any]:
        # Using strategic merge patch or merge patch for scaling
        headers = {"Content-Type": "application/strategic-merge-patch+json"}
        payload = {"spec": {"replicas": replicas}}
        return self._request("PATCH", f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}", json=payload, headers=headers)

    def restart_pod(self, namespace: str, name: str) -> None:
        # Delete the pod to trigger a restart if managed by a controller (Deployment, ReplicaSet, etc.)
        self._request("DELETE", f"/api/v1/namespaces/{namespace}/pods/{name}")

    def list_replicasets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/apps/v1/namespaces/{namespace}/replicasets" if namespace else "/apis/apps/v1/replicasets"
        return self._request("GET", path).get("items", [])

    def list_daemonsets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/apps/v1/namespaces/{namespace}/daemonsets" if namespace else "/apis/apps/v1/daemonsets"
        return self._request("GET", path).get("items", [])

    def list_statefulsets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/apps/v1/namespaces/{namespace}/statefulsets" if namespace else "/apis/apps/v1/statefulsets"
        return self._request("GET", path).get("items", [])

    def list_jobs(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/batch/v1/namespaces/{namespace}/jobs" if namespace else "/apis/batch/v1/jobs"
        return self._request("GET", path).get("items", [])

    def list_cronjobs(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/batch/v1/namespaces/{namespace}/cronjobs" if namespace else "/apis/batch/v1/cronjobs"
        return self._request("GET", path).get("items", [])

    def list_configmaps(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/api/v1/namespaces/{namespace}/configmaps" if namespace else "/api/v1/configmaps"
        return self._request("GET", path).get("items", [])

    def list_secrets_metadata(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/api/v1/namespaces/{namespace}/secrets" if namespace else "/api/v1/secrets"
        # We must fetch secrets but STRIP THE VALUES before returning
        resp = self._request("GET", path)
        items = resp.get("items", [])
        for item in items:
            # Strip data and stringData
            item.pop("data", None)
            item.pop("stringData", None)
        return items

    def list_ingress(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses" if namespace else "/apis/networking.k8s.io/v1/ingresses"
        return self._request("GET", path).get("items", [])

    def restart_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        from datetime import datetime
        now_str = datetime.utcnow().isoformat() + "Z"
        headers = {"Content-Type": "application/strategic-merge-patch+json"}
        payload = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now_str
                        }
                    }
                }
            }
        }
        return self._request("PATCH", f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}", json=payload, headers=headers)

    def pause_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        headers = {"Content-Type": "application/strategic-merge-patch+json"}
        payload = {"spec": {"paused": True}}
        return self._request("PATCH", f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}", json=payload, headers=headers)

    def resume_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        headers = {"Content-Type": "application/strategic-merge-patch+json"}
        payload = {"spec": {"paused": False}}
        return self._request("PATCH", f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}", json=payload, headers=headers)


