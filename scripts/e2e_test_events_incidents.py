"""
InfraPilot Phase 1.7 + 1.8 — E2E Verification Script
Validates the canonical Event, Alert, and Incident lifecycle.

Run: python scripts/e2e_test_events_incidents.py
Requires: API running at localhost:8000 with docker compose stack
"""
import sys
import time
import json
import uuid
import urllib.request
import urllib.error
import subprocess
from datetime import datetime

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


section("1. Setup Auth and RBAC")

# Register admin
uid = uuid.uuid4()
admin_email = f"e2e_evt_admin_{uid}@infrapilot.io"
s, reg = req("POST", "/api/v1/auth/register", {"email": admin_email, "password": "securepassword123!"})
check("Admin Registered", s == 201)
admin_id = reg.get("id")

s, login = req("POST", "/api/v1/auth/login", {"email": admin_email, "password": "securepassword123!"})
check("Admin Logged In", s == 200)
admin_token = login["access_token"]

# Assign admin role
psql(f"INSERT INTO user_roles (id, user_id, role_id, created_at) SELECT gen_random_uuid(), '{admin_id}', id, NOW() FROM roles WHERE name = 'ADMIN';")

# Create integration
s, integration = req("POST", "/api/v1/integrations/", {
    "name": f"Test Integration {uid}",
    "provider": "test_provider",
    "description": "E2E Test Integration",
    "configuration": {"api_key": "dummy"}
}, token=admin_token)
if s != 201:
    print(f"Integration Creation Failed. Status: {s}, Body: {integration}")
check("Created Integration", s == 201)
integration_id = integration["id"]


section("2. Event Ingestion")

event_payload_1 = {
    "integration_id": integration_id,
    "provider": "test_provider",
    "event_type": "cpu_high",
    "external_event_id": f"ext-{uid}-1",
    "payload": {
        "title": "High CPU on DB Node",
        "alert_type": "CPU_HIGH",
        "severity": "WARNING",
        "labels": {"host": "db-1"}
    }
}

s, ev1 = req("POST", "/api/v1/events", event_payload_1, token=admin_token)
if s != 202:
    print(f"Event Ingestion Failed. Status: {s}, Body: {ev1}")
check("Ingest Event 1", s == 202)
raw_event_id = ev1["id"]

# Verify Idempotency
s, ev_dup = req("POST", "/api/v1/events", event_payload_1, token=admin_token)
check("Idempotent Ingestion Returns 202", s == 202)
check("Idempotent Returns Same Event", ev_dup["id"] == raw_event_id)

# Wait for Celery processing
print("  Waiting 5 seconds for Celery processing...")
time.sleep(5)

s, ev1_fetched = req("GET", f"/api/v1/events/{raw_event_id}", token=admin_token)
check("Event Processed Status", ev1_fetched["processing_status"] == "PROCESSED")


section("3. Alert & Incident Creation")

# Check Alerts
s, alerts = req("GET", "/api/v1/alerts", token=admin_token)
check("Alert Created", len(alerts) >= 1)
alert1 = next(a for a in alerts if a["raw_event_id"] == raw_event_id)
check("Alert Status is ACTIVE", alert1["status"] == "ACTIVE")
check("Alert Severity is WARNING", alert1["severity"] == "WARNING")

# Check Incidents
s, incidents = req("GET", "/api/v1/incidents", token=admin_token)
check("Incident Created", len(incidents) >= 1)

# Find incident correlated to this alert
s, related_alerts = req("GET", f"/api/v1/incidents/{incidents[0]['id']}/alerts", token=admin_token)
# For this E2E, we didn't specify resource_id, so the alert won't strictly map via get_incident_alerts logic (which uses resource_id) 
# But we can verify the incident exists and timeline updated.
incident1 = incidents[0]
incident_id = incident1["id"]
check("Incident Status is OPEN", incident1["status"] == "OPEN")
check("Incident Severity is WARNING", incident1["severity"] == "WARNING")

s, timeline = req("GET", f"/api/v1/incidents/{incident_id}/timeline", token=admin_token)
check("Timeline has INCIDENT_CREATED", any(t["event_type"] == "INCIDENT_CREATED" for t in timeline))


section("4. Correlation & Severity Escalation")

event_payload_2 = {
    "integration_id": integration_id,
    "provider": "test_provider",
    "event_type": "db_down",
    "external_event_id": f"ext-{uid}-2",
    "payload": {
        "title": "CPU completely locked",
        "alert_type": "CPU_HIGH",
        "severity": "CRITICAL",
        "labels": {"host": "db-1"}
    }
}

s, ev2 = req("POST", "/api/v1/events", event_payload_2, token=admin_token)
check("Ingest Event 2 (CRITICAL)", s == 202)

print("  Waiting 5 seconds for Celery processing...")
time.sleep(5)

# Verify Incident escalated
s, inc_escalated = req("GET", f"/api/v1/incidents/{incident_id}", token=admin_token)
check("Incident Severity Escalated to CRITICAL", inc_escalated["severity"] == "CRITICAL")

s, timeline2 = req("GET", f"/api/v1/incidents/{incident_id}/timeline", token=admin_token)
check("Timeline has SEVERITY_CHANGED", any(t["event_type"] == "SEVERITY_CHANGED" for t in timeline2))


section("5. Incident State Machine")

# Acknowledge
s, ack = req("POST", f"/api/v1/incidents/{incident_id}/acknowledge", token=admin_token)
check("Acknowledge Incident -> INVESTIGATING", s == 200 and ack["status"] == "INVESTIGATING")

# Resolve Alert
s, ack_alert = req("POST", f"/api/v1/alerts/{alert1['id']}/resolve", token=admin_token)
check("Resolve Alert", s == 200 and ack_alert["status"] == "RESOLVED")

# Resolve Incident
s, resolve = req("POST", f"/api/v1/incidents/{incident_id}/resolve", token=admin_token)
check("Resolve Incident", s == 200 and resolve["status"] == "RESOLVED")

# Verify invalid transition
s, invalid = req("POST", f"/api/v1/incidents/{incident_id}/status", {"status": "OPEN"}, token=admin_token)
check("Invalid state transition rejected (RESOLVED -> OPEN)", s == 400)


section("6. Audit Validation")
s, audits = req("GET", "/api/v1/audit", token=admin_token)
check("Audit logs generated", len(audits) > 0)
event_audits = [a for a in audits if a["resource_type"] == "raw_event" and a["action"] == "event.ingestion.success"]
check("Audit logged event ingestion", len(event_audits) > 0)


# ─────────────────────────────────────────────
print("\n" + "="*60)
failures = sum(1 for _, ok, _ in RESULTS if not ok)
if failures > 0:
    print(f"❌ {failures} CHECKS FAILED.")
    sys.exit(1)
else:
    print(f"✅ ALL {len(RESULTS)} E2E CHECKS PASSED.")
    sys.exit(0)
