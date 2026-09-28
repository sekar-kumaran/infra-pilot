import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError, EndpointConnectionError, ConnectTimeoutError

from app.integrations.providers.aws.schemas import AWSIntegrationConfig, AWSIntegrationSecrets
from app.integrations.providers.aws.errors import (
    AWSProviderError,
    AWSAuthenticationError,
    AWSAuthorizationError,
    AWSResourceNotFoundError,
    AWSThrottlingError,
    AWSNetworkError,
    AWSAPIError,
    AWSInvalidParameterError,
)

logger = logging.getLogger(__name__)


class AWSClient:
    def __init__(self, config: AWSIntegrationConfig, secrets: AWSIntegrationSecrets):
        self.config = config
        self.secrets = secrets
        self._session = self._create_session()
        self._sts_client = self._get_client("sts")

    def _create_session(self) -> boto3.Session:
        kwargs = {"region_name": self.config.region}
        
        if self.secrets.access_key_id and self.secrets.secret_access_key:
            kwargs["aws_access_key_id"] = self.secrets.access_key_id
            kwargs["aws_secret_access_key"] = self.secrets.secret_access_key
            if self.secrets.session_token:
                kwargs["aws_session_token"] = self.secrets.session_token

        session = boto3.Session(**kwargs)

        if self.config.role_arn:
            sts = session.client(
                "sts", 
                region_name=self.config.region,
                endpoint_url=self.config.endpoint_overrides.sts if self.config.endpoint_overrides else None,
                verify=self.config.verify_tls
            )
            assume_role_kwargs = {
                "RoleArn": self.config.role_arn,
                "RoleSessionName": "InfraPilotSession",
            }
            if self.config.external_id:
                assume_role_kwargs["ExternalId"] = self.config.external_id

            try:
                assumed_role = sts.assume_role(**assume_role_kwargs)
                credentials = assumed_role["Credentials"]
                kwargs["aws_access_key_id"] = credentials["AccessKeyId"]
                kwargs["aws_secret_access_key"] = credentials["SecretAccessKey"]
                kwargs["aws_session_token"] = credentials["SessionToken"]
                session = boto3.Session(**kwargs)
            except Exception as e:
                self._handle_boto_exception(e, "assume_role")

        return session

    def _get_client(self, service_name: str) -> Any:
        endpoint_url = None
        if self.config.endpoint_overrides:
            endpoint_url = getattr(self.config.endpoint_overrides, service_name, None)
        return self._session.client(
            service_name,
            endpoint_url=endpoint_url,
            verify=self.config.verify_tls
        )

    def _handle_boto_exception(self, e: Exception, operation: str) -> None:
        if isinstance(e, ClientError):
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code in ("AuthFailure", "UnrecognizedClientException", "InvalidClientTokenId"):
                raise AWSAuthenticationError(f"AWS Authentication failed during {operation}: {error_msg}")
            elif error_code in ("AccessDenied", "AccessDeniedException", "UnauthorizedOperation"):
                raise AWSAuthorizationError(f"AWS Access Denied during {operation}: {error_msg}")
            elif error_code in ("InvalidInstanceID.NotFound", "NoSuchBucket", "ResourceNotFoundException"):
                raise AWSResourceNotFoundError(f"AWS Resource Not Found during {operation}: {error_msg}")
            elif error_code in ("Throttling", "ThrottlingException", "RequestLimitExceeded"):
                raise AWSThrottlingError(f"AWS Throttling during {operation}: {error_msg}")
            elif error_code in ("InvalidParameterValue", "ValidationError", "InvalidParameter"):
                raise AWSInvalidParameterError(f"AWS Invalid Parameter during {operation}: {error_msg}")
            else:
                raise AWSAPIError(f"AWS API Error during {operation}: [{error_code}] {error_msg}")
        
        elif isinstance(e, (EndpointConnectionError, ConnectTimeoutError)):
            raise AWSNetworkError(f"AWS Network Connection Error during {operation}: {str(e)}")
        
        elif isinstance(e, BotoCoreError):
            raise AWSAPIError(f"AWS BotoCore Error during {operation}: {str(e)}")
            
        raise AWSProviderError(f"Unexpected AWS error during {operation}: {str(e)}")

    def check_health(self) -> bool:
        try:
            self.get_account_identity()
            return True
        except Exception as e:
            logger.warning(f"AWS health check failed: {e}")
            return False

    def get_account_identity(self) -> Dict[str, str]:
        try:
            resp = self._sts_client.get_caller_identity()
            return {
                "account_id": resp.get("Account"),
                "arn": resp.get("Arn"),
                "user_id": resp.get("UserId"),
            }
        except Exception as e:
            self._handle_boto_exception(e, "get_caller_identity")

    def list_regions(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        try:
            resp = ec2.describe_regions()
            return resp.get("Regions", [])
        except Exception as e:
            self._handle_boto_exception(e, "describe_regions")

    def list_instances(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        instances = []
        paginator = ec2.get_paginator("describe_instances")
        try:
            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    instances.extend(reservation.get("Instances", []))
            return instances
        except Exception as e:
            self._handle_boto_exception(e, "describe_instances")

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        ec2 = self._get_client("ec2")
        try:
            resp = ec2.describe_instances(InstanceIds=[instance_id])
            reservations = resp.get("Reservations", [])
            if not reservations or not reservations[0].get("Instances"):
                raise AWSResourceNotFoundError(f"Instance {instance_id} not found")
            return reservations[0]["Instances"][0]
        except Exception as e:
            self._handle_boto_exception(e, "describe_instances")

    def start_instance(self, instance_id: str) -> None:
        ec2 = self._get_client("ec2")
        try:
            ec2.start_instances(InstanceIds=[instance_id])
        except Exception as e:
            self._handle_boto_exception(e, "start_instances")

    def stop_instance(self, instance_id: str) -> None:
        ec2 = self._get_client("ec2")
        try:
            ec2.stop_instances(InstanceIds=[instance_id])
        except Exception as e:
            self._handle_boto_exception(e, "stop_instances")

    def reboot_instance(self, instance_id: str) -> None:
        ec2 = self._get_client("ec2")
        try:
            ec2.reboot_instances(InstanceIds=[instance_id])
        except Exception as e:
            self._handle_boto_exception(e, "reboot_instances")

    def list_vpcs(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        try:
            resp = ec2.describe_vpcs()
            return resp.get("Vpcs", [])
        except Exception as e:
            self._handle_boto_exception(e, "describe_vpcs")

    def list_subnets(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        try:
            resp = ec2.describe_subnets()
            return resp.get("Subnets", [])
        except Exception as e:
            self._handle_boto_exception(e, "describe_subnets")

    def list_security_groups(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        try:
            resp = ec2.describe_security_groups()
            return resp.get("SecurityGroups", [])
        except Exception as e:
            self._handle_boto_exception(e, "describe_security_groups")

    def list_volumes(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        volumes = []
        paginator = ec2.get_paginator("describe_volumes")
        try:
            for page in paginator.paginate():
                volumes.extend(page.get("Volumes", []))
            return volumes
        except Exception as e:
            self._handle_boto_exception(e, "describe_volumes")

    def list_buckets(self) -> List[Dict[str, Any]]:
        s3 = self._get_client("s3")
        try:
            resp = s3.list_buckets()
            return resp.get("Buckets", [])
        except Exception as e:
            self._handle_boto_exception(e, "list_buckets")

    def terminate_instance(self, instance_id: str) -> None:
        ec2 = self._get_client("ec2")
        try:
            ec2.terminate_instances(InstanceIds=[instance_id])
        except Exception as e:
            self._handle_boto_exception(e, "terminate_instances")

    def list_auto_scaling_groups(self) -> List[Dict[str, Any]]:
        asg = self._get_client("autoscaling")
        groups = []
        paginator = asg.get_paginator("describe_auto_scaling_groups")
        try:
            for page in paginator.paginate():
                groups.extend(page.get("AutoScalingGroups", []))
            return groups
        except Exception as e:
            self._handle_boto_exception(e, "describe_auto_scaling_groups")

    def set_asg_desired_capacity(self, asg_name: str, desired_capacity: int) -> None:
        asg = self._get_client("autoscaling")
        try:
            asg.set_desired_capacity(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=desired_capacity,
                HonorGracePeriod=True
            )
        except Exception as e:
            self._handle_boto_exception(e, "set_desired_capacity")

    def suspend_asg_process(self, asg_name: str) -> None:
        asg = self._get_client("autoscaling")
        try:
            asg.suspend_processes(AutoScalingGroupName=asg_name)
        except Exception as e:
            self._handle_boto_exception(e, "suspend_processes")

    def resume_asg_process(self, asg_name: str) -> None:
        asg = self._get_client("autoscaling")
        try:
            asg.resume_processes(AutoScalingGroupName=asg_name)
        except Exception as e:
            self._handle_boto_exception(e, "resume_processes")

    def list_launch_templates(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        templates = []
        paginator = ec2.get_paginator("describe_launch_templates")
        try:
            for page in paginator.paginate():
                templates.extend(page.get("LaunchTemplates", []))
            return templates
        except Exception as e:
            self._handle_boto_exception(e, "describe_launch_templates")

    def list_route_tables(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        paginator = ec2.get_paginator("describe_route_tables")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("RouteTables", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_route_tables")

    def list_internet_gateways(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        paginator = ec2.get_paginator("describe_internet_gateways")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("InternetGateways", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_internet_gateways")

    def list_nat_gateways(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        paginator = ec2.get_paginator("describe_nat_gateways")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("NatGateways", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_nat_gateways")

    def list_network_interfaces(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        paginator = ec2.get_paginator("describe_network_interfaces")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("NetworkInterfaces", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_network_interfaces")

    def list_snapshots(self) -> List[Dict[str, Any]]:
        ec2 = self._get_client("ec2")
        paginator = ec2.get_paginator("describe_snapshots")
        items = []
        try:
            # Only list owned snapshots by default to avoid huge lists
            for page in paginator.paginate(OwnerIds=['self']):
                items.extend(page.get("Snapshots", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_snapshots")

    def list_load_balancers(self) -> List[Dict[str, Any]]:
        elbv2 = self._get_client("elbv2")
        paginator = elbv2.get_paginator("describe_load_balancers")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("LoadBalancers", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_load_balancers")

    def list_db_instances(self) -> List[Dict[str, Any]]:
        rds = self._get_client("rds")
        paginator = rds.get_paginator("describe_db_instances")
        items = []
        try:
            for page in paginator.paginate():
                items.extend(page.get("DBInstances", []))
            return items
        except Exception as e:
            self._handle_boto_exception(e, "describe_db_instances")
