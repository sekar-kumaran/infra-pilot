"""
InfraPilot — End-to-End System & Demo App Integration Verification Script
Verifies:
  1. System Info & Health endpoints
  2. Observability endpoints (/logs, /live-events)
  3. Settings endpoints (/notifications)
  4. Users endpoint (/users)
  5. Automation endpoints (/schedules, /templates, /executions, /providers)
  6. Infrastructure topology (/topology)
  7. Operations endpoints (/workers, /queues, /health)
  8. Demo App Alertmanager Webhook (/integrations/webhook/prometheus)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import create_app
from app.database.session import get_db

def run_verification():
    print("=" * 70)
    print("INFRAPILOT INTEGRATION & AUDIT VERIFICATION")
    print("=" * 70)

    # Prepare Mock Database Session for pure API contract & routing verification
    mock_db = Mock()
    mock_db.query.return_value.all.return_value = []
    mock_db.query.return_value.count.return_value = 0
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

    app = create_app()
    app.dependency_overrides[get_db] = lambda: mock_db

    # Dummy authenticated user token
    import jwt
    from app.core.config import settings
    test_uid = str(uuid.uuid4())
    token = jwt.encode({"sub": test_uid}, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}

    # Mock user query to return an active Admin user
    mock_user = Mock()
    mock_user.id = uuid.UUID(test_uid)
    mock_user.email = "admin@infrapilot.io"
    mock_user.is_active = True
    mock_user.tenant_id = None
    mock_user.is_superuser = True

    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app)

    passed = 0
    failed = 0

    def check(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name} - {details}")
            failed += 1

    print("\n1. SYSTEM & HEALTH")
    r = client.get("/health/live")
    check("GET /health/live returns 200", r.status_code == 200 and r.json().get("status") == "ok")

    r = client.get("/api/v1/system/info")
    check("GET /api/v1/system/info returns 200", r.status_code == 200)

    print("\n2. OBSERVABILITY ENDPOINTS")
    r = client.get("/api/v1/observability/logs", headers=headers)
    check("GET /api/v1/observability/logs returns {items, total}", 
          r.status_code == 200 and "items" in r.json() and "total" in r.json(),
          r.text)

    r = client.get("/api/v1/observability/live-events", headers=headers)
    check("GET /api/v1/observability/live-events returns {items, total}", 
          r.status_code == 200 and "items" in r.json() and "total" in r.json(),
          r.text)

    print("\n3. SETTINGS ENDPOINTS")
    r = client.get("/api/v1/settings/notifications", headers=headers)
    check("GET /api/v1/settings/notifications returns {items, total}",
          r.status_code == 200 and "items" in r.json(),
          r.text)

    print("\n4. USERS ENDPOINTS")
    r = client.get("/api/v1/users", headers=headers)
    check("GET /api/v1/users returns {items, total, page, size}",
          r.status_code == 200 and "items" in r.json() and "total" in r.json(),
          r.text)

    print("\n5. AUTOMATION ENDPOINTS")
    r = client.get("/api/v1/automation/schedules", headers=headers)
    check("GET /api/v1/automation/schedules returns {items, stats}",
          r.status_code == 200 and "items" in r.json() and "stats" in r.json(),
          r.text)

    r = client.get("/api/v1/automation/templates", headers=headers)
    check("GET /api/v1/automation/templates returns pre-built templates",
          r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0,
          r.text)

    r = client.get("/api/v1/automation/providers", headers=headers)
    check("GET /api/v1/automation/providers returns providers",
          r.status_code == 200 and isinstance(r.json(), list),
          r.text)

    print("\n6. INFRASTRUCTURE & TOPOLOGY")
    r = client.get("/api/v1/infrastructure/topology", headers=headers)
    check("GET /api/v1/infrastructure/topology returns {nodes, edges}",
          r.status_code == 200 and "nodes" in r.json() and "edges" in r.json(),
          r.text)

    print("\n7. OPERATIONS ENDPOINTS")
    r = client.get("/api/v1/operations/workers", headers=headers)
    check("GET /api/v1/operations/workers returns workers list",
          r.status_code == 200 and isinstance(r.json(), list),
          r.text)

    r = client.get("/api/v1/operations/queues", headers=headers)
    check("GET /api/v1/operations/queues returns queues list",
          r.status_code == 200 and isinstance(r.json(), list),
          r.text)

    r = client.get("/api/v1/operations/health", headers=headers)
    check("GET /api/v1/operations/health returns system health",
          r.status_code == 200 and "status" in r.json() and "workers" in r.json(),
          r.text)

    print("\n8. DEMO APP PROMETHEUS ALERTMANAGER WEBHOOK")
    webhook_payload = {
        "receiver": "infrapilot-webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "WeatherApiHighErrorRate",
                    "severity": "CRITICAL",
                    "service": "weather-backend",
                    "job": "weather-api",
                    "instance": "demo_app_api:4000"
                },
                "annotations": {
                    "summary": "Weather API is experiencing high error rate",
                    "description": "The weather API has returned 500 errors in the last minute. Upstream provider issue."
                },
                "startsAt": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    with patch("app.services.event_ingestion.EventIngestionService.ingest_event") as mock_ingest:
        mock_raw = Mock()
        mock_raw.id = uuid.uuid4()
        mock_ingest.return_value = (mock_raw, True)

        r = client.post("/api/v1/integrations/webhook/prometheus", json=webhook_payload)
        check("POST /api/v1/integrations/webhook/prometheus accepts Alertmanager alert",
              r.status_code == 200 and r.json().get("status") == "ok" and r.json().get("new_events_ingested") == 1,
              r.text)

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
