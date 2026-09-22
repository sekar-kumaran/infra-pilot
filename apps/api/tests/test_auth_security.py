import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text
import jwt
from datetime import datetime, timezone, timedelta

from app.core.config import settings

def test_password_is_not_stored_plaintext(db_session, client_with_real_db):
    uid = uuid.uuid4()
    email = f"sec_{uid}@example.com"
    raw_password = "supersecretpassword123"
    
    # Register
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": email, "password": raw_password}
    )
    
    # Query database directly
    result = db_session.execute(
        text("SELECT password_hash FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    assert result is not None
    password_hash = result[0]
    
    # Verify plaintext is not stored
    assert password_hash != raw_password
    # Verify it looks like a hash (argon2 or bcrypt typically starts with $)
    assert password_hash.startswith("$")

def test_auth_errors_do_not_leak_user_existence(client_with_real_db):
    uid = uuid.uuid4()
    # Register an account
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"exists_{uid}@example.com", "password": "securepassword"}
    )
    
    # Login with wrong password for existing account
    resp1 = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"exists_{uid}@example.com", "password": "wrongpassword"}
    )
    
    # Login for nonexistent account
    resp2 = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"notexists_{uid}@example.com", "password": "wrongpassword"}
    )
    
    # Responses should be identical
    assert resp1.status_code == 401
    assert resp2.status_code == 401
    assert resp1.json()["error"]["message"] == resp2.json()["error"]["message"]

def test_expired_token(client_with_real_db):
    uid = uuid.uuid4()
    # Register an account
    client_with_real_db.post(
        "/api/v1/auth/register",
        json={"email": f"expired_{uid}@example.com", "password": "securepassword"}
    )
    # Login to get valid payload structure
    login_resp = client_with_real_db.post(
        "/api/v1/auth/login",
        json={"email": f"expired_{uid}@example.com", "password": "securepassword"}
    )
    
    # Create an expired token manually
    token = login_resp.json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    
    # Set expiration in the past
    payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    expired_token = jwt.encode(payload, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)
    
    response = client_with_real_db.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["error"]["message"]

def test_jwt_secret_not_exposed_in_system_info(client_with_real_db):
    response = client_with_real_db.get("/api/v1/system/info")
    assert response.status_code == 200
    text_data = response.text
    # Ensure AUTH_SECRET_KEY value is not in output if it's set
    if settings.AUTH_SECRET_KEY:
        assert settings.AUTH_SECRET_KEY not in text_data
