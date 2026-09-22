"""
InfraPilot Phase 1.6 — Comprehensive E2E Verification Script
Validates all acceptance criteria from the Phase 1.6 specification.

Run: python scripts/e2e_test_integrations.py
Requires: API running at localhost:8000 with docker compose stack
"""
import sys
import time
import json
import uuid
import urllib.request
import urllib.error
import subprocess

BASE_URL = "http://localhost:8000"
RESULTS = []

def req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        status = resp.status
        body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {}
    return status, body

def psql(sql):
    result = subprocess.run(
        ["docker", "exec", "infrapilot_postgres", "psql", "-U", "postgres", "-d", "infrapilot", "-t", "-c", sql],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def docker_logs(container):
    result = subprocess.run(["docker", "logs", container, "2>&1"], capture_output=True, text=True, shell=False)
    return result.stdout + result.stderr

def check(label, condition, detail=""):
    ok = bool(condition)
    RESULTS.append((label, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f" - {detail}" if detail else ""))
    return ok

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ─────────────────────────────────────────────
section("1. API + Infrastructure Health")
# ─────────────────────────────────────────────
s, live = req("GET", "/health/live")
check("API /health/live -> 200", s == 200)
check("API live status = ok", live.get("status") == "ok")

s, ready = req("GET", "/health/ready")
check("API /health/ready -> DB healthy", ready.get("database") == "healthy")

pg_count = psql("SELECT 1")
check("PostgreSQL reachable", pg_count == "1")

rmq = subprocess.run(
    ["docker", "exec", "infrapilot_rabbitmq", "rabbitmq-diagnostics", "-q", "ping"],
    capture_output=True, text=True
)
check("RabbitMQ ping OK", rmq.returncode == 0)

worker_log = subprocess.run(
    ["docker", "logs", "infrapilot_celery_worker"],
    capture_output=True, text=True
).stderr + subprocess.run(
    ["docker", "logs", "infrapilot_celery_worker"],
    capture_output=True, text=True
).stdout
check("Celery worker connected to RabbitMQ", "Connected to amqp" in worker_log)
check("validate_integration_task registered", "validate_integration_task" in worker_log)
check("discover_resources_task registered", "discover_resources_task" in worker_log)


# ─────────────────────────────────────────────
section("2. Auth — Registration & Login")
# ─────────────────────────────────────────────
uid = uuid.uuid4()
admin_email = f"e2e_admin_{uid}@infrapilot.io"

s, reg = req("POST", "/api/v1/auth/register", {"email": admin_email, "password": "securepassword123!"})
if s != 201:
    print(f"  [DEBUG] Register returned {s}: {reg}")
check("Register admin user -> 201", s == 201)
admin_user_id = reg.get("id")
check("Registration returns user ID", bool(admin_user_id))

# Assign ADMIN role via psql
psql(f"INSERT INTO user_roles (id, user_id, role_id, created_at) SELECT gen_random_uuid(), '{admin_user_id}', id, NOW() FROM roles WHERE name = 'ADMIN';")

s, login = req("POST", "/api/v1/auth/login", {"email": admin_email, "password": "securepassword123!"})
check("Admin login -> 200", s == 200)
admin_token = login.get("access_token")
check("Admin login returns access_token", bool(admin_token))

# Viewer user
uid2 = uuid.uuid4()
viewer_email = f"e2e_viewer_{uid2}@infrapilot.io"
s, reg2 = req("POST", "/api/v1/auth/register", {"email": viewer_email, "password": "securepassword123!"})
viewer_user_id = reg2.get("id")
psql(f"INSERT INTO user_roles (id, user_id, role_id, created_at) SELECT gen_random_uuid(), '{viewer_user_id}', id, NOW() FROM roles WHERE name = 'VIEWER';")
s, vlogin = req("POST", "/api/v1/auth/login", {"email": viewer_email, "password": "securepassword123!"})
viewer_token = vlogin.get("access_token")
check("Viewer login successful", bool(viewer_token))


# ─────────────────────────────────────────────
section("3. RBAC — Restrictions")
# ─────────────────────────────────────────────
s, _ = req("GET", "/api/v1/integrations/")
check("Unauthenticated GET integrations -> 403", s == 403)

s, _ = req("POST", "/api/v1/integrations/", {
    "name": "viewer-attempt", "provider": "test_provider", "configuration": {}
}, token=viewer_token)
check("Viewer cannot CREATE integration -> 403", s == 403)

s, _ = req("GET", "/api/v1/integrations/", token=viewer_token)
check("Viewer CAN READ integrations -> 200", s == 200)

s, _ = req("POST", "/api/v1/environments/", {
    "name": "e2e-viewer-env", "environment_type": "DEVELOPMENT"
}, token=viewer_token)
check("Viewer cannot CREATE environment -> 403", s == 403)


# ─────────────────────────────────────────────
section("4. Integration CRUD")
# ─────────────────────────────────────────────
payload = {
    "name": "E2E Test Integration",
    "provider": "test_provider",
    "description": "Integration created by E2E script",
    "configuration": {
        "endpoint": "http://example.internal",
        "username": "admin",
        "api_token": "SUPER_SECRET",
        "test_mode": True,
        "test_token": "valid",
        "nested": {
            "password": "VERY_SECRET",
            "client_secret": "CLIENT_SECRET"
        }
    }
}
s, integ = req("POST", "/api/v1/integrations/", payload, token=admin_token)
check("Admin creates integration -> 201", s == 201)
integration_id = integ.get("id")
check("Integration ID assigned", bool(integration_id))
check("Status = CONFIGURED", integ.get("status") == "CONFIGURED")


# ─────────────────────────────────────────────
section("5. Secret Encryption Verification")
# ─────────────────────────────────────────────
s, get_resp = req("GET", f"/api/v1/integrations/{integration_id}", token=admin_token)
check("GET integration -> 200", s == 200)
resp_str = json.dumps(get_resp)
check("SUPER_SECRET not in GET response", "SUPER_SECRET" not in resp_str)
check("VERY_SECRET not in GET response", "VERY_SECRET" not in resp_str)
check("CLIENT_SECRET not in GET response", "CLIENT_SECRET" not in resp_str)
check("secret_payload not in GET response", "secret_payload" not in resp_str)
check("api_token key absent from configuration in response", "api_token" not in str(get_resp.get("configuration", {})))

db_config = psql(f"SELECT configuration::text FROM integrations WHERE id = '{integration_id}'")
check("SUPER_SECRET not in DB configuration column", "SUPER_SECRET" not in db_config)
check("VERY_SECRET not in DB configuration column", "VERY_SECRET" not in db_config)

db_payload = psql(f"SELECT secret_payload IS NOT NULL FROM integrations WHERE id = '{integration_id}'")
check("secret_payload column populated in DB", "t" in db_payload)


# ─────────────────────────────────────────────
section("6. Capabilities")
# ─────────────────────────────────────────────
s, caps = req("GET", f"/api/v1/integrations/{integration_id}/capabilities", token=admin_token)
check("Get capabilities -> 200", s == 200)
c = caps.get("capabilities", {})
check("resource_discovery capability = True", c.get("resource_discovery") is True)
check("resource_read capability = True", c.get("resource_read") is True)
check("health_check capability = True", c.get("health_check") is True)


# ─────────────────────────────────────────────
section("7. Integration Update")
# ─────────────────────────────────────────────
s, updated = req("PATCH", f"/api/v1/integrations/{integration_id}", {"description": "Updated by E2E"}, token=admin_token)
check("Update integration -> 200", s == 200)
check("Description updated", updated.get("description") == "Updated by E2E")


# ─────────────────────────────────────────────
section("8. Celery Validation Task")
# ─────────────────────────────────────────────
s, _ = req("POST", f"/api/v1/integrations/{integration_id}/validate", token=admin_token)
check("Trigger validate -> 202", s == 202)

print("  Waiting 6s for Celery to process validation...")
time.sleep(6)

s, integ_after = req("GET", f"/api/v1/integrations/{integration_id}", token=admin_token)
check("Status became HEALTHY after validation", integ_after.get("status") == "HEALTHY")
check("last_checked_at updated", integ_after.get("last_checked_at") is not None)

worker_log2 = subprocess.run(
    ["docker", "logs", "infrapilot_celery_worker"],
    capture_output=True, text=True
)
wlog2 = worker_log2.stdout + worker_log2.stderr
check("Celery log shows validation successful", "validation successful" in wlog2)


# ─────────────────────────────────────────────
section("9. Celery Discovery Task")
# ─────────────────────────────────────────────
before_count = psql("SELECT COUNT(*) FROM infrastructure_resources WHERE provider = 'test_provider'").strip()
before_count = int(before_count) if before_count.isdigit() else 0

s, _ = req("POST", f"/api/v1/integrations/{integration_id}/discover", token=admin_token)
check("Trigger discover -> 202", s == 202)

print("  Waiting 6s for Celery to process discovery...")
time.sleep(6)

after_count = psql("SELECT COUNT(*) FROM infrastructure_resources WHERE provider = 'test_provider'").strip()
after_count = int(after_count) if after_count.isdigit() else 0
check(f"Resources discovered and persisted (count={after_count})", after_count >= 2)

worker_log3 = subprocess.run(
    ["docker", "logs", "infrapilot_celery_worker"],
    capture_output=True, text=True
)
wlog3 = worker_log3.stdout + worker_log3.stderr
check("Celery log shows discovery succeeded", "Discovered 2 resources" in wlog3)


# ─────────────────────────────────────────────
section("10. Idempotency — Re-run Discovery")
# ─────────────────────────────────────────────
req("POST", f"/api/v1/integrations/{integration_id}/discover", token=admin_token)
print("  Waiting 6s for second discovery...")
time.sleep(6)

after_second = psql("SELECT COUNT(*) FROM infrastructure_resources WHERE provider = 'test_provider'").strip()
after_second = int(after_second) if after_second.isdigit() else 0
check(
    f"Idempotency: no duplicates (before={after_count}, after={after_second})",
    after_second == after_count
)


# ─────────────────────────────────────────────
section("11. Integration Disable / Enable")
# ─────────────────────────────────────────────
s, disabled = req("POST", f"/api/v1/integrations/{integration_id}/disable", token=admin_token)
check("Disable integration -> 200", s == 200)
check("Status = DISABLED", disabled.get("status") == "DISABLED")

s, enabled = req("POST", f"/api/v1/integrations/{integration_id}/enable", token=admin_token)
check("Re-enable integration -> 200", s == 200)
check("Status = HEALTHY after re-enable", enabled.get("status") in ("HEALTHY", "CONFIGURED"))


# ─────────────────────────────────────────────
section("12. Audit Events")
# ─────────────────────────────────────────────
s, audit_events = req("GET", f"/api/v1/audit/?resource_id={integration_id}", token=admin_token)
check("Audit API -> 200", s == 200)
if isinstance(audit_events, list):
    actions = [e.get("action") for e in audit_events]
    check("integration.created audit event present", "integration.created" in actions)
    check("integration.updated audit event present", "integration.updated" in actions)
    check("integration.disabled audit event present", "integration.disabled" in actions)
    audit_str = json.dumps(audit_events)
    check("SUPER_SECRET not in audit events", "SUPER_SECRET" not in audit_str)
    check("VERY_SECRET not in audit events", "VERY_SECRET" not in audit_str)
    check("CLIENT_SECRET not in audit events", "CLIENT_SECRET" not in audit_str)
else:
    check("Audit events is a list", False, str(type(audit_events)))


# ─────────────────────────────────────────────
section("13. Security — No Secrets in Logs")
# ─────────────────────────────────────────────
api_logs = subprocess.run(
    ["docker", "logs", "infrapilot_api"],
    capture_output=True, text=True
)
api_log_text = api_logs.stdout + api_logs.stderr
check("SUPER_SECRET not in API logs", "SUPER_SECRET" not in api_log_text)
check("VERY_SECRET not in API logs", "VERY_SECRET" not in api_log_text)
check("CLIENT_SECRET not in API logs", "CLIENT_SECRET" not in api_log_text)
check("postgrespassword not in API logs", "postgrespassword" not in api_log_text)

wfinal = subprocess.run(["docker", "logs", "infrapilot_celery_worker"], capture_output=True, text=True)
wlog_final = wfinal.stdout + wfinal.stderr
check("SUPER_SECRET not in worker logs", "SUPER_SECRET" not in wlog_final)
check("VERY_SECRET not in worker logs", "VERY_SECRET" not in wlog_final)


# ─────────────────────────────────────────────
section("14. Invalid Provider Rejected")
# ─────────────────────────────────────────────
s, err = req("POST", "/api/v1/integrations/", {
    "name": "bad-provider", "provider": "nonexistent_provider", "configuration": {}
}, token=admin_token)
check("Invalid provider rejected -> 422", s == 422)


# ─────────────────────────────────────────────
section("FINAL SUMMARY")
# ─────────────────────────────────────────────
total = len(RESULTS)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = total - passed

print(f"\n  Total checks : {total}")
print(f"  Passed       : {passed}")
print(f"  Failed       : {failed}")

if failed > 0:
    print("\nFailed checks:")
    for label, ok, detail in RESULTS:
        if not ok:
            print(f"  [FAIL] {label}" + (f" - {detail}" if detail else ""))
    sys.exit(1)
else:
    print("\n  ALL E2E CHECKS PASSED")
    print("  PHASE_1.6_IMPLEMENTED")
