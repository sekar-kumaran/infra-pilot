from unittest.mock import Mock, patch
from app.integrations.providers.prometheus.adapter import PrometheusAdapter

@patch('app.integrations.providers.prometheus.adapter.PrometheusClient')
def test_prometheus_adapter_read_metrics(mock_client_cls):
    mock_client = Mock()
    mock_client.query.return_value = {
        "resultType": "vector",
        "result": [{"metric": {"__name__": "up"}, "value": [1672531200, "1"]}]
    }
    mock_client_cls.return_value = mock_client
    
    adapter = PrometheusAdapter()
    metrics = adapter.read_metrics({"base_url": "http://fake", "timeout_seconds": 5}, {}, "up")
    
    assert metrics["resultType"] == "vector"
    assert len(metrics["result"]) == 1
    assert metrics["result"][0]["value"][1] == "1"
    mock_client.query.assert_called_with("up")
