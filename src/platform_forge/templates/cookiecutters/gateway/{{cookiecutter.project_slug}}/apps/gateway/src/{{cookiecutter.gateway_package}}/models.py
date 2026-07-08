"""Shared response models for the gateway edge."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    domain: str


class ProviderInfo(BaseModel):
    name: str
    display_name: str


class ServiceInfo(BaseModel):
    name: str
    port: int | None = None
