import uuid
import pytest

def test_authorization_valid_permission(client_with_real_db, db_session):
    uid = uuid.uuid4()
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": f"auth_{uid}@example.com", "password": "securepassword"})
    user_id = resp.json()["id"]
    
    # Manually make them ADMIN to have all permissions
    from app.services.rbac import assign_role
    assign_role(db_session, uuid.UUID(user_id), "ADMIN")
    db_session.commit()
    
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"auth_{uid}@example.com", "password": "securepassword"})
    token = login_resp.json()["access_token"]
    
    # Access a protected endpoint (e.g. GET /api/v1/roles requires roles:read)
    roles_resp = client_with_real_db.get("/api/v1/roles", headers={"Authorization": f"Bearer {token}"})
    assert roles_resp.status_code == 200
    assert isinstance(roles_resp.json(), list)

def test_authorization_missing_permission(client_with_real_db, db_session):
    uid = uuid.uuid4()
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": f"noauth_{uid}@example.com", "password": "securepassword"})
    user_id = resp.json()["id"]
    
    # Assign VIEWER role, which has roles:read but NOT roles:manage
    from app.services.rbac import assign_role
    assign_role(db_session, uuid.UUID(user_id), "VIEWER")
    db_session.commit()
    
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"noauth_{uid}@example.com", "password": "securepassword"})
    token = login_resp.json()["access_token"]
    
    # Attempt to access POST /api/v1/roles (requires roles:manage)
    # Wait, the endpoint is POST /api/v1/roles/users/...
    assign_resp = client_with_real_db.post(
        f"/api/v1/roles/users/{user_id}/roles/OPERATOR",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert assign_resp.status_code == 403
    assert assign_resp.json()["error"]["message"] == "Forbidden"

def test_authorization_unauthenticated(client_with_real_db):
    roles_resp = client_with_real_db.get("/api/v1/roles")
    assert roles_resp.status_code == 403
    assert "Not authenticated" in roles_resp.json()["error"]["message"]
