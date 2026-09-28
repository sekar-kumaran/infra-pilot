import os
import time
import requests
import psycopg2
import uuid
import subprocess

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

def setup_integrations():
    # Ansible
    res = requests.post(
        f"{API_URL}/integrations",
        headers=headers(),
        json={
            "provider": "ansible",
            "name": "Local Ansible",
            "config": {
                "inventory_path": "/app/ansible/inventory/hosts.yml"
            }
        }
    )
    print("Ansible Integration setup response:", res.status_code)
    
    # Get Kubernetes token
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.e2e")
    token = None
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("E2E_K8S_TOKEN="):
                    token = line.strip().split("=")[1]
    
    if not token:
        print("Warning: E2E_K8S_TOKEN not found, skipping Kubernetes real cluster integration")
        return
        
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
    if res.status_code == 201:
        int_id = res.json()["id"]
        requests.post(
            f"{API_URL}/integrations/{int_id}/secrets",
            headers=headers(),
            json={
                "bearer_token": token
            }
        )
    print("Kubernetes Integration setup response:", res.status_code)

def create_playbook(name):
    res = requests.post(
        f"{API_URL}/automation/playbooks",
        headers=headers(),
        json={
            "name": name,
            "description": "E2E Test Playbook",
            "trigger_type": "MANUAL"
        }
    )
    if res.status_code != 201:
        raise Exception(f"Failed to create playbook: {res.text}")
    return res.json()["id"]

def trigger_execution(playbook_id, resource_id=None):
    payload = {
        "playbook_id": playbook_id,
        "trigger_type": "MANUAL",
        "trigger_source": "API"
    }
    if resource_id:
        payload["resource_id"] = resource_id
        
    response = requests.post(
        f"{API_URL}/automation/executions",
        headers=headers(),
        json=payload
    )
    if response.status_code != 201:
        raise Exception(f"Failed to trigger execution: {response.text}")
    return response.json()["execution_id"]

def run():
    print("Starting Phase 1.16 Cross-Provider E2E Test...")
    login()
    setup_integrations()
    
    # Wait for discovery
    time.sleep(5)
    
    conn = psycopg2.connect("postgresql://postgres:postgrespassword@localhost:5432/infrapilot")
    cur = conn.cursor()
    
    # Create Playbook A (Ansible)
    pb_a = create_playbook("Ansible Service Restart")
    cur.execute(
        "INSERT INTO playbook_steps (id, playbook_id, step_order, name, action_name, action_type, parameters, risk_level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), pb_a, 1, "Restart Service", "restart_service", "EXECUTE_PROVIDER_ACTION", '{"service_name": "nginx"}', "HIGH")
    )
    
    # Create Playbook B (Kubernetes)
    pb_b = create_playbook("Kubernetes Pause Deployment")
    cur.execute(
        "INSERT INTO playbook_steps (id, playbook_id, step_order, name, action_name, action_type, parameters, risk_level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), pb_b, 1, "Pause", "kubernetes_pause_deployment", "EXECUTE_PROVIDER_ACTION", '{}', "HIGH")
    )
    conn.commit()
    conn.close()
    
    # Execute Ansible
    print("Executing Ansible Playbook...")
    exec_a = trigger_execution(pb_a)
    print(f"Triggered Execution A: {exec_a}")
    
    # Execute Kubernetes (Find a deployment first)
    res = requests.get(f"{API_URL}/resources?resource_type=KUBERNETES_DEPLOYMENT", headers=headers())
    resources = res.json()
    if resources:
        deploy_id = resources[0]["id"]
        print("Executing Kubernetes Playbook on", deploy_id)
        exec_b = trigger_execution(pb_b, deploy_id)
        print(f"Triggered Execution B: {exec_b}")
    else:
        print("Skipping Kubernetes execution test (no deployments found).")
        
    print("Phase 1.16 E2E Test setup completed successfully!")

if __name__ == "__main__":
    run()
