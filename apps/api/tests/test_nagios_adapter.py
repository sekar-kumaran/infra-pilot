import pytest
from unittest.mock import patch, MagicMock

from app.integrations.providers.nagios.adapter import NagiosAdapter
from app.models.enums import ProviderType, ResourceType, ResourceStatus

def test_nagios_adapter_properties():
    adapter = NagiosAdapter()
    assert adapter.provider_type == ProviderType.NAGIOS
    
    caps = adapter.get_capabilities()
    assert caps.resource_discovery is True
    assert caps.alerts_read is True
    assert caps.metrics_read is False

@patch('app.integrations.providers.nagios.adapter.NagiosClient')
def test_validate_connection(mock_client_class):
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    adapter = NagiosAdapter()
    result = adapter.validate_connection(
        {"base_url": "http://test", "status_endpoint": "/test"},
        {}
    )
    
    assert result is True
    mock_instance.get_status.assert_called_once()

@patch('app.integrations.providers.nagios.adapter.NagiosClient')
def test_discover_resources(mock_client_class):
    mock_instance = MagicMock()
    
    from app.integrations.providers.nagios.schemas import NagiosHostStatus, NagiosServiceStatus
    
    mock_instance.get_status.return_value = (
        [NagiosHostStatus(host_name="server01", current_state=0)],
        [NagiosServiceStatus(host_name="server01", service_description="HTTP", current_state=2)]
    )
    mock_client_class.return_value = mock_instance
    
    adapter = NagiosAdapter()
    resources = adapter.discover_resources(
        {"base_url": "http://test", "status_endpoint": "/test"},
        {}
    )
    
    assert len(resources) == 2
    
    host_res = next(r for r in resources if r.resource_type == ResourceType.HOST)
    assert host_res.external_id == "nagios/host/server01"
    assert host_res.status == ResourceStatus.ACTIVE
    
    svc_res = next(r for r in resources if r.resource_type == ResourceType.SERVICE)
    assert svc_res.external_id == "nagios/service/server01/HTTP"
    assert svc_res.status == ResourceStatus.FAILED
