import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, EndpointConnectionError
from app.integrations.providers.aws.client import AWSClient
from app.integrations.providers.aws.schemas import AWSIntegrationConfig, AWSIntegrationSecrets, AWSEndpointOverrides
from app.integrations.providers.aws.errors import (
    AWSAuthenticationError, AWSAuthorizationError, AWSResourceNotFoundError,
    AWSThrottlingError, AWSInvalidParameterError, AWSNetworkError, AWSAPIError
)

@pytest.fixture
def config():
    return AWSIntegrationConfig(region="us-east-1", verify_tls=False)

@pytest.fixture
def secrets():
    return AWSIntegrationSecrets(access_key_id="test", secret_access_key="test")

@pytest.fixture
def aws_client(config, secrets):
    with patch("boto3.Session"):
        return AWSClient(config, secrets)

class TestAWSClientExceptions:
    def test_auth_failure(self, aws_client):
        err = ClientError({"Error": {"Code": "AuthFailure", "Message": "auth"}}, "op")
        with pytest.raises(AWSAuthenticationError):
            aws_client._handle_boto_exception(err, "op")

    def test_access_denied(self, aws_client):
        err = ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "op")
        with pytest.raises(AWSAuthorizationError):
            aws_client._handle_boto_exception(err, "op")

    def test_not_found(self, aws_client):
        err = ClientError({"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "404"}}, "op")
        with pytest.raises(AWSResourceNotFoundError):
            aws_client._handle_boto_exception(err, "op")

    def test_throttling(self, aws_client):
        err = ClientError({"Error": {"Code": "Throttling", "Message": "slow down"}}, "op")
        with pytest.raises(AWSThrottlingError):
            aws_client._handle_boto_exception(err, "op")

    def test_network_error(self, aws_client):
        err = EndpointConnectionError(endpoint_url="http://x")
        with pytest.raises(AWSNetworkError):
            aws_client._handle_boto_exception(err, "op")

class TestAWSClientMethods:
    def test_get_account_identity(self, aws_client):
        aws_client._sts_client.get_caller_identity = MagicMock(return_value={"Account": "123", "Arn": "arn", "UserId": "uid"})
        res = aws_client.get_account_identity()
        assert res["account_id"] == "123"

    @patch("app.integrations.providers.aws.client.AWSClient._get_client")
    def test_list_regions(self, mock_get_client, aws_client):
        mock_ec2 = MagicMock()
        mock_ec2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
        mock_get_client.return_value = mock_ec2
        res = aws_client.list_regions()
        assert len(res) == 1
        assert res[0]["RegionName"] == "us-east-1"
