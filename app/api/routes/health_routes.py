from datetime import datetime, UTC
from fastapi import APIRouter, Depends

from app.settings import Settings
from app.api.dependencies import get_settings_instance

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", summary="Healthcheck endpoint")
async def healthcheck(
    settings_instance: Settings = Depends(get_settings_instance)
):
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "app_name": settings_instance.APP_NAME,
        "app_version": settings_instance.APP_VERSION
    }
