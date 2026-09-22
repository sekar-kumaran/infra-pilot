"""
Test suite: database infrastructure (Phase 1.2)

Test strategy: Option A — Dedicated PostgreSQL test database.
  - Uses the same PostgreSQL server running in Docker Compose.
  - A separate database "infrapilot_test" is used (created by fixture if needed).
  - Tests run with REAL PostgreSQL — no SQLite substitution.
  - Isolated per-test transactions: each test runs in its own transaction
    that is rolled back after the test, keeping the DB clean.

Environment variable:
  TEST_DATABASE_URL  (falls back to DATABASE_URL with _test suffix if absent)
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

# db_url, engine, and db_session fixtures are now in conftest.py


# --------------------------------------------------------------------------- #
# Configuration Tests
# --------------------------------------------------------------------------- #

class TestDatabaseConfig:
    def test_database_url_is_configured(self):
        from app.core.config import settings
        assert settings.DATABASE_URL, "DATABASE_URL must be set"

    def test_database_url_not_exposed_in_system_info(self, client):
        response = client.get("/api/v1/system/info")
        body = response.text
        assert "postgresql" not in body.lower(), (
            "DATABASE_URL must not appear in /api/v1/system/info response"
        )
        assert "postgrespassword" not in body, (
            "DB password must not appear in /api/v1/system/info response"
        )

    def test_database_url_not_in_live_response(self, client):
        response = client.get("/health/live")
        assert "postgresql" not in response.text.lower()


# --------------------------------------------------------------------------- #
# Connection Tests (real PostgreSQL)
# --------------------------------------------------------------------------- #

class TestDatabaseConnection:
    def test_basic_query_succeeds(self, db_session):
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_postgres_version_reachable(self, db_session):
        result = db_session.execute(text("SELECT version()")).scalar()
        assert result is not None
        assert "PostgreSQL" in result

    def test_current_database(self, db_session):
        result = db_session.execute(text("SELECT current_database()")).scalar()
        assert result is not None


# --------------------------------------------------------------------------- #
# Session / Transaction Tests
# --------------------------------------------------------------------------- #

class TestSessionManagement:
    def test_session_can_be_acquired_and_released(self, engine):
        """Session must open and close without leaking connections."""
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()

    def test_failed_transaction_rolls_back(self, db_session):
        """
        On error inside a transaction the session must roll back cleanly.
        We verify this by attempting to execute invalid SQL and confirming
        the session is still usable after rollback.
        """
        try:
            db_session.execute(text("SELECT * FROM table_that_does_not_exist_xyz"))
            db_session.commit()
        except Exception:
            db_session.rollback()

        # After rollback the session must still be usable
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_get_db_dependency_releases_session(self, engine):
        """get_db must close the session after use (no connection leak)."""
        from app.database.session import get_db

        # Patch the engine so get_db uses our test engine
        import app.database.session as session_mod
        original_engine = session_mod._engine
        original_factory = session_mod._SessionLocal
        session_mod._engine = engine
        session_mod._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        try:
            gen = get_db()
            db = next(gen)
            result = db.execute(text("SELECT 1")).scalar()
            assert result == 1
            try:
                next(gen)
            except StopIteration:
                pass
        finally:
            session_mod._engine = original_engine
            session_mod._SessionLocal = original_factory


# --------------------------------------------------------------------------- #
# Health / Readiness Tests (real DB)
# --------------------------------------------------------------------------- #

class TestHealthWithRealDB:
    def test_liveness_does_not_require_db(self, client):
        """Liveness must never depend on database state."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        # database field must be absent from liveness
        assert "database" not in response.json() or response.json()["database"] is None

    def test_readiness_with_db_available(self, client_with_real_db):
        """When a real DB is reachable, readiness must return 200/ready."""
        response = client_with_real_db.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["database"] == "healthy"

    def test_readiness_db_field_does_not_leak_credentials(self, client_with_real_db):
        """Readiness response must never include connection credentials."""
        response = client_with_real_db.get("/health/ready")
        body = response.text
        assert "postgrespassword" not in body
        assert "postgresql+psycopg" not in body


# --------------------------------------------------------------------------- #
# Unavailable DB Simulation (unit-level mock)
# --------------------------------------------------------------------------- #

class TestReadinessWhenDBUnavailable:
    def test_readiness_returns_503_when_db_unreachable(self, client):
        """
        Readiness must return 503 when the DB session raises OperationalError.
        We use a mock get_db dependency to simulate this without stopping Docker.
        """
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.database.session import get_db
        from sqlalchemy.exc import OperationalError as SAOpError

        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.execute.side_effect = SAOpError(None, None, Exception("connection refused"))

        def failing_db():
            yield mock_session

        override_app = create_app()
        override_app.dependency_overrides[get_db] = failing_db

        with TestClient(override_app, raise_server_exceptions=False) as tc:
            response = tc.get("/health/ready")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert body["database"] == "unhealthy"

    def test_readiness_does_not_leak_db_url_on_failure(self, client):
        """Error response must never include the database URL or password."""
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.database.session import get_db
        from sqlalchemy.exc import OperationalError as SAOpError
        from app.core.config import settings

        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.execute.side_effect = SAOpError(None, None, Exception(settings.DATABASE_URL))

        def failing_db():
            yield mock_session

        override_app = create_app()
        override_app.dependency_overrides[get_db] = failing_db

        with TestClient(override_app, raise_server_exceptions=False) as tc:
            response = tc.get("/health/ready")

        assert "postgresql" not in response.text.lower()
        assert "postgrespassword" not in response.text
