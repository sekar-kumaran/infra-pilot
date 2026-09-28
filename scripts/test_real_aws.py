#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.integrations.providers.aws.client import AWSClient
from app.integrations.providers.aws.schemas import AWSIntegrationConfig, AWSIntegrationSecrets, AWSEndpointOverrides

def run():
    region = os.environ.get("AWS_REAL_REGION", "us-east-1")
    role_arn = os.environ.get("AWS_REAL_ROLE_ARN")
    external_id = os.environ.get("AWS_REAL_EXTERNAL_ID")
    allow_mutation = os.environ.get("AWS_REAL_ALLOW_MUTATION", "false").lower() == "true"
    target_instance = os.environ.get("AWS_REAL_TARGET_INSTANCE")

    # If LocalStack is running, configure endpoint override
    # Only for testing, not in production path
    localstack_url = os.environ.get("LOCALSTACK_URL")
    overrides = None
    if localstack_url:
        overrides = AWSEndpointOverrides(
            ec2=localstack_url,
            sts=localstack_url,
            s3=localstack_url
        )

    config = AWSIntegrationConfig(
        region=region,
        role_arn=role_arn,
        external_id=external_id,
        verify_tls=not localstack_url,
        endpoint_overrides=overrides
    )
    
    # Resolves via standard boto3 chain (env vars, ~/.aws/credentials) unless explicitly passed
    secrets = AWSIntegrationSecrets(
        access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        session_token=os.environ.get("AWS_SESSION_TOKEN")
    )

    client = AWSClient(config=config, secrets=secrets)

    print("=== InfraPilot AWS Provider Acceptance Test ===")
    
    try:
        identity = client.get_account_identity()
        print(f"✓ Connected. Account: {identity['account_id']}, ARN: {identity['arn']}")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)

    try:
        regions = client.list_regions()
        print(f"✓ Discovered {len(regions)} regions")
    except Exception as e:
        print(f"✗ Failed to list regions: {e}")

    try:
        vpcs = client.list_vpcs()
        print(f"✓ Discovered {len(vpcs)} VPCs")
    except Exception as e:
        print(f"✗ Failed to list vpcs: {e}")

    try:
        subnets = client.list_subnets()
        print(f"✓ Discovered {len(subnets)} subnets")
    except Exception as e:
        print(f"✗ Failed to list subnets: {e}")

    try:
        instances = client.list_instances()
        print(f"✓ Discovered {len(instances)} instances")
        for i in instances[:3]:
            print(f"  - {i.get('InstanceId')} ({i.get('State', {}).get('Name')})")
    except Exception as e:
        print(f"✗ Failed to list instances: {e}")

    try:
        volumes = client.list_volumes()
        print(f"✓ Discovered {len(volumes)} volumes")
    except Exception as e:
        print(f"✗ Failed to list volumes: {e}")

    try:
        buckets = client.list_buckets()
        print(f"✓ Discovered {len(buckets)} S3 buckets")
    except Exception as e:
        print(f"✗ Failed to list buckets: {e}")

    try:
        asgs = client.list_auto_scaling_groups()
        print(f"✓ Discovered {len(asgs)} ASGs")
    except Exception as e:
        print(f"✗ Failed to list ASGs: {e}")

    try:
        lbs = client.list_load_balancers()
        print(f"✓ Discovered {len(lbs)} Load Balancers")
    except Exception as e:
        print(f"✗ Failed to list Load Balancers: {e}")

    try:
        dbs = client.list_db_instances()
        print(f"✓ Discovered {len(dbs)} RDS instances")
    except Exception as e:
        print(f"✗ Failed to list RDS instances: {e}")

    if allow_mutation:
        if not target_instance:
            print("✗ Mutation requested but AWS_REAL_TARGET_INSTANCE not set")
            sys.exit(1)
            
        print(f"=== Testing Mutation on {target_instance} ===")
        try:
            print("Stopping instance...")
            client.stop_instance(target_instance)
            time.sleep(5)
            print("Starting instance...")
            client.start_instance(target_instance)
            time.sleep(5)
            inst = client.get_instance(target_instance)
            print(f"✓ Instance state is now: {inst.get('State', {}).get('Name')}")
        except Exception as e:
            print(f"✗ Mutation failed: {e}")
            sys.exit(1)
    else:
        print("=== Read Only completed. Mutation requires AWS_REAL_ALLOW_MUTATION=true ===")

if __name__ == "__main__":
    run()
