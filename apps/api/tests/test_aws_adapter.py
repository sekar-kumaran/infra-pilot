import pytest
from unittest.mock import MagicMock, patch
from app.integrations.providers.aws.adapter import AWSAdapter

@pytest.fixture
def config():
    return {"region": "us-east-1", "verify_tls": False}

@pytest.fixture
def secrets():
    return {"access_key_id": "test", "secret_access_key": "test"}

class TestAWSAdapter:
    def test_provider_type(self):
        adapter = AWSAdapter()
        assert adapter.provider_type().value == "aws"

    def test_validate_config(self, config, secrets):
        adapter = AWSAdapter()
        assert adapter.validate_config(config, secrets) is True
        assert adapter.validate_config({}, {}) is False

    @patch("app.integrations.providers.aws.adapter.AWSClient")
    def test_discover_resources(self, mock_client_cls, config, secrets):
        mock_client = MagicMock()
        mock_client.config.region = "us-east-1"
        mock_client.get_account_identity.return_value = {"account_id": "111", "arn": "arn", "user_id": "u"}
        mock_client.list_regions.return_value = [{"RegionName": "us-east-1"}]
        mock_client.list_vpcs.return_value = [{"VpcId": "vpc-1", "State": "available"}]
        mock_client.list_subnets.return_value = []
        mock_client.list_security_groups.return_value = []
        mock_client.list_instances.return_value = [{"InstanceId": "i-123", "State": {"Name": "running"}}]
        mock_client.list_volumes.return_value = []
        mock_client.list_buckets.return_value = []
        mock_client_cls.return_value = mock_client

        adapter = AWSAdapter()
        resources = adapter.discover_resources(config, secrets)
        assert len(resources) == 4 # account, region, vpc, instance
        
        external_ids = [r.external_id for r in resources]
        assert "aws/account/111" in external_ids
        assert "aws/region/us-east-1" in external_ids
        assert "aws/vpc/vpc-1" in external_ids
        assert "aws/instance/i-123" in external_ids
