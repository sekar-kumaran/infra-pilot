import pytest
from app.integrations.providers.nagios.adapter import NagiosAdapter
from app.integrations.providers.nagios.client import NagiosClient
from app.models.enums import ProviderType

def test_nagios_secret_redaction_metadata():
    adapter = NagiosAdapter()
    config = {"base_url": "http://test", "status_endpoint": "/status.dat"}
    secrets = {"username": "admin", "password": "supersecretpassword"}
    
    # We must mock get_status to return something
    from unittest.mock import patch, MagicMock
    from app.integrations.providers.nagios.schemas import NagiosHostStatus
    
    with patch('app.integrations.providers.nagios.adapter.NagiosClient') as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_status.return_value = (
            [NagiosHostStatus(host_name="test", current_state=0)], []
        )
        mock_client.return_value = mock_instance
        
        resources = adapter.discover_resources(config, secrets)
        
        # Check that metadata does NOT contain secrets
        for r in resources:
            metadata_str = str(r.metadata)
            assert "admin" not in metadata_str
            assert "supersecretpassword" not in metadata_str
            assert "password" not in r.metadata
            assert "username" not in r.metadata

def test_client_auth_is_tuple():
    client = NagiosClient("http://test", "/status.dat", secrets={"username": "a", "password": "b"})
    auth = client._get_auth()
    assert auth == ("a", "b")
    assert isinstance(auth, tuple)
