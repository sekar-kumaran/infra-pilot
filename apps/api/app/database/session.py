"""
Database session management for InfraPilot.

Responsibilities:
  - Engine creation (lazy singleton — initialised on first access)
  - Session factory
  - Per-request session lifecycle via FastAPI dependency
  - Proper rollback and cleanup on exceptions

A global Engine is acceptable.
A global active Session is NOT acceptable — sessions are per-request only.

Driver: psycopg2 (via psycopg2-binary)
Dialect: postgresql+psycopg2
"""
import logging
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _get_engine() -> Engine:
    """
    Lazily initialise and return the singleton database engine.

    Raises RuntimeError if DATABASE_URL is not configured.
    This is intentional — a misconfigured database URL should surface
    immediately at startup rather than silently degrading.
    """
    global _engine, _SessionLocal

    if _engine is None:
        from app.core.config import settings  # avoid circular import at module level

        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured. "
                "Set it via environment variable or .env file."
            )

        _engine = create_engine(
            settings.DATABASE_URL,
            # pool_pre_ping: detect stale connections before handing them to the app.
            # Prevents "connection reset by peer" errors on long-lived idle connections.
            pool_pre_ping=True,
            # pool_size: concurrent connections to keep open.
            # 5 is a sensible default for development / small deployments.
            pool_size=5,
            # max_overflow: additional connections allowed beyond pool_size.
            max_overflow=10,
        )
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
        logger.info("Database engine initialised (pool_size=5, max_overflow=10)")

    return _engine


def get_session_factory() -> sessionmaker:
    """Return the session factory, initialising the engine if necessary."""
    _get_engine()  # ensures engine + factory are created
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a per-request database session.

    Session lifecycle guarantees:
      - A fresh session is opened at the start of each request.
      - SQLAlchemyError causes rollback before re-raising.
      - The session is always closed when the request ends (success or error).

    Credentials are never logged.
    """
    db: Session = get_session_factory()()
    try:
        yield db
    except SQLAlchemyError:
        # Log without the exception message to avoid leaking the DB URL,
        # which can appear inside SQLAlchemy OperationalError messages.
        logger.error("Database session error — rolling back transaction", exc_info=False)
        db.rollback()
        raise
    finally:
        db.close()
