"""
Pytest configuration and shared fixtures.

Test database strategy: Option A — dedicated PostgreSQL test database.
  - infrapilot_test database on the same Postgres instance as dev.
  - Real PostgreSQL connections; no SQLite substitutes.
  - Per-test transactions rolled back by db_session fixture (in test_database.py).
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, create_app
from app.database.session import get_db

@pytest.fixture(scope="session")
def engine():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgrespassword@localhost:5432/infrapilot",
    )
    eng = create_engine(db_url, pool_pre_ping=True)
    yield eng
    eng.dispose()

@pytest.fixture()
def db_session(engine):
    conn = engine.connect()
    tx = conn.begin()
    Session = sessionmaker(bind=conn)
    session = Session()
    
    # Patch commit to flush so endpoints don't actually commit the transaction
    session.commit = session.flush
    
    yield session
    session.close()
    tx.rollback()
    conn.close()


# ---------------------------------------------------------------------------
# Default client — uses the real DB via the app's get_db dependency.
# Used for integration-level endpoint tests when DB is available.
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Test client wired to the real application (including real get_db)."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Client backed by a real test DB session.
# Overrides get_db with a session pointing at the test database.
# ---------------------------------------------------------------------------

@pytest.fixture
def client_with_real_db(db_session):
    """
    Test client where get_db is overridden with the test's db_session.
    Because db_session.commit() is patched to flush(), endpoints see
    the same data and can 'commit', but it will be rolled back at the end.
    """
    def override_get_db():
        yield db_session

    test_app = create_app()
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as c:
        yield c

import uuid
from app.services.rbac import assign_role

@pytest.fixture
def admin_token_headers(client_with_real_db, db_session):
    uid = uuid.uuid4()
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": f"admin_{uid}@example.com", "password": "securepassword"})
    user_id = resp.json()["id"]
    assign_role(db_session, uuid.UUID(user_id), "ADMIN")
    db_session.commit()
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"admin_{uid}@example.com", "password": "securepassword"})
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

@pytest.fixture
def operator_token_headers(client_with_real_db, db_session):
    uid = uuid.uuid4()
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": f"op_{uid}@example.com", "password": "securepassword"})
    user_id = resp.json()["id"]
    assign_role(db_session, uuid.UUID(user_id), "OPERATOR")
    db_session.commit()
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"op_{uid}@example.com", "password": "securepassword"})
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

@pytest.fixture
def viewer_token_headers(client_with_real_db, db_session):
    uid = uuid.uuid4()
    resp = client_with_real_db.post("/api/v1/auth/register", json={"email": f"view_{uid}@example.com", "password": "securepassword"})
    user_id = resp.json()["id"]
    assign_role(db_session, uuid.UUID(user_id), "VIEWER")
    db_session.commit()
    login_resp = client_with_real_db.post("/api/v1/auth/login", json={"email": f"view_{uid}@example.com", "password": "securepassword"})
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
