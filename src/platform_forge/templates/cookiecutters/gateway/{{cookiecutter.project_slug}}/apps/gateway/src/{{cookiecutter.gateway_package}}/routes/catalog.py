"""Provider and internal service catalog route group."""

from fastapi import APIRouter

from {{ cookiecutter.gateway_package }}.models import ProviderInfo, ServiceInfo
from {{ cookiecutter.gateway_package }}.providers import PROVIDERS
from {{ cookiecutter.gateway_package }}.services import SERVICES

router = APIRouter(tags=["catalog"])


@router.get("/providers", response_model=list[ProviderInfo])
def list_providers() -> list[ProviderInfo]:
    return list(PROVIDERS)


@router.get("/services", response_model=list[ServiceInfo])
def list_services() -> list[ServiceInfo]:
    return list(SERVICES)
