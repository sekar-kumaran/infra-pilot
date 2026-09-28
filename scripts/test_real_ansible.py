import os
import sys
from app.models.automation import Playbook, PlaybookStep, AutomationExecution
from app.models.incidents import Incident
from app.models.events import Alert
from app.models.user import User
from app.models.policy import Policy
from app.models.integration import Integration
from app.models.resource import InfrastructureResource
from app.services.action_registry import ActionRegistry
from app.adapters.automation.ansible.executor import AnsibleAutomationExecutor

def run_acceptance():
    print("==================================================")
    print("PHASE 1.14 REAL PROVIDER ACCEPTANCE TEST")
    print("==================================================")
    
    # 1. Setup real target config via env
    os.environ["ANSIBLE_REAL_INVENTORY"] = "ansible/inventories/example/hosts"
    
    # If the user has a real target, they can provide it via ANSIBLE_REAL_TARGET
    # e.g., export ANSIBLE_REAL_TARGET=my-prod-server
    # If the user has a real target, they can provide it via ANSIBLE_REAL_TARGET
    # e.g., export ANSIBLE_REAL_TARGET=my-prod-server
    target = os.getenv("ANSIBLE_REAL_TARGET", "ansible-test")
    print(f"Executing against REAL target: {target}")
    
    try:
        # Create a mock execution scenario simulating the Celery Worker Context
        print("\n[1] Validating Action Registry...")
        action_name = "collect_system_information"
        action_def = ActionRegistry.get_action(action_name)
        
        if not action_def or action_def.executor_name != "ansible":
            print(f"FAILED: Action {action_name} not registered to ansible")
            sys.exit(1)
            
        print("  OK: Action registered to Ansible Executor")
        
        print("\n[2] Preparing Canonical Resource...")
        resource = InfrastructureResource(
            id="00000000-0000-0000-0000-000000000001",
            name="Acceptance Test Target",
            resource_type="host",
            external_id=f"test/host/{target}",
            metadata_={"hostname": target},
            provider="test",
            status="active"
        )
        print("  OK: Resource metadata prepared")
        
        print("\n[3] Instantiating AnsibleAutomationExecutor...")
        executor = AnsibleAutomationExecutor()
        
        print("\n[4] Validating execution payload...")
        params = {"resource": resource}
        if not executor.validate(action_name, params):
            print("FAILED: Executor validation rejected payload")
            sys.exit(1)
        print("  OK: Payload validated securely")
        
        print("\n[5] Executing Playbook via Subprocess...")
        success, output, msg = executor.execute(action_name, params)
        
        if success:
            print("  OK: Execution Succeeded!")
            print(f"    Duration: {output.get('duration'):.2f}s")
            print("    Stdout:")
            for line in output.get("stdout", "").split("\n")[:10]:
                print(f"      {line}")
        else:
            print(f"FAILED: Execution failed -> {msg}")
            print(f"    Stderr: {output.get('stderr')}")
            print(f"    Stdout: {output.get('stdout')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("ACCEPTANCE PASSED: Real Ansible integration proven.")
    print("==================================================")

if __name__ == "__main__":
    run_acceptance()
