"""Layered runtime settings for the gateway."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EventBusSettings(BaseModel):
    """Event bus settings owned by the gateway runtime."""

    provider: str = "{{ cookiecutter.event_bus }}"


class ObservabilitySettings(BaseModel):
    """Observability settings owned by the gateway runtime."""

    provider: str = "{{ cookiecutter.observability }}"


class Settings(BaseSettings):
    """Gateway settings loaded from root and app-local env files."""

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=(".env", "apps/gateway/.env"),
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "{{ cookiecutter.project_name }}"
    domain: str = "{{ cookiecutter.domain }}"
    auth_strategy: str = "{{ cookiecutter.auth_strategy }}"
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    event_bus: EventBusSettings = Field(default_factory=EventBusSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)


def get_settings() -> Settings:
    return Settings()
