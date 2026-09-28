from unittest.mock import Mock, patch
from app.integrations.providers.prometheus.adapter import PrometheusAdapter
from app.models.enums import ResourceStatus

def test_prometheus_adapter_capabilities():
    adapter = PrometheusAdapter()
    caps = adapter.get_capabilities()
    assert caps.resource_discovery is True
    assert caps.metrics_read is True
    assert caps.alerts_read is True
    assert caps.logs_read is False

@patch('app.integrations.providers.prometheus.adapter.PrometheusClient')
def test_prometheus_adapter_discover_resources(mock_client_cls):
    mock_client = Mock()
    mock_client.get_targets.return_value = {
        "activeTargets": [
            {
                "labels": {"job": "api", "instance": "10.0.0.1:8080"},
                "health": "up",
                "scrapeUrl": "http://10.0.0.1:8080/metrics"
            }
        ]
    }
    mock_client_cls.return_value = mock_client
    
    adapter = PrometheusAdapter()
    resources = adapter.discover_resources({"base_url": "http://fake", "timeout_seconds": 5}, {})
    
    assert len(resources) == 1
    res = resources[0]
    assert res.external_id == "api/10.0.0.1:8080"
    assert res.name == "api-10.0.0.1:8080"
    assert res.status == ResourceStatus.ACTIVE
    assert res.metadata["job"] == "api"
    assert res.metadata["instance"] == "10.0.0.1:8080"
