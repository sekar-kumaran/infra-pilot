from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.models.enums import ProviderType, ResourceType, RiskLevel
from app.integrations.registry import ProviderCapabilityRegistry
from app.services.action_registry import ActionRegistry
from app.services.remediation_registry import RemediationRegistry, RemediationStrategy

class ResolvedProviderStrategy(BaseModel):
    provider: ProviderType
    action: str
    executor: str
    risk: RiskLevel
    requires_approval: bool
    verification: str

class ProviderResolver:
    
    @classmethod
    def resolve_provider_for_strategy(
        cls, 
        strategy: RemediationStrategy, 
        target_resource_type: ResourceType
    ) -> Optional[ResolvedProviderStrategy]:
        
        # We need a provider that advertises the required capability
        # and supports the resource type
        capabilities = ProviderCapabilityRegistry.get_all()
        
        valid_providers = []
        for cap in capabilities:
            if strategy.required_capability in cap.capabilities:
                if target_resource_type in cap.resources:
                    valid_providers.append(cap)
                    
        if not valid_providers:
            return None
            
        # Select the first matching provider for now, optionally sort by priority or health
        # In a real scenario, we might check AdapterRegistry for healthy instances
        for cap in valid_providers:
            all_actions = cap.read_operations + cap.mutation_operations
            for action_name in all_actions:
                if action_name in strategy.allowed_actions:
                    action_def = ActionRegistry.get_action(action_name)
                    if action_def and target_resource_type in action_def.target_resource_types:
                        return ResolvedProviderStrategy(
                            provider=cap.provider,
                            action=action_name,
                            executor=action_def.executor_name,
                            risk=action_def.risk_level,
                            requires_approval=action_def.requires_approval,
                            verification=action_def.verification_strategy or strategy.verification_requirement
                        )
                        
        return None
