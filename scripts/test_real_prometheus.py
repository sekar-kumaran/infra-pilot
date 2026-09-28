import os
import sys
import requests
import time

def run_real_provider_test():
    real_url = os.getenv("PROMETHEUS_REAL_URL")
    real_token = os.getenv("PROMETHEUS_REAL_TOKEN", "")

    if not real_url:
        print("SKIP: PROMETHEUS_REAL_URL environment variable not set. Skipping real-provider acceptance test.")
        sys.exit(0)

    print(f"Running Real Prometheus Acceptance Test against: {real_url}")
    
    API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
    
    print("1. Logging in as ADMIN...")
    r = requests.post(f"{API_URL}/auth/login", json={"email": "admin@example.com", "password": "adminpassword"})
    if r.status_code != 200:
        print("Login failed")
        sys.exit(1)
    
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("2. Creating Real Prometheus Integration...")
    integration_payload = {
        "name": "Production Prometheus (Test)",
        "description": "Real prometheus instance for acceptance testing",
        "provider": "prometheus",
        "configuration": {
            "base_url": real_url,
            "timeout_seconds": 10,
            "tls_verify": False,
            "bearer_token": real_token
        }
    }
    r = requests.post(f"{API_URL}/integrations/", json=integration_payload, headers=headers)
    if r.status_code != 201:
        print(f"Failed to create integration: {r.text}")
        sys.exit(1)
    
    integration_id = r.json()["id"]
    print(f"Integration created with ID: {integration_id}")

    print("3. Validating integration connection...")
    r = requests.post(f"{API_URL}/integrations/{integration_id}/validate", headers=headers)
    
    print("Waiting for validation...")
    for _ in range(5):
        time.sleep(2)
        r = requests.get(f"{API_URL}/integrations/{integration_id}", headers=headers)
        if r.json()["status"] == "HEALTHY":
            break
            
    if r.json()["status"] != "HEALTHY":
        print(f"Validation failed. Status: {r.json()['status']}")
        sys.exit(1)
        
    print("Integration connection SUCCESSFUL.")

    print("4. Running Resource Discovery...")
    r = requests.post(f"{API_URL}/integrations/{integration_id}/discover", headers=headers)
    
    print("Waiting for discovery...")
    time.sleep(5)
    
    r = requests.get(f"{API_URL}/resources", headers=headers)
    resources = [res for res in r.json().get("items", []) if res.get("provider") == "prometheus"]
    print(f"Discovered {len(resources)} real resources from {real_url}.")
    
    print("5. Querying Metrics...")
    r = requests.get(f"{API_URL}/integrations/{integration_id}/metrics?metric_type=target_up", headers=headers)
    if r.status_code != 200:
        print(f"Metrics query failed: {r.text}")
        sys.exit(1)
        
    metrics_data = r.json()
    result_type = metrics_data.get("resultType")
    results = metrics_data.get("result", [])
    print(f"Metrics query successful! Result type: {result_type}. Found {len(results)} metrics.")

    print("\n==============================================")
    print("REAL PROMETHEUS ACCEPTANCE TEST PASSED!")
    print("==============================================")


if __name__ == "__main__":
    run_real_provider_test()
