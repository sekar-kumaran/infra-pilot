import pytest
from app.api.v1.endpoints.integrations import get_integration_metrics
from fastapi import HTTPException
from unittest.mock import Mock, patch

def test_prometheus_security_promql_validation():
    # Test that unsafe PromQL queries are rejected by the API endpoint
    
    mock_integration = Mock()
    mock_integration.status = "HEALTHY"
    mock_integration.provider = "prometheus"
    mock_integration.secret_payload = None
    
    mock_service = Mock()
    mock_service.get.return_value = mock_integration
    
    mock_adapter = Mock()
    mock_caps = Mock()
    mock_caps.metrics_read = True
    mock_adapter.get_capabilities.return_value = mock_caps
    
    with patch('app.api.v1.endpoints.integrations.IntegrationService', return_value=mock_service):
        with patch('app.api.v1.endpoints.integrations.AdapterRegistry.get_adapter', return_value=mock_adapter):
            # Valid query should proceed and call adapter
            mock_adapter.read_metrics.return_value = {"status": "success"}
            result = get_integration_metrics(db=Mock(), integration_id=Mock(), query="up{job='api'}", current_user=Mock())
            assert result == {"status": "success"}
            
            # Invalid/Unsafe query should raise HTTPException 400
            with pytest.raises(HTTPException) as excinfo:
                get_integration_metrics(db=Mock(), integration_id=Mock(), query="sum(rate(http_requests_total[5m]))", current_user=Mock())
            assert excinfo.value.status_code == 400
            assert "unsafe or unsupported" in str(excinfo.value.detail)

def test_prometheus_security_secrets_encrypted():
    from app.core.encryption import extract_secrets
    
    config = {
        "base_url": "http://test",
        "bearer_token": "my-secret-token",
        "nested": {
            "password": "test"
        }
    }
    
    safe_config, secrets = extract_secrets(config)
    
    assert "bearer_token" not in safe_config
    assert "bearer_token" in secrets
    assert secrets["bearer_token"] == "my-secret-token"
    
    assert "password" not in safe_config["nested"]
    assert "password" in secrets["nested"]
    assert secrets["nested"]["password"] == "test"
