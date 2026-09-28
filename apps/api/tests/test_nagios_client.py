import pytest
import httpx
from unittest.mock import patch, MagicMock

from app.integrations.providers.nagios.client import NagiosClient
from app.integrations.providers.nagios.errors import NagiosAuthenticationError, NagiosConnectionError, NagiosParserError

def test_client_auth_injection():
    client = NagiosClient("http://test", "/status.dat", secrets={"username": "admin", "password": "password123"})
    assert client._get_auth() == ("admin", "password123")
    
    client2 = NagiosClient("http://test", "/status.dat", secrets={})
    assert client2._get_auth() is None

@patch('app.integrations.providers.nagios.client.httpx.Client.get')
def test_client_get_status_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    hoststatus {
        host_name=test
        current_state=0
    }
    """
    mock_get.return_value = mock_resp
    
    client = NagiosClient("http://test", "/status.dat")
    hosts, services = client.get_status()
    
    assert len(hosts) == 1
    assert hosts[0].host_name == "test"
    assert len(services) == 0

@patch('app.integrations.providers.nagios.client.httpx.Client.get')
def test_client_get_status_auth_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp
    
    client = NagiosClient("http://test", "/status.dat")
    with pytest.raises(NagiosAuthenticationError):
        client.get_status()

@patch('app.integrations.providers.nagios.client.httpx.Client.get')
def test_client_get_status_invalid_format(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>Not nagios status</body></html>"
    mock_get.return_value = mock_resp
    
    client = NagiosClient("http://test", "/status.dat")
    with pytest.raises(NagiosParserError):
        client.get_status()

@patch('app.integrations.providers.nagios.client.httpx.Client.get')
def test_client_timeout_error(mock_get):
    mock_get.side_effect = httpx.TimeoutException("Timeout")
    
    client = NagiosClient("http://test", "/status.dat")
    with pytest.raises(NagiosConnectionError):
        client.get_status()
