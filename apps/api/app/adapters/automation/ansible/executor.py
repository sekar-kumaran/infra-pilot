import logging
from typing import Dict, Any, Tuple
import os

from app.adapters.automation.base import AutomationExecutor
from app.services.action_registry import ActionRegistry

from .client import AnsibleClient
from .errors import AnsibleValidationError, AnsibleTimeoutError, AnsibleExecutionError
from .playbook_registry import resolve_playbook_path
from .inventory import resolve_inventory_path, resolve_target_host
from .sanitizer import sanitize_identifier

logger = logging.getLogger(__name__)

class AnsibleAutomationExecutor(AutomationExecutor):
    """
    Real execution provider for Ansible playbooks.
    Complies with AutomationExecutor interface, strictly preventing arbitrary command execution.
    """
    
    def __init__(self, client: AnsibleClient = None):
        self.client = client or AnsibleClient()
        
    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Validates action is registered, playbook exists, and parameters are safe.
        """
        action_def = ActionRegistry.get_action(action_name)
        if not action_def:
            logger.error(f"Action '{action_name}' is not registered.")
            return False
            
        if action_def.executor_name != "ansible":
            logger.error(f"Action '{action_name}' is not an ansible action.")
            return False
            
        if not ActionRegistry.validate_parameters(action_name, parameters):
            logger.error(f"Action '{action_name}' failed parameter schema validation.")
            return False
            
        # Ensure parameters are safe identifiers
        try:
            for k, v in parameters.items():
                if k not in ["resource"]: # Resource is handled separately during execution
                    sanitize_identifier(v)
            resolve_playbook_path(action_name)
        except (ValueError, AnsibleValidationError) as e:
            logger.error(f"Ansible validation failed: {str(e)}")
            return False
            
        return True

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Executes a registered playbook against a resolved InfraPilot resource.
        """
        try:
            if not self.validate(action_name, parameters):
                return False, {}, f"Validation failed for action {action_name}"
                
            # Extract and validate resource
            resource = parameters.get("resource")
            if not resource:
                return False, {}, "No resource provided to Ansible executor"
                
            # Resolve target and paths
            target_host = resolve_target_host(resource)
            inventory_path = resolve_inventory_path()
            playbook_path = resolve_playbook_path(action_name)
            
            # Prepare extra vars (excluding internal parameters like 'resource')
            extra_vars = {k: v for k, v in parameters.items() if k != "resource"}
            
            # Fetch timeout from config or default to 300
            timeout = int(os.getenv("ANSIBLE_MAX_EXECUTION_TIMEOUT", "300"))
            
            # Execute
            result = self.client.execute_playbook(
                playbook_path=playbook_path,
                inventory_path=inventory_path,
                target_host=target_host,
                extra_vars=extra_vars,
                timeout_seconds=timeout
            )
            
            output = {
                "return_code": result.return_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": result.duration_seconds
            }
            
            return result.success, output, result.error_message or "Success"
            
        except AnsibleTimeoutError as e:
            return False, {}, f"Timeout: {str(e)}"
        except (AnsibleValidationError, AnsibleExecutionError) as e:
            return False, {}, f"Execution error: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error in Ansible execution")
            return False, {}, f"Unexpected error: {str(e)}"

    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Cancellation for Ansible is currently a no-op as Celery handles job termination.
        A real implementation could track subprocess PIDs.
        """
        logger.warning(f"Cancellation requested for {action_name}, but currently unsupported by Ansible executor directly.")
        return False

    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Verifies the execution by running a corresponding verify playbook or using action metadata.
        For simplicity in Phase 1.14, if there's no verify playbook, we return True if execution succeeded.
        """
        action_def = ActionRegistry.get_action(action_name)
        if not action_def or not action_def.verification_strategy:
            return True, expected_state, "No verification strategy required"
            
        verify_action = action_def.verification_strategy
        
        # In a real environment, we'd run the verify playbook
        if verify_action == "verify_service":
            # For this test implementation, we'll try to run the check_service playbook 
            try:
                verify_playbook = resolve_playbook_path("check_service")
                target_host = resolve_target_host(parameters.get("resource"))
                inventory_path = resolve_inventory_path()
                extra_vars = {k: v for k, v in parameters.items() if k != "resource"}
                
                result = self.client.execute_playbook(
                    playbook_path=verify_playbook,
                    inventory_path=inventory_path,
                    target_host=target_host,
                    extra_vars=extra_vars,
                    timeout_seconds=60
                )
                
                if result.success:
                    return True, "Active", "Service verified as active"
                else:
                    return False, "Inactive", "Service failed verification"
            except Exception as e:
                return False, None, f"Verification failed with error: {str(e)}"
                
        return False, None, f"Unknown verification strategy: {verify_action}"
