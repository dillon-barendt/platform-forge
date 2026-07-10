"""Health route group."""

from fastapi import APIRouter

from {{ cookiecutter.gateway_package }}.models import HealthResponse
from {{ cookiecutter.gateway_package }}.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_name=settings.app_name, domain=settings.domain)
