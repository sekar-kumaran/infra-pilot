import pytest
import uuid
from sqlalchemy import text
from app.services.rbac import assign_role
from sqlalchemy import text

def test_first_user_becomes_admin(client_with_real_db, db_session):
    # Clear users completely for this test using raw SQL
    db_session.execute(text("DELETE FROM audit_events"))
    # Clean up instead of hard commit
    db_session.execute(text("DELETE FROM user_roles"))
    db_session.execute(text("DELETE FROM users"))
    # We commit here so that the new connections used by the test client see an empty DB
    db_session.commit()
    
    uid1 = uuid.uuid4()
    resp1 = client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"first_{uid1}@example.com", "password": "securepassword"}
    )
    assert resp1.status_code == 201
    
    uid2 = uuid.uuid4()
    resp2 = client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"second_{uid2}@example.com", "password": "securepassword"}
    )
    assert resp2.status_code == 201
    
    # Verify User 1 is ADMIN
    from app.services.rbac import get_user_roles
    user1_roles = get_user_roles(db_session, resp1.json()["id"])
    assert "ADMIN" in user1_roles
    
    # Verify User 2 is not ADMIN
    user2_roles = get_user_roles(db_session, resp2.json()["id"])
    assert "ADMIN" not in user2_roles

def test_assign_role(client_with_real_db, db_session):
    # Register an admin (assuming this is the first user, or we manually make it admin)
    # We will just register and then force it to be admin directly if it's not
    uid_admin = uuid.uuid4()
    resp_admin = client_with_real_db.post("/api/v1/auth/register", json={"email": f"admin_{uid_admin}@example.com", "password": "securepassword"})
    admin_id = resp_admin.json()["id"]
    
    # Manually ensure ADMIN role
    from app.services.rbac import assign_role
    res = assign_role(db_session, uuid.UUID(admin_id), "ADMIN")
    print(f"ASSIGN_ROLE RESULT: {res}")
    db_session.commit()
    
    # Register a normal user
    uid_user = uuid.uuid4()
    resp_user = client_with_real_db.post("/api/v1/auth/register", json={"email": f"user_{uid_user}@example.com", "password": "securepassword"})
    user_id = resp_user.json()["id"]
    
    # Login as admin
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"admin_{uid_admin}@example.com", "password": "securepassword"})
    admin_token = login_resp.json()["access_token"]
    
    print(f"TEST admin_id: {admin_id}")
    print(f"TEST user_id: {user_id}")
    
    # Debug: what are the admin's permissions?
    from app.services.rbac import get_user_permissions
    from app.models.rbac import Role, RolePermission, UserRole
    print("Roles count:", db_session.query(Role).count())
    print("RolePerms count:", db_session.query(RolePermission).count())
    
    rp_role_ids = db_session.query(RolePermission.role_id).distinct().all()
    print("RolePerms distinct role_ids:", rp_role_ids)
    
    ur_list = db_session.query(UserRole).all()
    for ur in ur_list:
        print(f"UR: {ur.user_id} -> {ur.role_id}")
    
    perms = get_user_permissions(db_session, uuid.UUID(admin_id))
    print("ADMIN PERMS:", perms)
    
    # Assign role OPERATOR to user
    assign_resp = client_with_real_db.post(
        f"/api/v1/roles/users/{user_id}/roles/OPERATOR",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert assign_resp.status_code == 201
    
    # Verify role was assigned
    from app.services.rbac import get_user_roles
    assert "OPERATOR" in get_user_roles(db_session, user_id)
    
def test_self_escalation_prevented(client_with_real_db, db_session):
    # Register a normal user
    uid_user = uuid.uuid4()
    resp_user = client_with_real_db.post("/api/v1/auth/register", json={"email": f"user_{uid_user}@example.com", "password": "securepassword"})
    user_id = resp_user.json()["id"]
    
    # We need to give them roles:manage to even attempt this endpoint.
    # If they are VIEWER, they get 403 anyway. Let's make them ADMIN, but they can't assign themselves ANOTHER role
    # Wait, an ADMIN has roles:manage. Can they assign themselves OPERATOR?
    # No, self-escalation rule says "Cannot assign roles to yourself".
    assign_role(db_session, uuid.UUID(user_id), "ADMIN")
    db_session.commit()
    
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"user_{uid_user}@example.com", "password": "securepassword"})
    user_token = login_resp.json()["access_token"]
    
    # Attempt to assign role to self
    assign_resp = client_with_real_db.post(
        f"/api/v1/roles/users/{user_id}/roles/OPERATOR",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert assign_resp.status_code == 403
    assert "Cannot assign roles to yourself" in assign_resp.json()["error"]["message"]

def test_last_admin_protection(client_with_real_db, db_session):
    # Ensure there is exactly one ADMIN
    # First clear others
    db_session.execute(text("DELETE FROM user_roles WHERE role_id = (SELECT id FROM roles WHERE name = 'ADMIN')"))
    
    uid_admin = uuid.uuid4()
    resp_admin = client_with_real_db.post("/api/v1/auth/register", json={"email": f"onlyadmin_{uid_admin}@example.com", "password": "securepassword"})
    admin_id = resp_admin.json()["id"]
    assign_role(db_session, uuid.UUID(admin_id), "ADMIN")
    db_session.commit()
    
    # We need a SECOND admin to perform the removal since you can't remove your own role
    uid_admin2 = uuid.uuid4()
    resp_admin2 = client_with_real_db.post("/api/v1/auth/register", json={"email": f"admin2_{uid_admin2}@example.com", "password": "securepassword"})
    admin2_id = resp_admin2.json()["id"]
    assign_role(db_session, uuid.UUID(admin2_id), "ADMIN")
    db_session.commit()
    
    # Now there are 2 admins. admin2 removes admin1's ADMIN role
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"admin2_{uid_admin2}@example.com", "password": "securepassword"})
    admin2_token = login_resp.json()["access_token"]
    
    rem_resp = client_with_real_db.delete(
        f"/api/v1/roles/users/{admin_id}/roles/ADMIN",
        headers={"Authorization": f"Bearer {admin2_token}"}
    )
    assert rem_resp.status_code == 200
    
    # Now admin2 is the LAST admin. Try to remove admin2's role.
    # But wait, admin2 cannot remove their OWN role. So we need a third user with roles:manage?
    # OPERATOR doesn't have roles:manage (only roles:read). 
    # Let's create an OPERATOR and manually grant them roles:manage just for the test? No, that's complex.
    # Wait, if admin2 is the last admin, they can't remove their own role ANYWAY because of self-demotion.
    # But if someone else with roles:manage tried to remove it, it would fail.
    # Let's write the test so we call the SERVICE directly to test the last admin logic!
    from app.services.rbac import remove_role, RBACException
    with pytest.raises(RBACException) as excinfo:
        remove_role(db_session, uuid.UUID(admin2_id), "ADMIN")
    assert "Cannot remove the last ADMIN role" in str(excinfo.value)
