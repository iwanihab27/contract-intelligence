from fastapi import APIRouter, Depends
from app.core.config import Settings, get_settings
import google.generativeai as genai
from qdrant_client import QdrantClient

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "ok"
    }

@router.get("/models")
def list_models(settings: Settings = Depends(get_settings)):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    models = [m.name for m in genai.list_models()]
    return {"models": models}

@router.delete("/reset-qdrant")
def reset_qdrant(settings: Settings = Depends(get_settings)):
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    client.delete_collection(settings.QDRANT_COLLECTION_NAME)
    return {"signal": "Qdrant collection deleted"}