"""
Health check endpoints.

GET /health/live
    Liveness probe — answers: "Is the process alive?"
    Does NOT require a database connection.
    Used by container orchestrators to decide whether to restart the process.

GET /health/ready
    Readiness probe — answers: "Can this instance serve traffic?"
    Performs a real PostgreSQL connectivity check (SELECT 1).
    Returns HTTP 503 with database="unhealthy" when the database is unavailable.
    Database credentials are NEVER included in any response field or log message.
"""
import logging

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    database: str | None = None


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def check_live() -> HealthResponse:
    """
    Returns 200 OK as long as the process is running.
    Does not check external dependencies.
    """
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def check_ready(
    response: Response,
    db: Session = Depends(get_db),
) -> HealthResponse:
    """
    Returns 200 with database='healthy' when PostgreSQL is reachable.
    Returns 503 with database='unhealthy' when the database is not reachable.

    No database credentials are ever included in the response or logs.
    """
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="ready", database="healthy")
    except OperationalError:
        logger.error("Readiness check: database unavailable (OperationalError)")
        response.status_code = 503
        return HealthResponse(status="not_ready", database="unhealthy")
    except SQLAlchemyError:
        logger.error("Readiness check: database error (SQLAlchemyError)")
        response.status_code = 503
        return HealthResponse(status="not_ready", database="unhealthy")
    except Exception:  # noqa: BLE001
        logger.error("Readiness check: unexpected error")
        response.status_code = 503
        return HealthResponse(status="not_ready", database="unhealthy")
