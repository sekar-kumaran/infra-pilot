import os
import time
import requests
import subprocess
from typing import Dict, Any

API_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = None

def login():
    global ADMIN_TOKEN
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": "admin@infrapilot.local", "password": "adminpassword"}
    )
    if response.status_code == 200:
        ADMIN_TOKEN = response.json()["access_token"]
        print("Logged in successfully.")
    else:
        raise Exception(f"Login failed: {response.text}")

def headers():
    return {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}

def setup_k3s_and_get_token():
    print("Running setup_k3s_test_env.sh...")
    script_path = os.path.join(os.path.dirname(__file__), "setup_k3s_test_env.sh")
    subprocess.run(["bash", script_path], check=True)
    
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.e2e")
    token = None
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("E2E_K8S_TOKEN="):
                token = line.strip().split("=")[1]
    return token

def create_kubernetes_integration(token: str):
    res = requests.post(
        f"{API_URL}/integrations",
        headers=headers(),
        json={
            "provider": "kubernetes",
            "name": "E2E K3s Cluster",
            "config": {
                "base_url": "https://kubernetes-test:6443",
                "verify_tls": False
            }
        }
    )
    if res.status_code not in [201, 400]: # 400 if already exists
        raise Exception(f"Failed to create integration: {res.text}")
    
    if res.status_code == 201:
        int_id = res.json()["id"]
        requests.post(
            f"{API_URL}/integrations/{int_id}/secrets",
            headers=headers(),
            json={
                "bearer_token": token
            }
        )
        # Trigger discovery
        requests.post(f"{API_URL}/integrations/{int_id}/sync", headers=headers())
        time.sleep(5)
        print(f"Created K8s integration: {int_id}")
    else:
        print("K8s integration already exists. Updating secrets just in case...")
        ints = requests.get(f"{API_URL}/integrations?provider=kubernetes", headers=headers()).json()
        int_id = ints[0]["id"]
        requests.post(
            f"{API_URL}/integrations/{int_id}/secrets",
            headers=headers(),
            json={
                "bearer_token": token
            }
        )
        requests.post(f"{API_URL}/integrations/{int_id}/sync", headers=headers())
        time.sleep(5)
    return int_id

def create_playbook():
    response = requests.post(
        f"{API_URL}/automation/playbooks",
        headers=headers(),
        json={
            "name": "Phase 1.15 Scale Deployment",
            "description": "Scale K8s Deployment",
            "trigger_type": "MANUAL",
            "version": 1
        }
    )
    if response.status_code != 201:
        raise Exception(f"Failed to create playbook: {response.text}")
    
    playbook_id = response.json()["id"]
    print(f"Created playbook: {playbook_id}")
    
    # Add step (this requires DB manipulation or an API we haven't exposed fully for steps)
    # Actually wait, playbooks create doesn't allow adding steps in one go unless the model accepts it.
    # In earlier tests we bypassed full step creation or assumed it worked if we had an endpoint.
    # Since we didn't implement POST /playbooks/{id}/steps in the snippet, we'll write directly to DB if needed.
    return playbook_id

def trigger_execution(playbook_id: str, resource_id: str):
    response = requests.post(
        f"{API_URL}/automation/executions",
        headers=headers(),
        json={
            "playbook_id": playbook_id,
            "trigger_type": "MANUAL",
            "trigger_source": "API",
            "resource_id": resource_id
        }
    )
    if response.status_code != 201:
        raise Exception(f"Failed to trigger execution: {response.text}")
    
    execution_id = response.json()["execution_id"]
    print(f"Triggered execution: {execution_id}")
    return execution_id

def wait_for_execution(execution_id: str, timeout: int = 120):
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f"{API_URL}/automation/executions/{execution_id}", headers=headers())
        if response.status_code == 200:
            status = response.json().get("status")
            if status in ["SUCCEEDED", "FAILED", "TIMED_OUT"]:
                print(f"Execution finished with status: {status}")
                return response.json()
            elif status == "AWAITING_APPROVAL":
                print("Execution requires approval!")
                return response.json()
        time.sleep(2)
    raise Exception("Execution timed out waiting for completion")

def run():
    print("Starting Phase 1.15 E2E Test...")
    token = setup_k3s_and_get_token()
    login()
    
    create_kubernetes_integration(token)
    
    # Check Provider Status
    res = requests.get(f"{API_URL}/automation/providers/kubernetes/status", headers=headers())
    print(f"Kubernetes Status: {res.json()}")
    
    # Wait for resource discovery to pick up the demo deployment
    print("Waiting for resource discovery...")
    time.sleep(10)
    
    res = requests.get(f"{API_URL}/resources?resource_type=KUBERNETES_DEPLOYMENT", headers=headers())
    resources = res.json()
    demo_deploy = None
    for r in resources:
        if r.get("name") == "demo-nginx":
            demo_deploy = r
            break
            
    if not demo_deploy:
        raise Exception("demo-nginx deployment resource not found! Discovery failed.")
        
    print(f"Found deployment resource: {demo_deploy['id']}")
    
    # Since we don't have an API to add steps, we will inject a step using raw SQL via a script or just test execution validation.
    # Actually, we can inject a step directly into the DB.
    import psycopg2
    import uuid
    conn = psycopg2.connect("postgresql://postgres:postgrespassword@localhost:5432/infrapilot")
    cur = conn.cursor()
    
    playbook_id = create_playbook()
    step_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO playbook_steps (id, playbook_id, step_order, name, action_name, action_type, parameters, risk_level, verification_config) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (step_id, playbook_id, 1, "Scale Nginx", "kubernetes_scale_deployment", "EXECUTE_PROVIDER_ACTION", '{"desired_replicas": 3}', "HIGH", '{"strategy": "kubernetes_verify_scale"}')
    )
    conn.commit()
    conn.close()
    
    exec_id = trigger_execution(playbook_id, demo_deploy['id'])
    
    result = wait_for_execution(exec_id)
    if result.get("status") == "AWAITING_APPROVAL":
        # Find approval
        res = requests.get(f"{API_URL}/automation/approvals", headers=headers())
        approvals = [a for a in res.json() if a["execution_id"] == exec_id]
        if approvals:
            app_id = approvals[0]["id"]
            print(f"Approving execution {app_id}...")
            requests.post(
                f"{API_URL}/automation/approvals/{app_id}/action",
                headers=headers(),
                json={"action": "APPROVE", "reason": "E2E Test"}
            )
            result = wait_for_execution(exec_id)
            
    if result.get("status") != "SUCCEEDED":
        raise Exception(f"Execution failed: {result}")
        
    print("Phase 1.15 E2E Test completed successfully!")

if __name__ == "__main__":
    run()
