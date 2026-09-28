import pytest
from unittest.mock import patch, MagicMock
from app.integrations.providers.kubernetes.client import KubernetesClient
from app.integrations.providers.kubernetes.errors import (
    KubernetesAuthenticationError, KubernetesProviderError
)

@pytest.fixture
def kube_client():
    return KubernetesClient(base_url="https://kubernetes.local", token="test-token")

@patch('requests.get')
def test_get_version_success(mock_get, kube_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"gitVersion": "v1.30.0"}
    mock_get.return_value = mock_resp
    
    version = kube_client.get_version()
    assert version["gitVersion"] == "v1.30.0"

@patch('requests.get')
def test_get_version_auth_error(mock_get, kube_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp
    
    with pytest.raises(KubernetesAuthenticationError):
        kube_client.get_version()

@patch('requests.get')
def test_list_namespaces(mock_get, kube_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [{"metadata": {"name": "default"}}]}
    mock_get.return_value = mock_resp
    
    ns = kube_client.list_namespaces()
    assert len(ns) == 1
    assert ns[0]["metadata"]["name"] == "default"

@patch('requests.patch')
def test_scale_deployment(mock_patch, kube_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"spec": {"replicas": 3}}
    mock_patch.return_value = mock_resp
    
    res = kube_client.scale_deployment("default", "my-app", 3)
    assert res["spec"]["replicas"] == 3
    mock_patch.assert_called_once()
    assert mock_patch.call_args[1]['json'] == {"spec": {"replicas": 3}}
