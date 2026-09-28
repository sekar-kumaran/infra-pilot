from typing import Dict, Any, Tuple
import time
from .base import AutomationExecutor

class TestAutomationExecutor(AutomationExecutor):
    """
    A deterministic executor for testing the automation architecture.
    Does not mutate any real infrastructure.
    """
    
    SUPPORTED_ACTIONS = {
        "test_action_success",
        "test_action_failure",
        "test_action_timeout",
        "test_collect_information",
        "test_validate_resource",
        "test_provider_mutation"
    }

    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        return action_name in self.SUPPORTED_ACTIONS

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        if action_name == "test_action_success":
            return True, {"status": "success", "result": "Action completed successfully."}, ""
            
        elif action_name == "test_action_failure":
            return False, {}, "Deterministic failure triggered."
            
        elif action_name == "test_action_timeout":
            time.sleep(2) # Simulate work, actual timeout handled by celery
            return False, {}, "Simulated timeout exceeded."
            
        elif action_name == "test_collect_information":
            return True, {"query_result": "Simulated info for " + parameters.get("query", "unknown")}, ""
            
        elif action_name == "test_validate_resource":
            res_id = parameters.get("resource_id")
            return True, {"valid": True, "resource_id": res_id}, ""
            
        elif action_name == "test_provider_mutation":
            return True, {"mutated": True, "param": parameters.get("action_param")}, ""
            
        return False, {}, f"Unknown action: {action_name}"

    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        return True # Simulate successful cancellation

    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        # For testing, we can simulate verification failure by passing a specific expected_state
        if expected_state == "SIMULATE_FAILURE":
            return False, {"state": "mismatched"}, "Simulated verification failure."
            
        return True, {"state": expected_state}, "Simulated verification success."
