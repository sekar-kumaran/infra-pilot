# Phase 1.19 - AWS Operations Expansion & Cross-Provider Operations

## Objective
Expand AWS operations capabilities beyond EC2 and VPC discovery. Introduce broader read-only operations for AWS Auto Scaling Groups (ASG), Route Tables, Internet Gateways, NAT Gateways, Load Balancers, Snapshots, and RDS. Additionally, introduce high-risk mutative automation actions such as `aws_terminate_instance` and `aws_set_asg_desired_capacity` while preserving the strict architectural boundaries and provider-neutral model established in previous phases.

## IAM Least Privilege Required

To enforce least privilege, InfraPilot operations must be separated into two specific IAM roles/policies depending on the use case.

### 1. READ-ONLY IAM POLICY (Discovery & Observability)
This policy enables comprehensive discovery but inherently restricts all mutations.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InfraPilotDiscovery",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeRegions",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeRouteTables",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeNatGateways",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeSnapshots",
        "s3:ListAllMyBuckets",
        "autoscaling:DescribeAutoScalingGroups",
        "elasticloadbalancing:DescribeLoadBalancers",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. OPERATIONS IAM POLICY (Mutative Automations)
If InfraPilot is authorized to execute remediation operations, it needs the following explicit mutative permissions. (These are tightly constrained to explicitly supported operations only, preventing uncontrolled mutations).
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InfraPilotOperations",
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances",
        "ec2:TerminateInstances",
        "autoscaling:SetDesiredCapacity",
        "autoscaling:SuspendProcesses",
        "autoscaling:ResumeProcesses"
      ],
      "Resource": "*"
    }
  ]
}
```

## Files Modified / Created
- `apps/api/app/models/enums.py`: Modified (Added 8 new `ResourceType` enums).
- `apps/api/app/integrations/providers/aws/client.py`: Modified (Appended AWS SDK methods using pagination and robust exception handling).
- `apps/api/app/integrations/providers/aws/resource_mapper.py`: Modified (Added `map_asg`, `map_launch_template`, `map_route_table`, `map_internet_gateway`, `map_nat_gateway`, `map_network_interface`, `map_snapshot`, `map_load_balancer`, `map_db_instance`).
- `apps/api/app/integrations/providers/aws/adapter.py`: Modified (Added new methods to `discover_resources` block and expanded capabilities/resource types).
- `apps/api/app/services/action_registry.py`: Modified (Registered new ASG/DB/Bucket actions and terminating operations).
- `apps/api/app/adapters/automation/aws/executor.py`: Rewritten (Re-engineered to support ASG execution and verifications).
- `apps/api/tests/test_aws_executor.py`: Rewritten (Expanded to test ASG manipulations and Terminations).
- `apps/api/tests/test_aws_security.py`: Rewritten (Expanded security invariant tests for High Risk Actions).
- `scripts/test_real_aws.py`: Modified (Appended execution hooks for testing native boto3 client).
- `scripts/e2e_test_phase_1_19.py`: Created (Copied 1.18 and expanded).

## AWS Resources Supported
- Accounts, Regions, VPCs, Subnets, Security Groups, Instances, Volumes, S3 Buckets.
- Auto Scaling Groups (`CLOUD_AUTO_SCALING_GROUP`)
- Launch Templates (`CLOUD_LAUNCH_TEMPLATE`)
- Route Tables (`CLOUD_ROUTE_TABLE`)
- Internet Gateways (`CLOUD_INTERNET_GATEWAY`)
- NAT Gateways (`CLOUD_NAT_GATEWAY`)
- Network Interfaces (`CLOUD_NETWORK_INTERFACE`)
- EBS Snapshots (`CLOUD_VOLUME_SNAPSHOT`)
- Load Balancers (`CLOUD_LOAD_BALANCER`)
- RDS Instances (`DATABASE_INSTANCE`)

## AWS Capabilities Supported
- `health_check`
- `resource_discovery`
- `resource_read`
- `cloud_compute_management`

## AWS Actions Supported
### Low Risk (No Approval)
- `aws_collect_instance_information`
- `aws_collect_volume_information`
- `aws_collect_network_information`
- `aws_collect_asg_information`
- `aws_collect_database_information`
- `aws_collect_bucket_information`

### High Risk (Requires Approval)
- `aws_start_instance`
- `aws_stop_instance`
- `aws_reboot_instance`
- `aws_terminate_instance` (Requires explicit policy)
- `aws_set_asg_desired_capacity`
- `aws_suspend_asg_process`
- `aws_resume_asg_process`

## Verification Mechanisms
The `AWSAutomationExecutor` natively implements bounded verification routines.
- `aws_verify_instance_running`: Bound polling up to 15 retries ensuring instance `running` state.
- `aws_verify_instance_stopped`: Bound polling up to 15 retries ensuring instance `stopped` state.
- `aws_verify_instance_terminated`: Bound polling up to 15 retries ensuring instance `terminated` state.
- `aws_verify_asg_capacity`: Bound polling up to 15 retries checking ASG array payload mapping against `DesiredCapacity`.

## Security Controls
- **Never expose secrets**: Implemented securely. `Boto3` config uses `AWSIntegrationSecrets`.
- **Target Restrictions**: All mutation actions are locked securely strictly to target `CLOUD_INSTANCE` or `CLOUD_AUTO_SCALING_GROUP` resource enums.
- **Strict Role Assumption**: Supports `RoleArn` and `ExternalId` natively.

## E2E Results
Pytest suite executed correctly with 100% pass (19 successful tests). `e2e_test_phase_1_19.py` execution demonstrated capabilities correctly returning and endpoints functioning natively.

## Architectural Audit
- **No Mocking in Production**: Confirmed. `Boto3` SDK executes unmodified inside `adapter.py` and `client.py`. Tests override endpoints through payload params if `E2E_USE_LOCALSTACK` is true.
- **Provider Neutrality**: Confirmed. `AWSAutomationExecutor` continues to conform precisely to `AutomationExecutor`, passing agnostic payload formats back out.
- **Hierarchy Representation**: Relationships are deterministically preserved by relying on Parent IDs mapping directly back to generic enums (e.g., `aws/subnet/{subnet_id}`, `aws/vpc/{vpc_id}`).

## Recommended Next Phase
With 6 major real providers fully functional, the next priority should be **Phase 1.20 - Incident Routing and Cross-Provider Automations**, testing the scenario where one provider (e.g., Prometheus) orchestrates an action via the Policy Engine through another provider (e.g., Kubernetes or AWS).
