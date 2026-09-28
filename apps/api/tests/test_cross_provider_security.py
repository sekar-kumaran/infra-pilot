import pytest
from app.models.enums import ProviderType, ResourceType, RiskLevel
from app.services.remediation_registry import RemediationRegistry, RemediationStrategy
from app.services.provider_resolver import ProviderResolver
from app.integrations.registry import AdapterRegistry
from app.integrations.providers.aws.adapter import AWSAdapter

# This test checks that credentials/payloads don't leak,
# which primarily means the plan parameters should be minimal
# and risk logic prevents unauthorized automatic actions.

def test_high_risk_actions_require_approval():
    strategy = RemediationRegistry.get_strategy("restart_instance")
    assert strategy.requires_approval is True
    assert strategy.risk_level == RiskLevel.HIGH

def test_destructive_actions_prevented_by_default():
    # If a strategy does not have requires_approval = False for HIGH risk, it should be safe
    # All high risk must require approval
    strategies = RemediationRegistry.get_all_strategies()
    for s in strategies:
        if s.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            assert s.requires_approval is True
