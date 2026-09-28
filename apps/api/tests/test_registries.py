import pytest
from app.services.action_registry import ActionRegistry, ActionDefinition
from app.integrations.capabilities import ProviderCapabilityRegistry, ProviderCapabilityRegistryEntry
from app.models.enums import AutomationActionType, RiskLevel, ProviderType, ResourceType

def test_action_registry_register_and_get():
    ActionRegistry._actions.clear()
    
    def_action = ActionDefinition(
        action_name="test_action",
        action_type=AutomationActionType.EXECUTE_PROVIDER_ACTION,
        risk_level=RiskLevel.LOW,
        parameter_schema=[],
        executor_name="test_executor",
        target_resource_types=[ResourceType.VM],
        requires_approval=True
    )
    
    ActionRegistry.register(def_action)
    
    retrieved = ActionRegistry.get_action("test_action")
    assert retrieved is not None
    assert retrieved.action_name == "test_action"
    assert retrieved.executor_name == "test_executor"
    assert ResourceType.VM in retrieved.target_resource_types
    assert retrieved.requires_approval is True

    all_actions = ActionRegistry.get_all_actions()
    assert len(all_actions) >= 1
    assert "test_action" in [a.action_name for a in all_actions]

def test_provider_capability_registry():
    ProviderCapabilityRegistry._entries.clear()
    
    entry = ProviderCapabilityRegistryEntry(
        provider=ProviderType.ANSIBLE,
        display_name="Ansible",
        version="2.14",
        capabilities=["configuration_management"],
        resources=[ResourceType.VM],
        read_operations=["collect_system_info"],
        mutation_operations=["restart_service"],
        authentication_requirements=["ssh_key"]
    )
    
    ProviderCapabilityRegistry.register(entry)
    
    cap = ProviderCapabilityRegistry.get_capabilities(ProviderType.ANSIBLE)
    assert cap is not None
    assert cap.provider == ProviderType.ANSIBLE
    assert cap.display_name == "Ansible"
    assert "configuration_management" in cap.capabilities
    
    all_caps = ProviderCapabilityRegistry.get_all()
    assert len(all_caps) == 1
    assert all_caps[0].provider == ProviderType.ANSIBLE
