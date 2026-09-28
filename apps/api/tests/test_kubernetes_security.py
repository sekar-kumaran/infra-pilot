import pytest
from app.integrations.providers.kubernetes.schemas import KubernetesConfigSchema
from pydantic import ValidationError

def test_kubernetes_config_schema_validation():
    # Valid config
    config = KubernetesConfigSchema(
        base_url="https://k8s.example.com",
        verify_tls=True
    )
    assert config.base_url == "https://k8s.example.com"
    
    # Missing required url
    with pytest.raises(ValidationError):
        KubernetesConfigSchema(verify_tls=True)
        
    # Invalid URL scheme
    with pytest.raises(ValidationError):
        KubernetesConfigSchema(base_url="ftp://k8s.example.com", verify_tls=True)
