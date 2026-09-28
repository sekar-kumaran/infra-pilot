#!/usr/bin/env python3
import os
import sys
import time
import uuid
import requests
import psycopg2
import json

API_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = None

# Configure E2E to use LocalStack if requested
USE_LOCALSTACK = os.environ.get("E2E_USE_LOCALSTACK", "true").lower() == "true"
LOCALSTACK_URL = os.environ.get("LOCALSTACK_URL", "http://localhost:4566")

def login():
    global ADMIN_TOKEN
    res = requests.post(
        f"{API_URL}/auth/login",
        data={"username": "admin@infrapilot.local", "password": "adminpassword"}
    )
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.text}")
    ADMIN_TOKEN = res.json()["access_token"]
    print("✓ Logged in")

def headers():
    return {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}

def create_aws_integration():
    config = {
        "region": "us-east-1",
        "verify_tls": not USE_LOCALSTACK
    }
    if USE_LOCALSTACK:
        config["endpoint_overrides"] = {
            "ec2": LOCALSTACK_URL,
            "sts": LOCALSTACK_URL,
            "s3": LOCALSTACK_URL
        }
    
    # We must provide some credentials to bypass local boto3 checks
    secrets = {
        "access_key_id": "test",
        "secret_access_key": "test"
    }

    res = requests.post(
        f"{API_URL}/integrations",
        headers=headers(),
        json={
            "provider": "aws",
            "name": "E2E AWS Provider",
            "config": config,
            "secrets": secrets
        }
    )
    
    if res.status_code == 400:
        # Fetch existing
        existing = requests.get(f"{API_URL}/integrations", headers=headers())
        for i in existing.json():
            if i.get("provider") == "aws":
                return i["id"]
    elif res.status_code != 201:
        raise Exception(f"Failed to create integration: {res.text}")
    return res.json()["id"]

def trigger_discovery(integration_id: str):
    res = requests.post(f"{API_URL}/integrations/{integration_id}/discover", headers=headers())
    if res.status_code not in (200, 202):
        print(f"Warning: Discovery {res.status_code} - {res.text}")

def get_resources(resource_type: str):
    res = requests.get(f"{API_URL}/resources?resource_type={resource_type}", headers=headers())
    if res.status_code != 200:
        raise Exception(f"Failed to fetch resources: {res.text}")
    return res.json()

def run():
    print("=== InfraPilot AWS E2E Test (Phase 1.18) ===")
    
    try:
        login()
        int_id = create_aws_integration()
        print(f"✓ AWS Integration ID: {int_id}")
        
        print("Triggering Discovery...")
        trigger_discovery(int_id)
        time.sleep(5)
        
        accounts = get_resources("CLOUD_ACCOUNT")
        print(f"✓ Discovered Accounts: {len(accounts)}")
        
        vpcs = get_resources("CLOUD_VPC")
        print(f"✓ Discovered VPCs: {len(vpcs)}")
        
        # Test capabilities endpoint
        res = requests.get(f"{API_URL}/providers/capabilities", headers=headers())
        caps = res.json()
        aws_cap = next((c for c in caps if c.get("provider") == "aws"), None)
        if aws_cap:
            print("✓ AWS Capabilities registered correctly")
        else:
            raise Exception("AWS Capabilities missing")
            
        print("=== E2E Completed Successfully ===")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
