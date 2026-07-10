"""Settings for Platform Forge itself."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ForgeSettings(BaseSettings):
    """Environment-driven settings for Platform Forge defaults and integrations."""

    model_config = SettingsConfigDict(env_prefix="PLATFORM_FORGE_", extra="ignore")

    ai_model: str | None = Field(default=None, description="Pydantic AI model identifier.")
    default_project_name: str = "gateway-platform"
    default_domain: str = "platform"
    default_providers: list[str] = Field(default_factory=lambda: ["example-provider"])
    default_services: list[str] = Field(
        default_factory=lambda: ["pricing", "inventory", "fulfillment"]
    )
    frontend_choices: set[str] = Field(default_factory=lambda: {"none", "vite", "nextjs"})
    event_bus_choices: set[str] = Field(default_factory=lambda: {"none", "redis", "nats", "kafka"})
    observability_choices: set[str] = Field(
        default_factory=lambda: {"none", "logfire", "opentelemetry"}
    )
