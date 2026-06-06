from fastapi import APIRouter, Depends
from src.core.config import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "ok"
    }