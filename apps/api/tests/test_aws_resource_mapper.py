from app.integrations.providers.aws.resource_mapper import map_instance, map_vpc
from app.models.enums import ResourceStatus

class TestAWSResourceMapper:
    def test_map_instance(self):
        raw = {
            "InstanceId": "i-123",
            "State": {"Name": "running"},
            "InstanceType": "t2.micro",
            "Tags": [{"Key": "Name", "Value": "web-server"}]
        }
        res = map_instance(raw, "us-east-1")
        assert res.external_id == "aws/instance/i-123"
        assert res.name == "web-server"
        assert res.status == ResourceStatus.ACTIVE
        assert res.metadata["instance_type"] == "t2.micro"
        assert "Name" in res.metadata["tags"]

    def test_map_vpc(self):
        raw = {
            "VpcId": "vpc-1",
            "State": "available",
            "CidrBlock": "10.0.0.0/16",
            "Tags": [{"Key": "Name", "Value": "main-vpc"}]
        }
        res = map_vpc(raw, "us-east-1")
        assert res.external_id == "aws/vpc/vpc-1"
        assert res.name == "main-vpc"
        assert res.status == ResourceStatus.ACTIVE
        assert res.metadata["cidr_block"] == "10.0.0.0/16"
