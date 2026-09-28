import os
import sys
import time
from urllib.parse import urlparse

from app.integrations.providers.nagios.adapter import NagiosAdapter
from app.integrations.providers.nagios.client import NagiosClient

def main():
    print("==================================================")
    print("REAL NAGIOS PROVIDER ACCEPTANCE TEST")
    print("==================================================")
    
    url = os.environ.get("NAGIOS_REAL_URL")
    endpoint = os.environ.get("NAGIOS_REAL_STATUS_ENDPOINT", "/nagios/cgi-bin/status.dat")
    username = os.environ.get("NAGIOS_REAL_USERNAME")
    password = os.environ.get("NAGIOS_REAL_PASSWORD")
    
    if not url:
        print("ERROR: Missing required environment variable NAGIOS_REAL_URL")
        print("Please export credentials for a real Nagios instance to verify acceptance criteria.")
        print("Never fall back to the nagios-test fixture for this script.")
        sys.exit(1)
        
    print(f"Targeting: {url}{endpoint}")
    print(f"Authentication: {'Configured' if username else 'None'}")
    
    config = {
        "base_url": url,
        "status_endpoint": endpoint,
        "timeout_seconds": 10,
        "tls_verify": False
    }
    secrets = {}
    if username and password:
        secrets = {
            "username": username,
            "password": password
        }
        
    adapter = NagiosAdapter()
    
    print("\n1. Testing Connection Validation...")
    try:
        adapter.validate_connection(config, secrets)
        print("✓ Validation successful (HTTP reachable, auth succeeded, parser succeeded)")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)
        
    print("\n2. Testing Resource Discovery...")
    try:
        resources = adapter.discover_resources(config, secrets)
        hosts = [r for r in resources if r.resource_type == "HOST"]
        services = [r for r in resources if r.resource_type == "SERVICE"]
        
        print(f"✓ Discovery successful")
        print(f"  - Found {len(hosts)} hosts")
        print(f"  - Found {len(services)} services")
        
        if len(hosts) > 0:
            print(f"  - Example Host: {hosts[0].external_id} ({hosts[0].status})")
        if len(services) > 0:
            print(f"  - Example Service: {services[0].external_id} ({services[0].status})")
            
    except Exception as e:
        print(f"✗ Discovery failed: {e}")
        sys.exit(1)
        
    print("\n3. Testing Idempotency (Repeat Discovery)...")
    try:
        resources_2 = adapter.discover_resources(config, secrets)
        
        set_1 = {r.external_id for r in resources}
        set_2 = {r.external_id for r in resources_2}
        
        if set_1 == set_2:
            print("✓ Idempotency verified: Both discoveries returned identical deterministic external IDs.")
        else:
            print("✗ Idempotency failed: External IDs changed between discoveries.")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Repeated discovery failed: {e}")
        sys.exit(1)

    print("\n✓ ALL REAL NAGIOS ACCEPTANCE TESTS PASSED")

if __name__ == "__main__":
    main()
