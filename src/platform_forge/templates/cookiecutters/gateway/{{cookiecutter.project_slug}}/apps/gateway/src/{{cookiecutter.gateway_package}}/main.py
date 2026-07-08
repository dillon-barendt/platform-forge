"""FastAPI application factory."""

from fastapi import FastAPI

from {{ cookiecutter.gateway_package }}.routes import catalog, health
from {{ cookiecutter.gateway_package }}.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(catalog.router)
    return app


app = create_app()
