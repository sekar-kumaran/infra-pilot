import os
import sys
import time
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
WEB_URL = os.getenv("WEB_URL", "http://localhost:3000")

def check_health():
    print("1. Checking API health...")
    r = requests.get(f"http://localhost:8000/health/live")
    if r.status_code != 200:
        print("API is down")
        sys.exit(1)
    print("API is up.")

def run_tests():
    print("Running E2E tests for Phase 1.12...")
    
    # Login
    print("2. Logging in as ADMIN...")
    r = requests.post(f"{API_URL}/auth/login", json={"email": "admin@example.com", "password": "adminpassword"})
    if r.status_code != 200:
        print("Login failed")
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Integration
    print("3. Creating Prometheus Integration...")
    integration_payload = {
        "name": "E2E Prometheus",
        "description": "Test prometheus instance",
        "provider": "prometheus",
        "configuration": {
            "base_url": "http://prometheus-test:9090",
            "timeout_seconds": 5,
            "tls_verify": False,
            "bearer_token": "secret-test-token"
        }
    }
    r = requests.post(f"{API_URL}/integrations", json=integration_payload, headers=headers)
    if r.status_code != 201:
        print(f"Failed to create integration: {r.text}")
        sys.exit(1)
    integration_id = r.json()["id"]
    print(f"Integration created with ID: {integration_id}")
    
    # Validate
    print("4. Validating integration...")
    r = requests.post(f"{API_URL}/integrations/{integration_id}/validate", headers=headers)
    if r.status_code != 202:
        print(f"Validation request failed: {r.text}")
        sys.exit(1)
        
    print("Waiting for validation to complete...")
    time.sleep(5)
    
    r = requests.get(f"{API_URL}/integrations/{integration_id}", headers=headers)
    status = r.json().get("status")
    print(f"Integration status: {status}")
    if status != "HEALTHY":
        print("Integration is not HEALTHY")
        sys.exit(1)
        
    # Discover
    print("5. Running discovery...")
    r = requests.post(f"{API_URL}/integrations/{integration_id}/discover", headers=headers)
    if r.status_code != 202:
        print(f"Discovery request failed: {r.text}")
        sys.exit(1)
        
    print("Waiting for discovery to complete...")
    time.sleep(10)
    
    # Check resources
    r = requests.get(f"{API_URL}/resources", headers=headers)
    resources = [res for res in r.json().get("items", []) if res.get("provider") == "prometheus"]
    print(f"Found {len(resources)} prometheus resources.")
    if len(resources) < 1:
        print("Failed to discover resources.")
        sys.exit(1)
        
    resource_id = resources[0]["id"]
    
    # Query Metrics
    print("6. Querying metrics...")
    r = requests.get(f"{API_URL}/integrations/{integration_id}/metrics", params={"metric_type": "target_up"}, headers=headers)
    if r.status_code != 200:
        print(f"Failed to query metrics: {r.text}")
        sys.exit(1)
    
    print("Metrics query successful.")
    
    print("7. Verifying Celery background task ingested alert...")
    # Wait for celery beat to trigger
    time.sleep(35)
    
    r = requests.get(f"{API_URL}/events", headers=headers)
    events = [e for e in r.json() if e.get("provider") == "prometheus"]
    print(f"Found {len(events)} prometheus events.")
    if len(events) < 1:
        print("Failed to poll events from prometheus.")
        sys.exit(1)
        
    print("PHASE 1.12 E2E VALIDATION SUCCESSFUL")

if __name__ == "__main__":
    check_health()
    run_tests()
