import pytest
from app.services.action_registry import ActionRegistry
from app.models.enums import ResourceType

class TestAWSActionSecurity:
    def test_aws_mutations_require_approval(self):
        for action_name in [
            "aws_start_instance", 
            "aws_stop_instance", 
            "aws_reboot_instance", 
            "aws_terminate_instance",
            "aws_set_asg_desired_capacity",
            "aws_suspend_asg_process",
            "aws_resume_asg_process"
        ]:
            action = ActionRegistry.get_action(action_name)
            assert action is not None
            assert action.requires_approval is True

    def test_aws_reads_do_not_require_approval(self):
        for action_name in [
            "aws_collect_instance_information", 
            "aws_collect_volume_information", 
            "aws_collect_network_information",
            "aws_collect_asg_information",
            "aws_collect_database_information",
            "aws_collect_bucket_information"
        ]:
            action = ActionRegistry.get_action(action_name)
            assert action is not None
            assert action.requires_approval is False

    def test_aws_mutations_target_only_specific_resources(self):
        # EC2
        for action_name in ["aws_start_instance", "aws_stop_instance", "aws_reboot_instance", "aws_terminate_instance"]:
            action = ActionRegistry.get_action(action_name)
            assert action.target_resource_types == [ResourceType.CLOUD_INSTANCE]
            
        # ASG
        for action_name in ["aws_set_asg_desired_capacity", "aws_suspend_asg_process", "aws_resume_asg_process"]:
            action = ActionRegistry.get_action(action_name)
            assert action.target_resource_types == [ResourceType.CLOUD_AUTO_SCALING_GROUP]
