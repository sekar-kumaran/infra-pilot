import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.services.rbac import assign_role
from app.services.audit import log_event

def setup_users(client, db):
    # Register ADMIN user
    uid_admin = uuid.uuid4()
    admin_email = f"admin_{uid_admin}@example.com"
    resp = client.post("/api/v1/auth/register", json={"email": admin_email, "password": "securepassword"})
    admin_id = resp.json()["id"]

    # Assign ADMIN explicitly (just in case it's not the first user)
    assign_role(db, uuid.UUID(admin_id), "ADMIN")
    db.flush()

    # Login ADMIN
    admin_token = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "securepassword"}).json()["access_token"]

    # Register VIEWER user
    uid_viewer = uuid.uuid4()
    viewer_email = f"viewer_{uid_viewer}@example.com"
    resp = client.post("/api/v1/auth/register", json={"email": viewer_email, "password": "securepassword"})
    viewer_id = resp.json()["id"]

    # Assign VIEWER
    assign_role(db, uuid.UUID(viewer_id), "VIEWER")
    db.flush()

    # Login VIEWER
    viewer_token = client.post("/api/v1/auth/login", json={"email": viewer_email, "password": "securepassword"}).json()["access_token"]

    return admin_token, viewer_token, admin_id, viewer_id

def test_audit_api_authentication(client_with_real_db):
    resp = client_with_real_db.get("/api/v1/audit/")
    assert resp.status_code == 403

def test_audit_api_authorization(client_with_real_db, db_session):
    admin_token, viewer_token, _, viewer_id = setup_users(client_with_real_db, db_session)

    # Remove VIEWER role to ensure they have no permissions
    from app.services.rbac import remove_role
    remove_role(db_session, uuid.UUID(viewer_id), "VIEWER")
    db_session.flush()

    # User with no permissions should be rejected
    resp = client_with_real_db.get("/api/v1/audit/", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403

    # Admin should be allowed
    resp = client_with_real_db.get("/api/v1/audit/", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200

def test_audit_api_filtering_and_sorting(client_with_real_db, db_session):
    admin_token, _, admin_id, viewer_id = setup_users(client_with_real_db, db_session)

    # Log some custom events
    log_event(db_session, action="TEST_ACTION_1", resource_type="TEST_RES", result="SUCCESS", actor_user_id=uuid.UUID(admin_id))
    log_event(db_session, action="TEST_ACTION_2", resource_type="TEST_RES", result="DENY", actor_user_id=uuid.UUID(viewer_id))
    log_event(db_session, action="TEST_ACTION_1", resource_type="TEST_RES_OTHER", result="SUCCESS", actor_user_id=uuid.UUID(viewer_id))
    db_session.flush()

    # Filter by action
    resp = client_with_real_db.get("/api/v1/audit/?action=TEST_ACTION_1", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    for item in data:
        assert item["action"] == "TEST_ACTION_1"
        
    # Sort check (newest first)
    if len(data) >= 2:
        t1 = datetime.fromisoformat(data[0]["timestamp"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(data[1]["timestamp"].replace("Z", "+00:00"))
        assert t1 >= t2

    # Filter by actor_user_id
    resp = client_with_real_db.get(f"/api/v1/audit/?actor_user_id={viewer_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert item["actor_user_id"] == viewer_id

def test_audit_api_pagination(client_with_real_db, db_session):
    admin_token, _, admin_id, _ = setup_users(client_with_real_db, db_session)

    # Log 5 events
    for i in range(5):
        log_event(db_session, action=f"PAGE_TEST_{i}", resource_type="TEST", result="SUCCESS", actor_user_id=uuid.UUID(admin_id))
    db_session.flush()

    # Get page 1, size 2
    resp1 = client_with_real_db.get("/api/v1/audit/?page=1&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1) == 2

    # Get page 2, size 2
    resp2 = client_with_real_db.get("/api/v1/audit/?page=2&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 2

    # Ensure items are different
    assert data1[0]["id"] != data2[0]["id"]

def test_audit_api_sensitive_data_redacted(client_with_real_db, db_session):
    admin_token, _, admin_id, _ = setup_users(client_with_real_db, db_session)

    # Log an event with sensitive metadata
    log_event(
        db_session,
        action="TEST_SENSITIVE",
        resource_type="TEST",
        result="SUCCESS",
        actor_user_id=uuid.UUID(admin_id),
        metadata={"password": "secretpassword", "jwt": "header.payload.sig", "safe_field": "hello"}
    )
    db_session.flush()

    # Query it back
    resp = client_with_real_db.get("/api/v1/audit/?action=TEST_SENSITIVE", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    
    # We should find our event
    found = False
    for item in data:
        if item["action"] == "TEST_SENSITIVE":
            found = True
            meta = item.get("metadata", {})
            assert meta.get("password") == "[REDACTED]"
            assert meta.get("jwt") == "[REDACTED]"
            assert meta.get("safe_field") == "hello"
    
    assert found
