from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

class SystemInfo(BaseModel):
    application_name: str
    version: str
    environment: str

@router.get("/info", response_model=SystemInfo)
async def system_info():
    return {
        "application_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }
