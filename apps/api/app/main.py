import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import validation_exception_handler, http_exception_handler, unhandled_exception_handler
from app.api.v1.router import api_router
from app.api.v1.endpoints import health

# Initialize logging before application starts
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting InfraPilot API...")
    # Initialize future dependencies here (e.g., db connections)
    yield
    logger.info("Shutting down InfraPilot API...")
    # Clean up future dependencies here

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    
    if settings.CORS_ALLOWED_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Exception Handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers
    # Mount health at root level for load balancers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    # Mount v1 API
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()
