from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="", tags=["meta"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/version")
def version():
    return {
        "app": settings.APP_NAME,
        "version": getattr(settings, "APP_VERSION", "1.0.0")
    }
