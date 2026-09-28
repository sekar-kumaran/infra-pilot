import logging
import time
from typing import Dict, Any, Tuple

from app.adapters.automation.base import AutomationExecutor
from app.integrations.providers.aws.schemas import AWSIntegrationConfig, AWSIntegrationSecrets
from app.integrations.providers.aws.client import AWSClient
from app.integrations.providers.aws.errors import AWSProviderError

logger = logging.getLogger(__name__)

class AWSAutomationExecutor(AutomationExecutor):
    def __init__(self):
        self.supported_actions = [
            "aws_collect_instance_information",
            "aws_collect_volume_information",
            "aws_collect_network_information",
            "aws_start_instance",
            "aws_stop_instance",
            "aws_reboot_instance",
            "aws_terminate_instance",
            "aws_collect_asg_information",
            "aws_set_asg_desired_capacity",
            "aws_suspend_asg_process",
            "aws_resume_asg_process",
            "aws_collect_database_information",
            "aws_collect_bucket_information"
        ]

    def _get_client(self, integration) -> AWSClient:
        # integration should have config and secrets loaded
        config = AWSIntegrationConfig(**integration.config)
        # secrets are assumed to be loaded onto integration in parameters
        secrets = AWSIntegrationSecrets(**integration.get("secrets", {}))
        return AWSClient(config=config, secrets=secrets)

    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        if action_name not in self.supported_actions:
            return False
        if not parameters.get("resource"):
            return False
        if not parameters.get("integration"):
            return False
        return True

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        if not self.validate(action_name, parameters):
            return False, {}, "Validation failed"

        resource = parameters["resource"]
        integration = parameters["integration"]
        external_id = resource.external_id
        
        parts = external_id.split("/")
        
        try:
            client = self._get_client(integration)
            
            # EC2 Actions
            if action_name in ["aws_start_instance", "aws_stop_instance", "aws_reboot_instance", "aws_terminate_instance", "aws_collect_instance_information"]:
                if len(parts) < 3 or parts[1] != "instance":
                    return False, {}, f"Target resource {external_id} is not an AWS instance"
                instance_id = parts[2]

                if action_name == "aws_collect_instance_information":
                    instance_info = client.get_instance(instance_id)
                    return True, {"instance_info": instance_info}, ""
                elif action_name == "aws_start_instance":
                    client.start_instance(instance_id)
                    return True, {"status": f"Start signal sent to {instance_id}"}, ""
                elif action_name == "aws_stop_instance":
                    client.stop_instance(instance_id)
                    return True, {"status": f"Stop signal sent to {instance_id}"}, ""
                elif action_name == "aws_reboot_instance":
                    client.reboot_instance(instance_id)
                    return True, {"status": f"Reboot signal sent to {instance_id}"}, ""
                elif action_name == "aws_terminate_instance":
                    client.terminate_instance(instance_id)
                    return True, {"status": f"Terminate signal sent to {instance_id}"}, ""

            # ASG Actions
            elif action_name in ["aws_collect_asg_information", "aws_set_asg_desired_capacity", "aws_suspend_asg_process", "aws_resume_asg_process"]:
                if len(parts) < 3 or parts[1] != "asg":
                    return False, {}, f"Target resource {external_id} is not an Auto Scaling Group"
                asg_name = parts[2]
                
                if action_name == "aws_collect_asg_information":
                    return True, {"status": "aws_collect_asg_information simulated"}, ""
                elif action_name == "aws_set_asg_desired_capacity":
                    desired_capacity = parameters.get("desired_capacity")
                    if desired_capacity is None:
                        return False, {}, "Missing 'desired_capacity' parameter"
                    client.set_asg_desired_capacity(asg_name, int(desired_capacity))
                    return True, {"status": f"Set desired capacity to {desired_capacity}"}, ""
                elif action_name == "aws_suspend_asg_process":
                    client.suspend_asg_process(asg_name)
                    return True, {"status": f"Suspended processes for {asg_name}"}, ""
                elif action_name == "aws_resume_asg_process":
                    client.resume_asg_process(asg_name)
                    return True, {"status": f"Resumed processes for {asg_name}"}, ""

            # Miscellaneous Read Actions
            elif action_name == "aws_collect_volume_information":
                return True, {"status": "aws_collect_volume_information simulated"}, ""
            elif action_name == "aws_collect_network_information":
                return True, {"status": "aws_collect_network_information simulated"}, ""
            elif action_name == "aws_collect_database_information":
                return True, {"status": "aws_collect_database_information simulated"}, ""
            elif action_name == "aws_collect_bucket_information":
                return True, {"status": "aws_collect_bucket_information simulated"}, ""
                
            return False, {}, f"Unsupported AWS action: {action_name}"

        except AWSProviderError as e:
            return False, {}, f"AWS API failed: {str(e)}"
        except Exception as e:
            return False, {}, f"Unexpected executor error: {str(e)}"

    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        return False

    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        if not self.validate(action_name, parameters):
            return False, None, "Validation failed"

        resource = parameters["resource"]
        integration = parameters["integration"]
        external_id = resource.external_id
        parts = external_id.split("/")

        max_attempts = 15
        delay = 5

        try:
            client = self._get_client(integration)
            
            # ASG Capacity Verification
            if expected_state == "aws_verify_asg_capacity":
                asg_name = parts[2]
                desired_capacity = parameters.get("desired_capacity")
                for attempt in range(max_attempts):
                    try:
                        asgs = client.list_auto_scaling_groups()
                        for asg in asgs:
                            if asg.get("AutoScalingGroupName") == asg_name:
                                if asg.get("DesiredCapacity") == desired_capacity:
                                    return True, asg.get("DesiredCapacity"), ""
                    except AWSProviderError as e:
                        logger.warning(f"Verification check failed on attempt {attempt+1}: {e}")
                    time.sleep(delay)
                return False, None, f"AWS ASG capacity verification timed out for {asg_name}"

            # EC2 State Verification
            if expected_state in ["running", "stopped", "terminated"]:
                instance_id = parts[2]
                for attempt in range(max_attempts):
                    try:
                        instance = client.get_instance(instance_id)
                        state = instance.get("State", {}).get("Name", "")
                        
                        if expected_state == "running":
                            if state == "running":
                                return True, state, ""
                            if state in ("shutting-down", "terminated", "stopping"):
                                return False, state, f"Instance in unexpected state: {state}"
                                
                        elif expected_state == "stopped":
                            if state == "stopped":
                                return True, state, ""
                            if state in ("terminated", "shutting-down"):
                                return True, state, ""

                        elif expected_state == "terminated":
                            if state == "terminated":
                                return True, state, ""
                                
                    except AWSProviderError as e:
                        logger.warning(f"Verification check failed on attempt {attempt+1}: {e}")
                        
                    time.sleep(delay)

                return False, None, f"AWS resource verification timed out expecting {expected_state}"
            
            return True, expected_state, ""
            
        except Exception as e:
            return False, None, f"Verification execution failed: {str(e)}"
