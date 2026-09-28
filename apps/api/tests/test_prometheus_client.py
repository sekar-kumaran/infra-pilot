import pytest
import requests
from unittest.mock import Mock, patch
from app.integrations.providers.prometheus.client import PrometheusClient
from app.integrations.providers.prometheus.errors import (
    PrometheusConnectionError,
    PrometheusTimeoutError,
    PrometheusAuthenticationError,
    PrometheusQueryError
)

def test_prometheus_client_success():
    with patch('requests.Session.request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"version": "2.45.0"}}
        mock_request.return_value = mock_response

        client = PrometheusClient("http://fake:9090", {"bearer_token": "secret"})
        data = client.get_buildinfo()
        assert data["version"] == "2.45.0"
        
        # Verify headers
        assert client.session.headers.get("Authorization") == "Bearer secret"

def test_prometheus_client_timeout():
    with patch('requests.Session.request', side_effect=requests.exceptions.Timeout("timeout")):
        client = PrometheusClient("http://fake:9090", {})
        with pytest.raises(PrometheusTimeoutError):
            client.get_buildinfo()

def test_prometheus_client_auth_error():
    with patch('requests.Session.request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        client = PrometheusClient("http://fake:9090", {})
        with pytest.raises(PrometheusAuthenticationError):
            client.get_buildinfo()

def test_prometheus_client_query_error():
    with patch('requests.Session.request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "error", "errorType": "bad_data", "error": "invalid parameter"}
        mock_request.return_value = mock_response

        client = PrometheusClient("http://fake:9090", {})
        with pytest.raises(PrometheusQueryError, match="invalid parameter"):
            client.query("up")
