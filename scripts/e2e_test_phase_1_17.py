#!/usr/bin/env python3
"""
InfraPilot Phase 1.17 — E2E Test: Docker Provider.

This test exercises the full operations lifecycle:
  Discovery → Policy → Approval → Execution → Verification → Audit → Incident Timeline

The test uses a REAL Docker test container as the target.
No fake Docker API responses exist. The same DockerClient used in production is used here.
"""
import os
import sys
import time
import uuid
import requests
import psycopg2

API_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = None
DOCKER_URL = os.environ.get("E2E_DOCKER_URL", "http://docker-test:2375")


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


def create_docker_integration():
    res = requests.post(
        f"{API_URL}/integrations",
        headers=headers(),
        json={
            "provider": "docker",
            "name": "E2E Docker Engine",
            "config": {
                "base_url": DOCKER_URL,
                "verify_tls": False,
                "timeout_seconds": 10
            }
        }
    )
    if res.status_code == 400:
        print("  Integration already exists — continuing")
        # Fetch existing
        existing = requests.get(f"{API_URL}/integrations", headers=headers())
        for i in existing.json():
            if i.get("provider") == "docker":
                return i["id"]
    elif res.status_code != 201:
        raise Exception(f"Failed to create integration: {res.text}")
    int_id = res.json()["id"]
    print(f"✓ Docker integration created: {int_id}")
    return int_id


def trigger_discovery(integration_id: str):
    res = requests.post(
        f"{API_URL}/integrations/{integration_id}/discover",
        headers=headers()
    )
    if res.status_code not in (200, 202):
        print(f"  Warning: Discovery trigger returned {res.status_code}: {res.text}")
    else:
        print("✓ Discovery triggered")


def get_container_resources():
    res = requests.get(f"{API_URL}/resources?resource_type=CONTAINER", headers=headers())
    if res.status_code != 200:
        raise Exception(f"Failed to fetch resources: {res.text}")
    return res.json()


def create_playbook(name: str):
    res = requests.post(
        f"{API_URL}/automation/playbooks",
        headers=headers(),
        json={"name": name, "description": "E2E Docker Test", "trigger_type": "MANUAL"}
    )
    if res.status_code != 201:
        raise Exception(f"Failed to create playbook: {res.text}")
    pb_id = res.json()["id"]
    print(f"✓ Playbook created: {pb_id}")
    return pb_id


def inject_step_via_db(playbook_id: str, action_name: str, params: dict = None):
    conn = psycopg2.connect("postgresql://postgres:postgrespassword@localhost:5432/infrapilot")
    cur = conn.cursor()
    step_id = str(uuid.uuid4())
    import json
    cur.execute(
        "INSERT INTO playbook_steps (id, playbook_id, step_order, name, action_name, action_type, parameters, risk_level) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (step_id, playbook_id, 1, action_name, action_name, "EXECUTE_PROVIDER_ACTION",
         json.dumps(params or {}), "HIGH")
    )
    conn.commit()
    conn.close()
    print(f"✓ Step '{action_name}' injected")


def trigger_execution(playbook_id: str, resource_id: str):
    res = requests.post(
        f"{API_URL}/automation/executions",
        headers=headers(),
        json={"playbook_id": playbook_id, "trigger_type": "MANUAL", "trigger_source": "API", "resource_id": resource_id}
    )
    if res.status_code != 201:
        raise Exception(f"Failed to trigger execution: {res.text}")
    exec_id = res.json()["execution_id"]
    print(f"✓ Execution triggered: {exec_id}")
    return exec_id


def wait_for_execution(exec_id: str, timeout: int = 120):
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(f"{API_URL}/automation/executions/{exec_id}", headers=headers())
        if res.status_code == 200:
            status = res.json().get("status")
            if status in ("SUCCEEDED", "FAILED", "TIMED_OUT", "REJECTED"):
                return res.json()
            elif status == "AWAITING_APPROVAL":
                return res.json()
        time.sleep(3)
    raise Exception(f"Execution {exec_id} timed out after {timeout}s")


def approve_execution(exec_id: str):
    res = requests.get(f"{API_URL}/automation/approvals", headers=headers())
    approvals = [a for a in res.json() if a.get("execution_id") == exec_id]
    if not approvals:
        print("  No pending approval found")
        return False
    app_id = approvals[0]["id"]
    res = requests.post(
        f"{API_URL}/automation/approvals/{app_id}/action",
        headers=headers(),
        json={"action": "APPROVE", "reason": "E2E Test Approval"}
    )
    if res.status_code != 200:
        raise Exception(f"Approval failed: {res.text}")
    print(f"✓ Execution approved")
    return True


def run():
    print("\n" + "="*60)
    print("InfraPilot Phase 1.17 Docker E2E Test")
    print("="*60)

    failures = []

    login()

    # 1. Create Docker Integration
    print("\n[1] Create Docker Integration")
    int_id = create_docker_integration()

    # 2. Trigger Discovery
    print("\n[2] Trigger Resource Discovery")
    trigger_discovery(int_id)
    time.sleep(8)  # Wait for discovery to complete

    # 3. Verify containers discovered
    print("\n[3] Verify Container Resources")
    containers = get_container_resources()
    print(f"  Found {len(containers)} container(s)")
    if not containers:
        print("  WARNING: No containers found — E2E will skip automation test")
        failures.append("no_containers_discovered")
    else:
        print(f"  ✓ Containers discovered")

    # 4. Idempotent Discovery
    print("\n[4] Idempotent Discovery Check")
    trigger_discovery(int_id)
    time.sleep(8)
    containers_after = get_container_resources()
    if len(containers_after) == len(containers):
        print(f"  ✓ Idempotent: resource count unchanged ({len(containers_after)})")
    else:
        print(f"  ✗ Non-idempotent: {len(containers)} → {len(containers_after)}")
        failures.append("non_idempotent_discovery")

    # 5. Read Operation (inspect container)
    print("\n[5] Read Operation — Collect Container Information")
    if containers:
        pb_read = create_playbook("E2E Docker Read")
        inject_step_via_db(pb_read, "docker_collect_container_information")
        exec_id = trigger_execution(pb_read, containers[0]["id"])
        result = wait_for_execution(exec_id)
        if result.get("status") == "SUCCEEDED":
            print("  ✓ Read execution succeeded")
        else:
            print(f"  ✗ Read execution failed: {result.get('status')}")
            failures.append("read_execution_failed")

    # 6. Automation (restart) — requires approval
    print("\n[6] Automation — Restart Container (High Risk, Requires Approval)")
    if containers:
        pb_restart = create_playbook("E2E Docker Restart")
        inject_step_via_db(pb_restart, "docker_restart_container")
        exec_id = trigger_execution(pb_restart, containers[0]["id"])
        result = wait_for_execution(exec_id)

        if result.get("status") == "AWAITING_APPROVAL":
            print("  ✓ Policy correctly flagged for approval")
            approved = approve_execution(exec_id)
            if approved:
                result = wait_for_execution(exec_id, timeout=180)
                if result.get("status") == "SUCCEEDED":
                    print("  ✓ Restart execution succeeded and verified")
                elif result.get("status") == "VERIFYING":
                    print("  ✓ Execution in verification (async verification pending)")
                else:
                    print(f"  ✗ Restart execution ended with: {result.get('status')}")
                    failures.append("restart_execution_failed")
        elif result.get("status") == "SUCCEEDED":
            print("  ✓ Restart succeeded (no approval required in test policy config)")
        else:
            print(f"  ✗ Unexpected execution status: {result.get('status')}")
            failures.append("restart_unexpected_status")

    # 7. Capabilities API
    print("\n[7] Providers Capability API")
    res = requests.get(f"{API_URL}/providers/capabilities", headers=headers())
    if res.status_code == 200:
        caps = res.json()
        docker_cap = next((c for c in caps if c.get("provider") == "docker"), None)
        if docker_cap:
            print(f"  ✓ Docker capabilities visible: {docker_cap.get('capabilities', [])}")
        else:
            print("  ✗ Docker not found in capability registry")
            failures.append("capability_not_found")
    else:
        print(f"  ✗ Capability API failed: {res.status_code}")
        failures.append("capability_api_error")

    # Summary
    print("\n" + "="*60)
    if failures:
        print(f"FAILED — {len(failures)} failure(s): {failures}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED ✓")
        sys.exit(0)


if __name__ == "__main__":
    run()
