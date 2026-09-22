"""
Integration tests that run inside the Docker container (container-to-postgres path).
These replace the host-based tests in test_database.py for environments where
the host cannot directly connect to the Docker-published postgres port.

Strategy: tests run via `docker exec` against the real infrapilot database.
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError as SAOpError

# Use the internal Docker network URL
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgrespassword@postgres:5432/infrapilot",
)


# Fixtures are now in conftest.py


class TestDatabaseConnection:
    def test_select_one(self, db_session):
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_postgres_version(self, db_session):
        version = db_session.execute(text("SELECT version()")).scalar()
        assert "PostgreSQL" in version

    def test_current_database(self, db_session):
        dbname = db_session.execute(text("SELECT current_database()")).scalar()
        assert dbname == "infrapilot"

    def test_alembic_version_table_exists(self, db_session):
        result = db_session.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchone()
        assert result is not None
        assert len(result[0]) > 0


class TestSessionLifecycle:
    def test_session_opens_and_closes(self, engine):
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()

    def test_transaction_rollback(self, db_session):
        try:
            db_session.execute(text("SELECT * FROM nonexistent_xyz_table"))
        except Exception:
            db_session.rollback()
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1


class TestDatabaseSecurity:
    def test_database_url_not_in_system_info(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/api/v1/system/info")
        assert "postgresql" not in resp.text.lower()
        assert "postgrespassword" not in resp.text

    def test_live_does_not_include_db_url(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health/live")
        assert "postgresql" not in resp.text.lower()
        assert "postgrespassword" not in resp.text


class TestReadinessEndpoint:
    def test_ready_with_db_up(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.database.session import get_db

        def real_db():
            eng = create_engine(DB_URL, pool_pre_ping=True)
            Session = sessionmaker(bind=eng)
            db = Session()
            try:
                yield db
            finally:
                db.close()
                eng.dispose()

        test_app = create_app()
        test_app.dependency_overrides[get_db] = real_db
        with TestClient(test_app) as client:
            resp = client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
        assert resp.json()["database"] == "healthy"

    def test_ready_fails_when_db_unreachable(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.database.session import get_db
        from sqlalchemy.exc import OperationalError
        from unittest.mock import MagicMock, patch

        # Provide a session that raises OperationalError on execute()
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            "connection refused", None, Exception("connection refused")
        )

        def failing_db():
            yield mock_session

        test_app = create_app()
        test_app.dependency_overrides[get_db] = failing_db
        with TestClient(test_app) as client:
            resp = client.get("/health/ready")
        assert resp.status_code == 503
        assert resp.json()["status"] == "not_ready"
        assert resp.json()["database"] == "unhealthy"

    def test_ready_db_failure_does_not_leak_url(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.database.session import get_db
        from sqlalchemy.exc import OperationalError
        from unittest.mock import MagicMock

        # Simulate OperationalError that contains URL in message
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            DB_URL, None, Exception(DB_URL)
        )

        def failing_db():
            yield mock_session

        test_app = create_app()
        test_app.dependency_overrides[get_db] = failing_db
        with TestClient(test_app) as client:
            resp = client.get("/health/ready")
        # Response body must not contain any credential information
        assert "postgresql" not in resp.text.lower()
        assert "postgrespassword" not in resp.text
        assert DB_URL not in resp.text
