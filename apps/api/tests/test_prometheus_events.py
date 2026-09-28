from unittest.mock import Mock, patch
from app.integrations.providers.prometheus.adapter import PrometheusAdapter

@patch('app.integrations.providers.prometheus.adapter.PrometheusClient')
def test_prometheus_adapter_get_alerts(mock_client_cls):
    mock_client = Mock()
    mock_client.get_alerts.return_value = {
        "alerts": [
            {
                "labels": {"alertname": "HighCPU", "job": "api", "instance": "10.0.0.1"},
                "state": "firing"
            }
        ]
    }
    mock_client_cls.return_value = mock_client
    
    adapter = PrometheusAdapter()
    alerts = adapter.get_alerts({"base_url": "http://fake", "timeout_seconds": 5}, {})
    
    assert len(alerts) == 1
    assert alerts[0]["labels"]["alertname"] == "HighCPU"
    assert alerts[0]["state"] == "firing"
