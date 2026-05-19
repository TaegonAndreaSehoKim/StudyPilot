from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", app=get_settings().app_name)


@router.post("/auth/check", response_model=HealthOut)
def auth_check() -> HealthOut:
    return HealthOut(status="ok", app=get_settings().app_name)
