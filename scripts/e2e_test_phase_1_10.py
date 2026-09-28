import requests
import time
import os
import sys
import uuid

API_URL = "http://localhost:8000/api/v1"
ADMIN_USER = "admin@infrapilot.local"
ADMIN_PASS = "admin123"

def print_step(msg):
    print(f"\n[{time.strftime('%H:%M:%S')}] {msg}")
    print("-" * 50)

def main():
    print_step("Phase 1.10 Automation E2E Validation")

    # 1. Login as Admin
    uid = uuid.uuid4()
    admin_email = f"e2e_admin_{uid}@infrapilot.io"
    admin_pass = "securepassword123!"
    
    # Register admin
    res = requests.post(f"{API_URL}/auth/register", json={"email": admin_email, "password": admin_pass})
    if res.status_code != 201:
        print("Registration failed:", res.text)
        sys.exit(1)
    admin_id = res.json()["id"]
        
    res = requests.post(
        f"{API_URL}/auth/login",
        json={"email": admin_email, "password": admin_pass}
    )
    if res.status_code != 200:
        print("Login failed:", res.text)
        sys.exit(1)
        
    # Assign admin role via psql
    assign_cmd = f'docker exec infrapilot_postgres psql -U postgres -d infrapilot -c "INSERT INTO user_roles (id, user_id, role_id, created_at) SELECT gen_random_uuid(), \'{admin_id}\', id, NOW() FROM roles WHERE name = \'ADMIN\';"'
    os.system(assign_cmd)
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Setup a Policy directly via DB script if API doesn't exist for it yet, but we will assume we use the DB directly for policy setup for this E2E test, 
    # since we did not create CRUD endpoints for policies (only automation endpoints were requested).
    print_step("2. Setting up test policies in DB")
    # For simplicity, we will run a quick DB command via docker exec to insert a policy
    db_setup_sql = """
        DELETE FROM policy_rules;
        DELETE FROM policies;
        
        INSERT INTO policies (id, name, description, enabled, priority) 
        VALUES ('00000000-0000-0000-0000-000000000001', 'Allow Low Risk', 'Allow low risk', true, 100);
        
        INSERT INTO policy_rules (id, policy_id, field, operator, expected_value, decision)
        VALUES (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'risk_level', 'EQUALS', '"LOW"', 'ALLOW');

        INSERT INTO policies (id, name, description, enabled, priority) 
        VALUES ('00000000-0000-0000-0000-000000000002', 'Require Approval Medium Risk', 'Require Approval', true, 200);
        
        INSERT INTO policy_rules (id, policy_id, field, operator, expected_value, decision)
        VALUES (gen_random_uuid(), '00000000-0000-0000-0000-000000000002', 'risk_level', 'EQUALS', '"MEDIUM"', 'REQUIRE_APPROVAL');
        
        INSERT INTO policies (id, name, description, enabled, priority) 
        VALUES ('00000000-0000-0000-0000-000000000003', 'Deny High Risk', 'Deny high risk', true, 300);
        
        INSERT INTO policy_rules (id, policy_id, field, operator, expected_value, decision)
        VALUES (gen_random_uuid(), '00000000-0000-0000-0000-000000000003', 'risk_level', 'EQUALS', '"HIGH"', 'DENY');
    """
    import subprocess
    subprocess.run(["docker", "exec", "-i", "infrapilot_postgres", "psql", "-U", "postgres", "-d", "infrapilot"], input=db_setup_sql.encode(), check=True)

    # 3. Create Playbook
    print_step("3. Creating Test Playbook")
    pb_payload = {
        "name": f"Test Playbook E2E {uid}",
        "description": "Playbook for E2E",
        "trigger_type": "MANUAL",
        "version": 1
    }
    res = requests.post(f"{API_URL}/automation/playbooks", json=pb_payload, headers=headers)
    if res.status_code != 201:
        print("Playbook creation failed:", res.text)
        sys.exit(1)
    playbook_id = res.json()["id"]
    print(f"Playbook created: {playbook_id}")

    # 4. Insert Playbook Steps into DB directly since no API was created for it
    print_step("4. Inserting Playbook Steps")
    step_setup_sql = f"""
        INSERT INTO playbook_steps (id, playbook_id, step_order, name, action_name, action_type, parameters, verification_config, risk_level, timeout_seconds, continue_on_failure)
        VALUES (gen_random_uuid(), '{playbook_id}', 1, 'Test Step', 'test_action_success', 'NOOP', '{{}}', '"EXPECT_SUCCESS"', 'LOW', 300, false);
    """
    subprocess.run(["docker", "exec", "-i", "infrapilot_postgres", "psql", "-U", "postgres", "-d", "infrapilot"], input=step_setup_sql.encode(), check=True)

    # Activate Playbook
    activate_sql = f"UPDATE playbooks SET status = 'ACTIVE' WHERE id = '{playbook_id}';"
    subprocess.run(["docker", "exec", "-i", "infrapilot_postgres", "psql", "-U", "postgres", "-d", "infrapilot"], input=activate_sql.encode(), check=True)

    # 5. Trigger Automation Execution
    print_step("5. Triggering Automation")
    exec_payload = {
        "playbook_id": playbook_id,
        "trigger_type": "MANUAL",
        "trigger_source": "E2E Script"
    }
    res = requests.post(f"{API_URL}/automation/executions", json=exec_payload, headers=headers)
    if res.status_code != 201:
        print("Execution creation failed:", res.text)
        sys.exit(1)
    
    exec_id = res.json()["execution_id"]
    print(f"Execution triggered: {exec_id}")
    
    # 6. Wait and check status
    print_step("6. Waiting for Policy Engine & Execution")
    for i in range(15):
        time.sleep(1)
        res = requests.get(f"{API_URL}/automation/executions/{exec_id}", headers=headers)
        if res.status_code == 200:
            status = res.json()["status"]
            print(f"Status: {status}")
            if status in ["SUCCEEDED", "FAILED", "REJECTED"]:
                break
    
    res = requests.get(f"{API_URL}/automation/executions/{exec_id}", headers=headers)
    final_status = res.json()["status"]
    
    if final_status != "SUCCEEDED":
        print(f"E2E Failed! Execution finished with status {final_status}")
        sys.exit(1)
        
    print_step("E2E Phase 1.10 Validation Successful!")

if __name__ == "__main__":
    main()
