from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "model": settings.MODEL_NAME
    }
