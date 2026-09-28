import logging
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from app.models.enums import ProviderType, ResourceType
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import DiscoveredResource, IntegrationCapability
from app.integrations.providers.aws.schemas import AWSIntegrationConfig, AWSIntegrationSecrets
from app.integrations.providers.aws.client import AWSClient
from app.integrations.providers.aws.capabilities import AWS_CAPABILITIES
from app.integrations.providers.aws.errors import AWSProviderError
from app.integrations.providers.aws.resource_mapper import (
    map_account,
    map_region,
    map_vpc,
    map_subnet,
    map_security_group,
    map_instance,
    map_volume,
    map_bucket,
    map_asg,
    map_launch_template,
    map_route_table,
    map_internet_gateway,
    map_nat_gateway,
    map_network_interface,
    map_snapshot,
    map_load_balancer,
    map_db_instance,
)

from app.integrations.capabilities import ProviderCapabilityRegistryEntry

logger = logging.getLogger(__name__)

class AWSAdapter(ProviderAdapter):
    """
    AWS Provider Adapter for discovering and interacting with AWS resources.
    """

    def provider_type(self) -> ProviderType:
        return ProviderType.AWS

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.AWS,
            display_name="AWS",
            version="1.0",
            capabilities=["health_check", "resource_discovery", "resource_read", "cloud_compute_management"],
            resources=[
                ResourceType.CLOUD_ACCOUNT,
                ResourceType.CLOUD_REGION,
                ResourceType.CLOUD_VPC,
                ResourceType.CLOUD_SUBNET,
                ResourceType.CLOUD_SECURITY_GROUP,
                ResourceType.CLOUD_INSTANCE,
                ResourceType.CLOUD_VOLUME,
                ResourceType.CLOUD_BUCKET,
                ResourceType.CLOUD_AUTO_SCALING_GROUP,
                ResourceType.CLOUD_LAUNCH_TEMPLATE,
                ResourceType.CLOUD_ROUTE_TABLE,
                ResourceType.CLOUD_INTERNET_GATEWAY,
                ResourceType.CLOUD_NAT_GATEWAY,
                ResourceType.CLOUD_NETWORK_INTERFACE,
                ResourceType.CLOUD_VOLUME_SNAPSHOT,
                ResourceType.CLOUD_LOAD_BALANCER,
                ResourceType.DATABASE_INSTANCE,
            ],
            read_operations=[
                "aws_collect_instance_information", 
                "aws_collect_volume_information", 
                "aws_collect_network_information", 
                "aws_collect_asg_information",
                "aws_collect_database_information",
                "aws_collect_bucket_information"
            ],
            mutation_operations=[
                "aws_start_instance", 
                "aws_stop_instance", 
                "aws_reboot_instance",
                "aws_terminate_instance",
                "aws_set_asg_desired_capacity",
                "aws_suspend_asg_process",
                "aws_resume_asg_process"
            ]
        )

    def get_capabilities(self) -> IntegrationCapability:
        return AWS_CAPABILITIES

    def validate_config(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            AWSIntegrationConfig(**config)
            AWSIntegrationSecrets(**secrets)
            return True
        except ValidationError as e:
            logger.warning(f"AWS config validation failed: {e}")
            return False

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> AWSClient:
        conf = AWSIntegrationConfig(**config)
        sec = AWSIntegrationSecrets(**secrets)
        return AWSClient(config=conf, secrets=sec)

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        return self.check_health(config, secrets)

    def check_health(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        client = self._get_client(config, secrets)
        return client.check_health()

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        resources: List[DiscoveredResource] = []

        try:
            # 1. Identity / Account
            identity = client.get_account_identity()
            account_resource = map_account(identity)
            resources.append(account_resource)
            account_id = identity["account_id"]

            # 2. Regions
            regions = client.list_regions()
            for r in regions:
                resources.append(map_region(r, account_id))
            
            # The client is bound to config.region. We'll map resources to config.region.
            current_region = client.config.region

            # 3. VPCs
            vpcs = client.list_vpcs()
            for vpc in vpcs:
                resources.append(map_vpc(vpc, current_region))

            # 4. Subnets
            subnets = client.list_subnets()
            for sn in subnets:
                resources.append(map_subnet(sn, current_region))

            # 5. Security Groups
            sgs = client.list_security_groups()
            for sg in sgs:
                resources.append(map_security_group(sg, current_region))

            # 6. EC2 Instances
            instances = client.list_instances()
            for inst in instances:
                resources.append(map_instance(inst, current_region))

            # 7. EBS Volumes
            volumes = client.list_volumes()
            for vol in volumes:
                resources.append(map_volume(vol, current_region))

            # 8. S3 Buckets
            buckets = client.list_buckets()
            for bucket in buckets:
                resources.append(map_bucket(bucket, account_id))

            # 9. Auto Scaling Groups
            asgs = client.list_auto_scaling_groups()
            for asg in asgs:
                resources.append(map_asg(asg, current_region))

            # 10. Launch Templates
            lts = client.list_launch_templates()
            for lt in lts:
                resources.append(map_launch_template(lt, current_region))

            # 11. Route Tables
            rts = client.list_route_tables()
            for rt in rts:
                resources.append(map_route_table(rt, current_region))

            # 12. Internet Gateways
            igws = client.list_internet_gateways()
            for igw in igws:
                resources.append(map_internet_gateway(igw, current_region))

            # 13. NAT Gateways
            nats = client.list_nat_gateways()
            for nat in nats:
                resources.append(map_nat_gateway(nat, current_region))

            # 14. Network Interfaces
            enis = client.list_network_interfaces()
            for eni in enis:
                resources.append(map_network_interface(eni, current_region))

            # 15. EBS Snapshots
            snaps = client.list_snapshots()
            for snap in snaps:
                resources.append(map_snapshot(snap, current_region))

            # 16. Load Balancers
            lbs = client.list_load_balancers()
            for lb in lbs:
                resources.append(map_load_balancer(lb, current_region))

            # 17. RDS DB Instances
            dbs = client.list_db_instances()
            for db in dbs:
                resources.append(map_db_instance(db, current_region))

        except AWSProviderError as e:
            logger.error(f"AWS discovery error: {e}")
            # Reraise so the sync task marks discovery as failed if it's fatal
            raise

        return resources

    def read_resource(self, config: Dict[str, Any], secrets: Dict[str, Any], external_id: str) -> Optional[Dict[str, Any]]:
        client = self._get_client(config, secrets)
        parts = external_id.split("/")
        
        # e.g., aws/instance/i-12345
        if len(parts) >= 3 and parts[1] == "instance":
            instance_id = parts[2]
            try:
                inst = client.get_instance(instance_id)
                # Convert back to mapped representation to get consistent metadata
                mapped = map_instance(inst, client.config.region)
                return mapped.metadata
            except AWSProviderError:
                return None
        return None
