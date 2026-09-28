from typing import Dict, Any, Optional
from app.models.enums import ResourceType, ResourceStatus, ProviderType
from app.integrations.models import DiscoveredResource

def _get_name_from_tags(tags: list, default: str) -> str:
    if not tags:
        return default
    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value", default)
    return default

def _format_tags(tags: list) -> Dict[str, str]:
    if not tags:
        return {}
    return {tag.get("Key"): tag.get("Value") for tag in tags if tag.get("Key")}

def map_account(identity: Dict[str, str]) -> DiscoveredResource:
    account_id = identity["account_id"]
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/account/{account_id}",
        name=account_id,
        display_name=f"AWS Account {account_id}",
        resource_type=ResourceType.CLOUD_ACCOUNT,
        status=ResourceStatus.ACTIVE,
        metadata={
            "arn": identity.get("arn"),
            "user_id": identity.get("user_id")
        }
    )

def map_region(region: Dict[str, Any], account_id: str) -> DiscoveredResource:
    region_name = region.get("RegionName", "unknown")
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/region/{region_name}",
        name=region_name,
        display_name=f"AWS Region {region_name}",
        resource_type=ResourceType.CLOUD_REGION,
        status=ResourceStatus.ACTIVE,
        metadata={
            "endpoint": region.get("Endpoint"),
            "opt_in_status": region.get("OptInStatus")
        },
        parent_external_id=f"aws/account/{account_id}"
    )

def map_vpc(vpc: Dict[str, Any], region_name: str) -> DiscoveredResource:
    vpc_id = vpc.get("VpcId", "")
    name = _get_name_from_tags(vpc.get("Tags", []), vpc_id)
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/vpc/{vpc_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_VPC,
        status=ResourceStatus.ACTIVE if vpc.get("State") == "available" else ResourceStatus.DEGRADED,
        metadata={
            "cidr_block": vpc.get("CidrBlock"),
            "is_default": vpc.get("IsDefault", False),
            "state": vpc.get("State"),
            "tags": _format_tags(vpc.get("Tags", []))
        },
        parent_external_id=f"aws/region/{region_name}"
    )

def map_subnet(subnet: Dict[str, Any], region_name: str) -> DiscoveredResource:
    subnet_id = subnet.get("SubnetId", "")
    vpc_id = subnet.get("VpcId", "")
    name = _get_name_from_tags(subnet.get("Tags", []), subnet_id)
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/subnet/{subnet_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_SUBNET,
        status=ResourceStatus.ACTIVE if subnet.get("State") == "available" else ResourceStatus.DEGRADED,
        metadata={
            "vpc_id": vpc_id,
            "cidr_block": subnet.get("CidrBlock"),
            "availability_zone": subnet.get("AvailabilityZone"),
            "available_ip_address_count": subnet.get("AvailableIpAddressCount"),
            "state": subnet.get("State"),
            "tags": _format_tags(subnet.get("Tags", []))
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_security_group(sg: Dict[str, Any], region_name: str) -> DiscoveredResource:
    group_id = sg.get("GroupId", "")
    vpc_id = sg.get("VpcId", "")
    name = sg.get("GroupName", group_id)
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/security-group/{group_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_SECURITY_GROUP,
        status=ResourceStatus.ACTIVE,
        metadata={
            "vpc_id": vpc_id,
            "description": sg.get("Description"),
            "tags": _format_tags(sg.get("Tags", []))
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_instance(instance: Dict[str, Any], region_name: str) -> DiscoveredResource:
    instance_id = instance.get("InstanceId", "")
    subnet_id = instance.get("SubnetId", "")
    name = _get_name_from_tags(instance.get("Tags", []), instance_id)
    
    state_name = instance.get("State", {}).get("Name", "unknown")
    if state_name == "running":
        status = ResourceStatus.ACTIVE
    elif state_name in ("stopped", "terminated", "shutting-down"):
        status = ResourceStatus.INACTIVE
    else:
        status = ResourceStatus.DEGRADED

    metadata = {
        "instance_id": instance_id,
        "instance_type": instance.get("InstanceType"),
        "state": state_name,
        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
        "private_ip": instance.get("PrivateIpAddress"),
        "public_ip": instance.get("PublicIpAddress"),
        "subnet_id": subnet_id,
        "vpc_id": instance.get("VpcId"),
        "security_group_ids": [sg.get("GroupId") for sg in instance.get("SecurityGroups", [])],
        "launch_time": instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None,
        "tags": _format_tags(instance.get("Tags", []))
    }
    
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/instance/{instance_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_INSTANCE,
        status=status,
        metadata=metadata,
        parent_external_id=f"aws/subnet/{subnet_id}" if subnet_id else f"aws/region/{region_name}"
    )

def map_volume(volume: Dict[str, Any], region_name: str) -> DiscoveredResource:
    volume_id = volume.get("VolumeId", "")
    name = _get_name_from_tags(volume.get("Tags", []), volume_id)
    
    state = volume.get("State", "unknown")
    if state == "in-use":
        status = ResourceStatus.ACTIVE
    elif state == "available":
        status = ResourceStatus.INACTIVE
    else:
        status = ResourceStatus.DEGRADED

    metadata = {
        "volume_id": volume_id,
        "size_gb": volume.get("Size"),
        "volume_type": volume.get("VolumeType"),
        "state": state,
        "availability_zone": volume.get("AvailabilityZone"),
        "encrypted": volume.get("Encrypted"),
        "tags": _format_tags(volume.get("Tags", []))
    }

    attachments = volume.get("Attachments", [])
    parent_id = f"aws/region/{region_name}"
    if attachments:
        instance_id = attachments[0].get("InstanceId")
        if instance_id:
            parent_id = f"aws/instance/{instance_id}"

    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/volume/{volume_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_VOLUME,
        status=status,
        metadata=metadata,
        parent_external_id=parent_id
    )

def map_bucket(bucket: Dict[str, Any], account_id: str) -> DiscoveredResource:
    bucket_name = bucket.get("Name", "")
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/bucket/{bucket_name}",
        name=bucket_name,
        display_name=bucket_name,
        resource_type=ResourceType.CLOUD_BUCKET,
        status=ResourceStatus.ACTIVE,
        metadata={
            "creation_date": bucket.get("CreationDate").isoformat() if bucket.get("CreationDate") else None
        },
        parent_external_id=f"aws/account/{account_id}"
    )

def map_asg(asg: Dict[str, Any], region_name: str) -> DiscoveredResource:
    asg_name = asg.get("AutoScalingGroupName", "")
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/asg/{asg_name}",
        name=asg_name,
        display_name=asg_name,
        resource_type=ResourceType.CLOUD_AUTO_SCALING_GROUP,
        status=ResourceStatus.ACTIVE,
        metadata={
            "min_size": asg.get("MinSize"),
            "max_size": asg.get("MaxSize"),
            "desired_capacity": asg.get("DesiredCapacity"),
            "vpc_zone_identifier": asg.get("VPCZoneIdentifier"),
            "tags": _format_tags(asg.get("Tags", []))
        },
        parent_external_id=f"aws/region/{region_name}"
    )

def map_launch_template(lt: Dict[str, Any], region_name: str) -> DiscoveredResource:
    lt_id = lt.get("LaunchTemplateId", "")
    lt_name = lt.get("LaunchTemplateName", lt_id)
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/launch-template/{lt_id}",
        name=lt_name,
        display_name=lt_name,
        resource_type=ResourceType.CLOUD_LAUNCH_TEMPLATE,
        status=ResourceStatus.ACTIVE,
        metadata={
            "default_version": lt.get("DefaultVersionNumber"),
            "latest_version": lt.get("LatestVersionNumber"),
            "tags": _format_tags(lt.get("Tags", []))
        },
        parent_external_id=f"aws/region/{region_name}"
    )

def map_route_table(rt: Dict[str, Any], region_name: str) -> DiscoveredResource:
    rt_id = rt.get("RouteTableId", "")
    vpc_id = rt.get("VpcId", "")
    name = _get_name_from_tags(rt.get("Tags", []), rt_id)
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/route-table/{rt_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_ROUTE_TABLE,
        status=ResourceStatus.ACTIVE,
        metadata={
            "vpc_id": vpc_id,
            "tags": _format_tags(rt.get("Tags", []))
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_internet_gateway(igw: Dict[str, Any], region_name: str) -> DiscoveredResource:
    igw_id = igw.get("InternetGatewayId", "")
    name = _get_name_from_tags(igw.get("Tags", []), igw_id)
    vpc_id = None
    if igw.get("Attachments"):
        vpc_id = igw["Attachments"][0].get("VpcId")
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/internet-gateway/{igw_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_INTERNET_GATEWAY,
        status=ResourceStatus.ACTIVE,
        metadata={
            "vpc_id": vpc_id,
            "tags": _format_tags(igw.get("Tags", []))
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_nat_gateway(nat: Dict[str, Any], region_name: str) -> DiscoveredResource:
    nat_id = nat.get("NatGatewayId", "")
    name = _get_name_from_tags(nat.get("Tags", []), nat_id)
    vpc_id = nat.get("VpcId")
    state = nat.get("State", "unknown")
    status = ResourceStatus.ACTIVE if state == "available" else ResourceStatus.DEGRADED
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/nat-gateway/{nat_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_NAT_GATEWAY,
        status=status,
        metadata={
            "vpc_id": vpc_id,
            "subnet_id": nat.get("SubnetId"),
            "state": state,
            "tags": _format_tags(nat.get("Tags", []))
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_network_interface(eni: Dict[str, Any], region_name: str) -> DiscoveredResource:
    eni_id = eni.get("NetworkInterfaceId", "")
    name = _get_name_from_tags(eni.get("TagSet", []), eni_id)
    subnet_id = eni.get("SubnetId")
    state = eni.get("Status", "unknown")
    status = ResourceStatus.ACTIVE if state == "in-use" else ResourceStatus.INACTIVE
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/network-interface/{eni_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_NETWORK_INTERFACE,
        status=status,
        metadata={
            "vpc_id": eni.get("VpcId"),
            "subnet_id": subnet_id,
            "private_ip": eni.get("PrivateIpAddress"),
            "mac_address": eni.get("MacAddress"),
            "status": state,
            "tags": _format_tags(eni.get("TagSet", []))
        },
        parent_external_id=f"aws/subnet/{subnet_id}" if subnet_id else f"aws/region/{region_name}"
    )

def map_snapshot(snap: Dict[str, Any], region_name: str) -> DiscoveredResource:
    snap_id = snap.get("SnapshotId", "")
    name = _get_name_from_tags(snap.get("Tags", []), snap_id)
    state = snap.get("State", "unknown")
    status = ResourceStatus.ACTIVE if state == "completed" else ResourceStatus.DEGRADED
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/snapshot/{snap_id}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_VOLUME_SNAPSHOT,
        status=status,
        metadata={
            "volume_id": snap.get("VolumeId"),
            "volume_size": snap.get("VolumeSize"),
            "state": state,
            "encrypted": snap.get("Encrypted"),
            "tags": _format_tags(snap.get("Tags", []))
        },
        parent_external_id=f"aws/region/{region_name}"
    )

def map_load_balancer(lb: Dict[str, Any], region_name: str) -> DiscoveredResource:
    lb_arn = lb.get("LoadBalancerArn", "")
    name = lb.get("LoadBalancerName", lb_arn.split("/")[-1] if lb_arn else "")
    vpc_id = lb.get("VpcId")
    state = lb.get("State", {}).get("Code", "unknown")
    status = ResourceStatus.ACTIVE if state == "active" else ResourceStatus.DEGRADED
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/load-balancer/{name}",
        name=name,
        display_name=name,
        resource_type=ResourceType.CLOUD_LOAD_BALANCER,
        status=status,
        metadata={
            "arn": lb_arn,
            "scheme": lb.get("Scheme"),
            "type": lb.get("Type"),
            "vpc_id": vpc_id,
            "state": state
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )

def map_db_instance(db: Dict[str, Any], region_name: str) -> DiscoveredResource:
    db_id = db.get("DBInstanceIdentifier", "")
    state = db.get("DBInstanceStatus", "unknown")
    status = ResourceStatus.ACTIVE if state == "available" else ResourceStatus.DEGRADED
    vpc_id = None
    if db.get("DBSubnetGroup"):
        vpc_id = db["DBSubnetGroup"].get("VpcId")
        
    return DiscoveredResource(
        provider=ProviderType.AWS,
        external_id=f"aws/rds/{db_id}",
        name=db_id,
        display_name=db_id,
        resource_type=ResourceType.DATABASE_INSTANCE,
        status=status,
        metadata={
            "engine": db.get("Engine"),
            "engine_version": db.get("EngineVersion"),
            "instance_class": db.get("DBInstanceClass"),
            "status": state,
            "allocated_storage": db.get("AllocatedStorage"),
            "multi_az": db.get("MultiAZ"),
            "vpc_id": vpc_id
        },
        parent_external_id=f"aws/vpc/{vpc_id}" if vpc_id else f"aws/region/{region_name}"
    )
