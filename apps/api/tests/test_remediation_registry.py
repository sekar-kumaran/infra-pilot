import pytest
from app.services.remediation_registry import RemediationRegistry, RemediationStrategy
from app.models.enums import ResourceType, RiskLevel

def test_registry_contains_default_strategies():
    strategies = RemediationRegistry.get_all_strategies()
    assert len(strategies) > 0
    names = [s.name for s in strategies]
    assert "restore_service" in names
    assert "restart_container" in names
    assert "restart_deployment" in names

def test_get_strategy_by_name():
    s = RemediationRegistry.get_strategy("restart_instance")
    assert s is not None
    assert s.required_capability == "cloud_compute_management"
    assert s.risk_level == RiskLevel.HIGH

def test_get_strategies_for_resource():
    strats = RemediationRegistry.get_strategies_for_resource(ResourceType.KUBERNETES_DEPLOYMENT)
    assert len(strats) == 1
    assert strats[0].name == "restart_deployment"
    
    strats = RemediationRegistry.get_strategies_for_resource(ResourceType.CLOUD_INSTANCE)
    assert len(strats) >= 2
    names = [s.name for s in strats]
    assert "restart_instance" in names
    assert "collect_diagnostics" in names
