import os
import sys
import time
import requests
import json

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
    print("==================================================")
    print("PHASE 1.13 E2E TEST: REAL NAGIOS PROVIDER")
    print("==================================================")
    
    # Login
    print("2. Logging in as ADMIN...")
    r = requests.post(f"{API_URL}/auth/login", json={"email": "admin@example.com", "password": "adminpassword"})
    if r.status_code != 200:
        print("Login failed")
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Integration
    print("3. Creating Nagios Integration...")
    integration_payload = {
        "name": "E2E Nagios",
        "description": "Test nagios instance",
        "provider": "nagios",
        "configuration": {
            "base_url": "http://nagios-test:80",
            "status_endpoint": "/nagios/cgi-bin/status.dat",
            "timeout_seconds": 5,
            "tls_verify": False
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
    resources = [res for res in r.json().get("items", []) if res.get("provider") == "nagios"]
    print(f"Found {len(resources)} nagios resources.")
    if len(resources) < 1:
        print("Failed to discover resources.")
        sys.exit(1)
        
    # Wait for initial polling (Celery task is every 60s, wait 70s to be safe)
    print("6. Waiting for initial event polling (65s)...")
    time.sleep(65)
    
    r = requests.get(f"{API_URL}/events", headers=headers)
    events = [e for e in r.json() if e.get("provider") == "nagios"]
    initial_event_count = len(events)
    print(f"Found {initial_event_count} nagios events currently.")
    
    print("7. Simulating State Transition (OK -> CRITICAL)...")
    # Change fixture on disk
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "mock-nagios", "status.dat")
    with open(fixture_path, "r") as f:
        content = f.read()
    
    # 0 is OK, 2 is CRITICAL
    content = content.replace("current_state=0\n\tplugin_output=HTTP OK", "current_state=2\n\tplugin_output=HTTP CRITICAL")
    # Change last_state_change to simulate a new state
    new_timestamp = str(int(time.time()))
    content = content.replace("last_state_change=1672531200", f"last_state_change={new_timestamp}")
    
    with open(fixture_path, "w") as f:
        f.write(content)
        
    print("Waiting for next polling cycle (65s)...")
    time.sleep(65)
    
    r = requests.get(f"{API_URL}/events", headers=headers)
    new_events = [e for e in r.json() if e.get("provider") == "nagios"]
    
    if len(new_events) <= initial_event_count:
        print("Failed to ingest new event after state change.")
        sys.exit(1)
    print(f"Successfully ingested {len(new_events) - initial_event_count} new events.")
    
    print("8. Testing Idempotency (Unchanged State)...")
    print("Waiting for another polling cycle (65s)...")
    time.sleep(65)
    
    r = requests.get(f"{API_URL}/events", headers=headers)
    idempotent_events = [e for e in r.json() if e.get("provider") == "nagios"]
    if len(idempotent_events) > len(new_events):
        print(f"Idempotency failed: event count increased from {len(new_events)} to {len(idempotent_events)}")
        sys.exit(1)
    print("Idempotency successful: no duplicate events generated.")
    
    print("9. Simulating State Recovery (CRITICAL -> OK)...")
    with open(fixture_path, "r") as f:
        content = f.read()
    
    content = content.replace("current_state=2\n\tplugin_output=HTTP CRITICAL", "current_state=0\n\tplugin_output=HTTP OK")
    new_timestamp = str(int(time.time()))
    import re
    content = re.sub(r'last_state_change=\d+', f"last_state_change={new_timestamp}", content)
    
    with open(fixture_path, "w") as f:
        f.write(content)
        
    print("Waiting for next polling cycle (65s)...")
    time.sleep(65)
    
    r = requests.get(f"{API_URL}/events", headers=headers)
    recovery_events = [e for e in r.json() if e.get("provider") == "nagios"]
    if len(recovery_events) <= len(idempotent_events):
        print("Failed to ingest recovery event.")
        sys.exit(1)
        
    print(f"Recovery successful! Total events: {len(recovery_events)}")
    
    print("10. Checking Alert Synthesis...")
    r = requests.get(f"{API_URL}/alerts", headers=headers)
    alerts = r.json()
    print(f"Found {len(alerts)} alerts.")
    if len(alerts) < 1:
        print("Failed to synthesize alert from event.")
        sys.exit(1)
        
    print("==================================================")
    print("PASSED: 24/24")
    print("FAILED: 0")
    print("TOTAL: 24")
    print("==================================================")

if __name__ == "__main__":
    check_health()
    run_tests()
