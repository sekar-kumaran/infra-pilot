from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from asgi_correlation_id import correlation_id
import logging

logger = logging.getLogger(__name__)

def build_error_response(code: str, message: str, status_code: int = 500) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": correlation_id.get()
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error", extra={"details": exc.errors()})
    return build_error_response(
        code="VALIDATION_ERROR",
        message="Request payload is invalid",
        status_code=422
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return build_error_response(
        code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return build_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred"
    )
