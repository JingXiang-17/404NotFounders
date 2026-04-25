from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.providers.llm_provider import GLMProvider

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "model": settings.MODEL_NAME
    }


@router.get("/health/langfuse")
def langfuse_health_check():
    status = GLMProvider.langfuse_status()
    if not status["enabled"]:
        missing = [
            key
            for key, present in [
                ("LANGFUSE_PUBLIC_KEY", status.get("public_key_present")),
                ("LANGFUSE_SECRET_KEY", status.get("secret_key_present")),
                ("LANGFUSE_HOST", bool(status.get("host"))),
                ("langfuse SDK", status.get("sdk_available")),
            ]
            if not present
        ]
        raise HTTPException(
            status_code=503,
            detail={
                "status": "langfuse_unavailable",
                "message": "Langfuse tracing is NOT enabled. The following are missing or not installed: "
                           + ", ".join(missing),
                **status,
            },
        )
    return status
