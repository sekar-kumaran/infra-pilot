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
from app.workers.celery_app import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    database: str | None = None
    broker: str | None = None


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
    Returns 200 with database='healthy' and broker='healthy' when reachable.
    Returns 503 when the database or broker is not reachable.
    """
    db_status = "healthy"
    broker_status = "healthy"
    is_ready = True
    
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness check: database unavailable: {str(e)}")
        db_status = "unhealthy"
        is_ready = False
        
    try:
        with celery_app.connection() as conn:
            conn.heartbeat_check()
    except Exception as e:
        logger.error(f"Readiness check: broker unavailable: {str(e)}")
        broker_status = "unhealthy"
        is_ready = False
        
    if not is_ready:
        response.status_code = 503
        return HealthResponse(status="not_ready", database=db_status, broker=broker_status)
        
    return HealthResponse(status="ready", database=db_status, broker=broker_status)

