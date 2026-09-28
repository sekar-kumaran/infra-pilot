import pytest
from unittest.mock import patch, MagicMock

from app.integrations.providers.nagios.adapter import NagiosAdapter
from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.providers.nagios.schemas import NagiosHostStatus, NagiosServiceStatus

@patch('app.integrations.providers.nagios.adapter.NagiosClient')
def test_nagios_discovery_mapping(mock_client_class):
    mock_instance = MagicMock()
    mock_instance.get_status.return_value = (
        [
            NagiosHostStatus(host_name="web1", current_state=0, plugin_output="OK"),
            NagiosHostStatus(host_name="db1", current_state=1, plugin_output="DOWN")
        ],
        [
            NagiosServiceStatus(host_name="web1", service_description="HTTP", current_state=2, plugin_output="CRITICAL")
        ]
    )
    mock_client_class.return_value = mock_instance
    
    adapter = NagiosAdapter()
    resources = adapter.discover_resources(
        {"base_url": "http://test", "status_endpoint": "/status.dat"}, {}
    )
    
    assert len(resources) == 3
    
    # Verify deterministic IDs
    assert any(r.external_id == "nagios/host/web1" for r in resources)
    assert any(r.external_id == "nagios/host/db1" for r in resources)
    assert any(r.external_id == "nagios/service/web1/HTTP" for r in resources)
    
    # Verify state mapping
    web1 = next(r for r in resources if r.external_id == "nagios/host/web1")
    assert web1.status == ResourceStatus.ACTIVE
    
    db1 = next(r for r in resources if r.external_id == "nagios/host/db1")
    assert db1.status == ResourceStatus.FAILED
    
    http_svc = next(r for r in resources if r.external_id == "nagios/service/web1/HTTP")
    assert http_svc.status == ResourceStatus.FAILED
    assert http_svc.metadata["state"] == 2
    assert http_svc.metadata["entity_type"] == "service"
