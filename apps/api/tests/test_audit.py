import uuid
from sqlalchemy import text
from app.models.audit import AuditEvent

def test_audit_registration_and_login(client_with_real_db, db_session):
    uid = uuid.uuid4()
    email = f"audit_{uid}@example.com"
    
    # Register
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": email, "password": "securepassword"})
    user_id = resp.json()["id"]
    
    # Login
    client_with_real_db.post("/api/v1/auth/login", json={"email": email, "password": "securepassword"})
    
    # Login fail
    client_with_real_db.post("/api/v1/auth/login", json={"email": email, "password": "wrongpassword"})
    
    # Check DB
    events = db_session.query(AuditEvent).filter(AuditEvent.actor_user_id == user_id).order_by(AuditEvent.timestamp).all()
    
    # Should have at least REGISTER, LOGIN_SUCCESS, LOGIN_FAILED
    actions = [e.action for e in events]
    assert "USER_REGISTERED" in actions
    assert "USER_LOGIN_SUCCESS" in actions
    assert "USER_LOGIN_FAILED" in actions
    
    # Verify metadata sanitization
    for event in events:
        if event.metadata_:
            assert "password" not in event.metadata_ or event.metadata_["password"] == "[REDACTED]"
            assert "password_hash" not in event.metadata_
            assert "jwt" not in event.metadata_
            
def test_audit_authorization_denial(client_with_real_db, db_session):
    uid = uuid.uuid4()
    email = f"auditdenial_{uid}@example.com"
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": email, "password": "securepassword"})
    user_id = resp.json()["id"]
    
    from app.services.rbac import assign_role
    assign_role(db_session, uuid.UUID(user_id), "VIEWER")
    db_session.commit()
    
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": email, "password": "securepassword"})
    token = login_resp.json()["access_token"]
    
    # Attempt unauthorized action
    client_with_real_db.post(
        f"/api/v1/roles/users/{user_id}/roles/OPERATOR",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    events = db_session.query(AuditEvent).filter(
        AuditEvent.actor_user_id == user_id, 
        AuditEvent.action == "AUTHORIZATION_DENIED"
    ).all()
    
    assert len(events) > 0
    assert events[0].result == "DENY"
    assert events[0].resource_type == "PERMISSION"
    assert events[0].resource_id == "roles:manage"
