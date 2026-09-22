import pytest
import uuid
from fastapi.testclient import TestClient

def test_register_user_success(client_with_real_db):
    uid = uuid.uuid4()
    response = client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"test_{uid}@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == f"test_{uid}@example.com"
    assert "id" in data
    assert "password_hash" not in data

def test_register_duplicate_email(client_with_real_db):
    uid = uuid.uuid4()
    # Register first
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"dup_{uid}@example.com", "password": "securepassword"}
    )
    # Register duplicate
    response = client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"dup_{uid}@example.com", "password": "securepassword2"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Email already registered"

def test_register_invalid_password(client_with_real_db):
    uid = uuid.uuid4()
    response = client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"test3_{uid}@example.com", "password": "short"}
    )
    assert response.status_code == 400
    assert "Password must be at least" in response.json()["error"]["message"]

def test_login_success(client_with_real_db):
    uid = uuid.uuid4()
    # Setup user
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"login_{uid}@example.com", "password": "securepassword"}
    )
    
    # Login
    response = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"login_{uid}@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client_with_real_db):
    uid = uuid.uuid4()
    # Setup user
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"login2_{uid}@example.com", "password": "securepassword"}
    )
    
    # Login with wrong pass
    response = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"login2_{uid}@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"

def test_login_nonexistent_account(client_with_real_db):
    uid = uuid.uuid4()
    response = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"nobody_{uid}@example.com", "password": "securepassword"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"

def test_auth_me_success(client_with_real_db):
    uid = uuid.uuid4()
    # Setup user
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"me_{uid}@example.com", "password": "securepassword"}
    )
    
    # Login
    login_resp = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"me_{uid}@example.com", "password": "securepassword"}
    )
    token = login_resp.json()["access_token"]
    
    # Get me
    response = client_with_real_db.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == f"me_{uid}@example.com"
    assert "password_hash" not in data

def test_auth_me_unauthenticated(client_with_real_db):
    response = client_with_real_db.get("/api/v1/auth/me")
    assert response.status_code == 403 # HTTPBearer returns 403 when not provided

def test_auth_me_invalid_token(client_with_real_db):
    response = client_with_real_db.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["error"]["message"]
