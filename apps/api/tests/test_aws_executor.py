import pytest
from unittest.mock import MagicMock, patch
from app.adapters.automation.aws.executor import AWSAutomationExecutor

@pytest.fixture
def executor():
    return AWSAutomationExecutor()

@pytest.fixture
def integration():
    mock = MagicMock()
    mock.config = {"region": "us-east-1", "verify_tls": False}
    mock.get.return_value = {}
    return mock

class TestAWSExecutor:
    @patch("app.adapters.automation.aws.executor.AWSClient")
    def test_execute_start_instance(self, mock_client_cls, executor, integration):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        target_resource = MagicMock()
        target_resource.external_id = "aws/instance/i-12345"
        
        parameters = {
            "resource": target_resource,
            "integration": integration
        }
        success, output, err = executor.execute("aws_start_instance", parameters)
        mock_client.start_instance.assert_called_once_with("i-12345")
        assert success is True
        assert "status" in output

    @patch("app.adapters.automation.aws.executor.AWSClient")
    def test_execute_terminate_instance(self, mock_client_cls, executor, integration):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        target_resource = MagicMock()
        target_resource.external_id = "aws/instance/i-12345"
        
        parameters = {
            "resource": target_resource,
            "integration": integration
        }
        success, output, err = executor.execute("aws_terminate_instance", parameters)
        mock_client.terminate_instance.assert_called_once_with("i-12345")
        assert success is True

    @patch("app.adapters.automation.aws.executor.AWSClient")
    def test_execute_set_asg_capacity(self, mock_client_cls, executor, integration):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        target_resource = MagicMock()
        target_resource.external_id = "aws/asg/my-asg"
        
        parameters = {
            "resource": target_resource,
            "integration": integration,
            "desired_capacity": 5
        }
        success, output, err = executor.execute("aws_set_asg_desired_capacity", parameters)
        mock_client.set_asg_desired_capacity.assert_called_once_with("my-asg", 5)
        assert success is True

    def test_invalid_target_format(self, executor, integration):
        target_resource = MagicMock()
        target_resource.external_id = "aws/bucket/my-bucket"
        parameters = {
            "resource": target_resource,
            "integration": integration
        }
        success, output, err = executor.execute("aws_start_instance", parameters)
        assert success is False
        assert "is not an AWS instance" in err
